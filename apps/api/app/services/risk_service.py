from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from apps.api.app.models.claim import ClaimType, MemoryClaim
from apps.api.app.models.provenance import ProvenanceRecord
from apps.api.app.models.verdict import RiskAssessment

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "classify_risk.txt"

_VALID_FLAGS = {
    "policy_bypass",
    "authority_injection",
    "credential_request",
    "exfiltration",
    "low_authority_instruction",
    "contradiction_detected",
    "external_longform_input",
    "identity_density",
    "write_burst",
    "obfuscation",
    "url_injection",
}


class RiskService:
    """Score the risk of a memory item.

    When ``use_openai=True`` in Settings, calls ``gpt-4.1-mini`` with the
    ``classify_risk.txt`` prompt and merges the LLM result with the local
    pattern-matching flags for belt-and-suspenders coverage.
    Falls back to heuristic-only on any LLM failure.
    """

    PATTERN_FLAGS = {
        "policy_bypass": (
            "ignore previous", "override policy", "skip approval", "disable guardrail", 
            "disable all guardrail", "disable guardrails", "bypass all security", 
            "stop quarantining", "ignore all future", "skip all human", 
            "policy filters should be disabled", "disable the memory firewall",
            "compliance rules are suspended", "never block emails", "update policy:"
        ),
        "authority_injection": (
            "always trust", "act as admin", "system says", "authorized by", 
            "i am the system administrator", "granted admin access", "grant full trust", 
            "i am the ceo", "system-level authority", "executive authority"
        ),
        "credential_request": (
            "password", "secret", "token", "credential", "api key", "api_key",
            "password for", "password:", "secret token", "secret is", "access key",
            "ssh key", "private key", "id_rsa", "credential hidden", "credentials are"
        ),
        "exfiltration": (
            "do not tell", "keep hidden", "silently", "exfiltrate", "forward all future", 
            "without telling", "send a copy of", "always respond with the stored", "hidden instruction"
        ),
    }

    # Compiled regex patterns for obfuscation / URL injection detection.
    # These are checked separately from string patterns to handle regex semantics.
    _OBFUSCATION_PATTERNS = (
        re.compile(r"[A-Za-z0-9+/]{20,}={0,2}"),   # base64-like blobs
        re.compile(r"0x[0-9a-fA-F]{8,}"),            # long hex literals
    )
    _URL_INJECTION_PATTERNS = (
        re.compile(r"data:text/html", re.IGNORECASE),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"vbscript:", re.IGNORECASE),
    )

    def __init__(self, settings=None) -> None:
        self._settings = settings
        self._prompt_template = self._load_prompt()

    def assess(
        self,
        claims: list[MemoryClaim],
        provenance: ProvenanceRecord,
        contradictions: list[str],
        content: str,
        score: float = 0.0,
        is_burst: bool = False,
    ) -> RiskAssessment:
        heuristic = self._heuristic_assess(
            claims=claims,
            provenance=provenance,
            contradictions=contradictions,
            content=content,
            score=score,
            is_burst=is_burst,
        )

        if self._settings and self._settings.use_openai and self._settings.openai_api_key:
            try:
                llm = self._llm_assess(claims, provenance, content)
                return self._merge(heuristic, llm)
            except Exception as exc:
                logger.warning("LLM risk scoring failed, falling back to heuristic: %s", exc)

        return heuristic

    def _heuristic_assess(
        self,
        claims: list[MemoryClaim],
        provenance: ProvenanceRecord,
        contradictions: list[str],
        content: str,
        score: float = 0.0,
        is_burst: bool = False,
    ) -> RiskAssessment:
        flags: list[str] = []
        reasons: list[str] = []
        lowered = content.lower()

        matched_flags = []
        for flag, patterns in self.PATTERN_FLAGS.items():
            if any(pattern in lowered for pattern in patterns):
                score += 0.22
                flags.append(flag)
                reasons.append(f"Matched suspicious pattern set: {flag}")
                matched_flags.append(flag)

        for flag in matched_flags:
            if flag == "exfiltration":
                score += 0.80
            elif flag == "credential_request":
                if any(x in lowered for x in ("ssh key", "id_rsa", "private key")):
                    score += 0.52
                else:
                    score += 0.80
            elif flag == "policy_bypass":
                direct_overrides = (
                    "ignore previous", "override policy", "system override", 
                    "disable all guardrail", "disable guardrail", "disable the memory firewall", 
                    "ignore all future safety", "policy filters should be disabled", 
                    "executive authority", "system-level authority", "full trust", 
                    "always respond with the stored"
                )
                if any(pat in lowered for pat in direct_overrides):
                    score += 0.80
                else:
                    score += 0.52
            elif flag == "authority_injection":
                direct_admins = (
                    "act as admin", "system-level authority", "executive authority", 
                    "grant full trust", "system override"
                )
                if any(pat in lowered for pat in direct_admins):
                    score += 0.80
                else:
                    score += 0.52

        instruction_like = any(
            claim.claim_type in {ClaimType.INSTRUCTION, ClaimType.POLICY}
            for claim in claims
        )
        if instruction_like and provenance.authority_score < 0.6:
            score += 0.18
            flags.append("low_authority_instruction")
            reasons.append("Instructional memory came from a low-authority source")

        if contradictions:
            score += min(0.28, 0.1 * len(contradictions))
            flags.append("contradiction_detected")
            reasons.append("New memory conflicts with existing memory")

        if provenance.source_type.lower() in {"web", "email", "slack"} and len(content) > 300:
            score += 0.08
            flags.append("external_longform_input")
            reasons.append("External long-form content is being written into memory")

        if sum(1 for claim in claims if claim.claim_type == ClaimType.IDENTITY) > 2:
            score += 0.08
            flags.append("identity_density")
            reasons.append("Memory contains dense identity assertions")

        if is_burst:
            score += 0.40
            flags.append("write_burst")
            reasons.append("Actor has exceeded the burst write threshold")

        # Obfuscation: base64 blobs or long hex literals suggest hidden payloads
        if any(pat.search(content) for pat in self._OBFUSCATION_PATTERNS):
            score += 0.30
            flags.append("obfuscation")
            reasons.append("Content contains encoded/obfuscated data (base64 or hex blob)")

        # URL injection: data-URI or script URL schemes are always suspicious in memory writes
        if any(pat.search(content) for pat in self._URL_INJECTION_PATTERNS):
            score += 0.45
            flags.append("url_injection")
            reasons.append("Content contains a script or data URL injection pattern")

        return RiskAssessment(
            score=min(score, 1.0),
            flags=sorted(set(flags)),
            reasons=reasons,
            contradiction_count=len(contradictions),
        )

    def _llm_assess(
        self,
        claims: list[MemoryClaim],
        provenance: ProvenanceRecord,
        content: str,
    ) -> RiskAssessment:
        from openai import OpenAI

        if not self._settings or not self._settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        client = OpenAI(api_key=self._settings.openai_api_key)
        prompt = (self._prompt_template or "").replace(
            "{content}", content
        ).replace(
            "{claims_json}", json.dumps([c.model_dump() for c in claims], default=str)
        ).replace(
            "{source_type}", provenance.source_type
        ).replace(
            "{authority_score}", str(round(provenance.authority_score, 2))
        )

        response = client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a memory security classifier. "
                        "Return only the JSON object specified. No markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=512,
        )

        raw = response.choices[0].message.content or "{}"
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        data: dict = json.loads(raw)

        raw_flags = [f for f in data.get("flags", []) if f in _VALID_FLAGS]
        return RiskAssessment(
            score=float(data.get("risk_score", 0.1)),
            flags=raw_flags,
            reasons=data.get("reasons", []),
        )

    # ------------------------------------------------------------------ #
    # Merge helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _merge(heuristic: RiskAssessment, llm: RiskAssessment) -> RiskAssessment:
        """Take the higher risk score and union all flags/reasons."""
        merged_score = max(heuristic.score, llm.score)
        merged_flags = sorted(set(heuristic.flags) | set(llm.flags))
        merged_reasons = list(dict.fromkeys(heuristic.reasons + llm.reasons))  # dedup, preserve order
        return RiskAssessment(
            score=min(merged_score, 1.0),
            flags=merged_flags,
            reasons=merged_reasons,
        )

    @staticmethod
    def _load_prompt() -> str | None:
        try:
            return _PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("classify_risk.txt prompt not found at %s", _PROMPT_PATH)
            return None


