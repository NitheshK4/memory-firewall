from apps.api.app.models.api import StoredMemory
from apps.api.app.models.claim import MemoryClaim


class ContradictionService:
    def analyze(self, claims: list[MemoryClaim], candidates: list[StoredMemory]) -> list[str]:
        contradictions: set[str] = set()
        for claim in claims:
            for candidate in candidates:
                for previous in candidate.claims:
                    if claim.subject.lower() != previous.subject.lower():
                        continue
                    if claim.text.lower() == previous.text.lower():
                        continue
                    if self._is_opposed(claim.text, previous.text):
                        contradictions.add(
                            f"'{claim.subject}' conflicts with memory {candidate.memory_id}"
                        )
                    elif self._lexical_overlap(claim.text, previous.text) > 0.65:
                        contradictions.add(
                            f"'{claim.subject}' has competing variants in memory {candidate.memory_id}"
                        )
        return sorted(contradictions)

    @staticmethod
    def _is_opposed(left: str, right: str) -> bool:
        left_negated = any(token in left.lower().split() for token in ("no", "not", "never", "cannot", "can't"))
        right_negated = any(token in right.lower().split() for token in ("no", "not", "never", "cannot", "can't"))
        return left_negated != right_negated

    @staticmethod
    def _lexical_overlap(left: str, right: str) -> float:
        left_tokens = {token for token in left.lower().split() if token}
        right_tokens = {token for token in right.lower().split() if token}
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = len(left_tokens & right_tokens)
        return overlap / max(len(left_tokens), len(right_tokens))

