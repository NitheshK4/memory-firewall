from pydantic import BaseModel, Field

from apps.api.app.models.api import RetrievalResult, StoredMemory


class RetrievalContext(BaseModel):
    """Snapshot of everything the read-firewall sees when evaluating a query."""

    query: str
    actor: str
    candidate_memories: list[StoredMemory] = Field(default_factory=list)
    filtered_results: list[RetrievalResult] = Field(default_factory=list)
    suppressed_ids: list[str] = Field(default_factory=list)
    suppression_reasons: dict[str, list[str]] = Field(default_factory=dict)
    guard_flags: list[str] = Field(default_factory=list)
