from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from apps.api.app.config import Settings
from apps.api.app.models.claim import ClaimType, MemoryClaim
from packages.shared.utils.sanitise import sanitise_content

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extract_claims.txt"


class ClaimExtractor:
    """Extract atomic claims from raw memory text.

    When ``settings.use_openai=True`` and an API key is configured, uses
    ``gpt-4.1-mini`` with the ``extract_claims.txt`` prompt for high-quality
    structured extraction.  Falls back to a fast heuristic extractor on any
    failure or when OpenAI is disabled.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._prompt_template: str | None = self._load_prompt()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def extract(self, content: str) -> list[MemoryClaim]:
        # Sanitise before any processing so neither the LLM path nor the
        # heuristic path ever sees raw control characters or oversized input.
        content = sanitise_content(content)
        if self.settings.use_openai and self.settings.openai_api_key:
            try:
                return self._extract_llm(content)
            except Exception as exc:
                logger.warning("LLM claim extraction failed, falling back to heuristic: %s", exc)
        return self._extract_heuristic(content)

    # ------------------------------------------------------------------ #
    # LLM path
    # ------------------------------------------------------------------ #

    def _extract_llm(self, content: str) -> list[MemoryClaim]:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        prompt = (self._prompt_template or "").replace("{content}", content)

        response = client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a security-focused knowledge extractor. "
                        "Return only valid JSON arrays as instructed."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=1024,
        )

        raw = response.choices[0].message.content or "[]"
        # Strip any accidental markdown fences
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        items: list[dict] = json.loads(raw)

        claims: list[MemoryClaim] = []
        for item in items[:10]:
            try:
                claim_type = ClaimType(item.get("claim_type", "fact"))
            except ValueError:
                claim_type = ClaimType.FACT
            claims.append(
                MemoryClaim(
                    claim_type=claim_type,
                    text=str(item.get("text", ""))[:500],
                    subject=str(item.get("subject", "unknown"))[:80],
                    confidence=float(item.get("confidence", 0.65)),
                )
            )
        return claims or self._extract_heuristic(content)

    # ------------------------------------------------------------------ #
    # Heuristic fallback
    # ------------------------------------------------------------------ #

    def _extract_heuristic(self, content: str) -> list[MemoryClaim]:
        sentences = [
            chunk.strip()
            for chunk in re.split(r"[.!?\n]+", content)
            if chunk.strip()
        ]
        if not sentences:
            sentences = [content.strip()]

        claims: list[MemoryClaim] = []
        for sentence in sentences[:8]:
            claim_type = self._infer_claim_type(sentence)
            claims.append(
                MemoryClaim(
                    claim_type=claim_type,
                    text=sentence,
                    subject=self._extract_subject(sentence),
                    confidence=self._estimate_confidence(sentence, claim_type),
                )
            )
        return claims

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_prompt() -> str | None:
        try:
            return _PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("extract_claims.txt prompt not found at %s", _PROMPT_PATH)
            return None

    @staticmethod
    def _infer_claim_type(text: str) -> ClaimType:
        lowered = text.lower()
        if any(token in lowered for token in ("always", "must", "required", "policy", "compliance")):
            return ClaimType.POLICY
        if any(token in lowered for token in ("please", "should", "do ", "skip", "approve", "trust")):
            return ClaimType.INSTRUCTION
        if any(token in lowered for token in ("prefer", "likes", "favorite")):
            return ClaimType.PREFERENCE
        if any(token in lowered for token in ("i am", "my name is", "role is", "works as")):
            return ClaimType.IDENTITY
        return ClaimType.FACT

    @staticmethod
    def _extract_subject(text: str) -> str:
        lowered = text.lower()
        for separator in (" is ", " should ", " must ", " are ", " was ", " were "):
            if separator in lowered:
                index = lowered.index(separator)
                return text[:index].strip()[:80] or text[:80].strip()
        return " ".join(text.split()[:4]).strip()[:80]

    @staticmethod
    def _estimate_confidence(text: str, claim_type: ClaimType) -> float:
        score = 0.55
        if any(char.isdigit() for char in text):
            score += 0.1
        if len(text.split()) > 6:
            score += 0.1
        if claim_type in {ClaimType.POLICY, ClaimType.INSTRUCTION}:
            score += 0.05
        return min(score, 0.9)

