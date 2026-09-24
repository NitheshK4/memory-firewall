"""Memory Firewall Python SDK client."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


class MemoryFirewallClientError(Exception):
    """Raised when Memory Firewall API returns an error status."""

    def __init__(self, status_code: int, message: str, payload: Any = None) -> None:
        super().__init__(f"[{status_code}] {message}")
        self.status_code = status_code
        self.message = message
        self.payload = payload


class MemoryFirewallClient:
    """Synchronous Python client for Memory Firewall FastAPI backend."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            query_items = []
            for k, v in params.items():
                if v is None:
                    continue
                if isinstance(v, (list, tuple)):
                    for item in v:
                        query_items.append((k, str(item)))
                else:
                    query_items.append((k, str(v)))
            if query_items:
                url = f"{url}?{urllib.parse.urlencode(query_items)}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "MemoryFirewall-Python-SDK/0.2.0",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        body: Optional[bytes] = None
        if json_data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(json_data).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8")
            try:
                parsed_err = json.loads(err_body)
                detail = parsed_err.get("detail", err_body)
            except Exception:
                detail = err_body
            raise MemoryFirewallClientError(exc.code, str(detail), parsed_err if "parsed_err" in locals() else None) from exc
        except urllib.error.URLError as exc:
            raise MemoryFirewallClientError(0, f"Connection failed: {exc.reason}") from exc

    def health(self, detailed: bool = False) -> Dict[str, Any]:
        """Check API service health status."""
        endpoint = "/api/v1/health/detailed" if detailed else "/api/v1/health"
        return self._request("GET", endpoint)

    def write_memory(
        self,
        content: str,
        source_type: str = "agent",
        source_id: str = "direct",
        actor: str = "default_user",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Submit a memory write request through the write firewall pipeline."""
        payload: Dict[str, Any] = {
            "content": content,
            "source_type": source_type,
            "source_id": source_id,
            "actor": actor,
        }
        if tags is not None:
            payload["tags"] = tags
        if metadata is not None:
            payload["metadata"] = metadata
        return self._request("POST", "/api/v1/memories", json_data=payload)

    def retrieve_memories(
        self,
        query: str,
        actor: str = "default_user",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Query memories through the read firewall with prompt-injection defense."""
        payload = {
            "query": query,
            "actor": actor,
            "limit": limit,
        }
        return self._request("POST", "/api/v1/retrieval", json_data=payload)

    def list_memories(
        self,
        limit: int = 50,
        offset: int = 0,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List stored memories with optional tag filter and pagination."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if tags:
            params["tags"] = tags
        return self._request("GET", "/api/v1/memories", params=params)

    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """Fetch a single memory item by ID."""
        return self._request("GET", f"/api/v1/memories/{memory_id}")

    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Soft-delete/block a memory by ID."""
        return self._request("DELETE", f"/api/v1/memories/{memory_id}")

    def review_decision(
        self,
        memory_id: str,
        action: str,  # "approve", "reject", "edit"
        reviewed_by: str = "admin",
        reason: Optional[str] = None,
        edited_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a manual human review decision for quarantined memory."""
        payload = {
            "action": action,
            "reviewed_by": reviewed_by,
            "reason": reason or f"Manual review: {action}",
            "edited_content": edited_content,
        }
        return self._request("POST", f"/api/v1/review/{memory_id}/decision", json_data=payload)

    def get_audit_stats(self) -> Dict[str, Any]:
        """Fetch audit log event count breakdown."""
        return self._request("GET", "/api/v1/audit/stats")

    def get_actor_stats(self) -> List[Dict[str, Any]]:
        """Fetch write statistics aggregated by actor."""
        return self._request("GET", "/api/v1/audit/actors")

    def __enter__(self) -> "MemoryFirewallClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
