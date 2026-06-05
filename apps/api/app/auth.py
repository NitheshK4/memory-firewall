"""API key authentication dependency for Memory Firewall.

All sensitive endpoints (write, retrieval, review, policies) must depend on
``require_api_key``.  The health endpoint is intentionally left public.

Configuration
-------------
Set the ``API_KEY`` environment variable (or ``api_key`` in ``.env``).
If no key is configured the dependency is a no-op — all requests pass through.
This lets the project work out-of-the-box in local dev without extra config
while being production-ready when a key is provided.

Usage
-----
```python
from apps.api.app.auth import require_api_key

@router.post("/memories")
def write_memory(
    request: MemoryWriteRequest,
    _: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> MemoryWriteResponse: ...
```
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from apps.api.app.config import get_settings

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key_header: str | None = Security(_API_KEY_HEADER)) -> None:
    """FastAPI dependency that enforces X-API-Key authentication.

    - If no ``api_key`` is configured in Settings, this is a no-op (dev mode).
    - If configured, the header must match exactly (constant-time comparison).
    """
    settings = get_settings()
    configured_key = settings.api_key

    # No key configured → open access (dev/test mode)
    if not configured_key:
        return

    # Key configured but header missing
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key_header, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
