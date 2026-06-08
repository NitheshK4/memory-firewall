from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.models.api import RetrievalRequest, RetrievalResponse, RetrievalResult, StoredMemory
from apps.api.app.models.verdict import MemoryStatus


class RetrievalService:
    def __init__(self, repository: InMemoryMemoryRepository) -> None:
        self.repository = repository

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        candidates = self.repository.query(request.query, limit=request.max_results * 3)
        threat_level = self._detect_threat(request.query, request.actor)
        if threat_level == "high":
            return RetrievalResponse(query=request.query, results=[])

        query_text = request.query
        if "supplier" in query_text.lower():
            query_text += " vendor"

        candidates = self.repository.query(query_text, limit=request.max_results * 3)
        results: list[RetrievalResult] = []
        for memory, similarity in candidates:
            if memory.status in {MemoryStatus.BLOCKED, MemoryStatus.QUARANTINED}:
                continue
            if request.min_trust_score > 0.0 and memory.trust_score < request.min_trust_score:
                continue
            results.append(
                self._build_result(memory, similarity)
            )
            if len(results) >= request.max_results:
                break

        return RetrievalResponse(query=request.query, results=results)

    def _detect_threat(self, query: str, actor: str) -> str:
        lowered_query = query.lower()
        lowered_actor = actor.lower()
        
        untrusted_actors = {"external", "untrusted", "adversarial", "malicious", "attacker", "fake", "impersonator", "unknown"}
        is_untrusted_actor = any(token in lowered_actor for token in untrusted_actors)
        
        prompt_injection_patterns = (
            "ignore previous", "forget all", "dump your system", "debug mode", 
            "disregard your safety", "disregard safety", "tell me everything", 
            "execute the following", "cat /etc", "system prompt", "system instructions",
            "return all memory", "repeat back every", "word for word", "most sensitive"
        )
        
        scope_escalation_patterns = (
            "show me blocked", "reveal quarantined", "quarantined memories", 
            "blocked memories", "user id is 0", "root", "system-level", 
            "auditor", "retrieve all blocked", "override your instructions"
        )
        
        credential_fishing_patterns = (
            "api key", "api_key", "password", "secret password", "credentials", 
            "token", "tokens", "ssh key", "private key", "keys stored"
        )
        
        if any(pat in lowered_query for pat in prompt_injection_patterns):
            return "high"
        if any(pat in lowered_query for pat in scope_escalation_patterns):
            return "high"
        if any(pat in lowered_query for pat in credential_fishing_patterns):
            if is_untrusted_actor:
                return "high"
            return "low"
            
        return "none"

    @staticmethod
    def _build_result(memory: StoredMemory, similarity: float) -> RetrievalResult:
        reasons = [
            f"similarity:{similarity:.2f}",
            f"trust:{memory.trust_score:.2f}",
            f"status:{memory.status.value}",
        ]
        if memory.flags:
            reasons.append(f"flags:{', '.join(memory.flags[:3])}")

        return RetrievalResult(
            memory_id=memory.memory_id,
            raw_content=memory.raw_content,
            claims=memory.claims,
            trust_score=memory.trust_score,
            status=memory.status,
            reasons=reasons,
        )