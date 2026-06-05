# Re-exports claim.py under the canonical name expected by the project spec.
# All internal code uses apps.api.app.models.claim; this module provides
# the memory_claim alias for external consumers and the schema package.
from apps.api.app.models.claim import ClaimType, MemoryClaim

__all__ = ["ClaimType", "MemoryClaim"]
