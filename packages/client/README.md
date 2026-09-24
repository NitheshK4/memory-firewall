# memory-firewall-client

Official Python SDK for the [Memory Firewall](https://github.com/NitheshK4/memory-firewall) API.

## Installation

```bash
pip install memory-firewall-client
# or with uv
uv add memory-firewall-client
```

## Quick start

```python
from memory_firewall_client import MemoryFirewallClient

client = MemoryFirewallClient(base_url="http://localhost:8000")

# Write a memory
verdict = client.write_memory(
    content="The capital of France is Paris.",
    agent_id="agent-001",
    session_id="session-abc",
)
print(verdict.action)   # "allow"

# Retrieve memories
results = client.retrieve_memory(query="What is the capital of France?")
for r in results:
    print(r.content, r.trust_score)
```

## Configuration

| Parameter | Description | Default |
|---|---|---|
| `base_url` | Memory Firewall API base URL | `http://localhost:8000` |
| `api_key` | Bearer token (if auth enabled) | `None` |
| `timeout` | Request timeout in seconds | `30` |
| `retries` | Number of retry attempts | `3` |

## API Reference

### `MemoryFirewallClient`

#### `write_memory(content, agent_id, session_id, metadata=None) → MemoryVerdict`

Submit a memory write for firewall evaluation.

#### `retrieve_memory(query, agent_id=None, top_k=10) → list[MemoryResult]`

Retrieve memories relevant to a query, scored by the firewall.

#### `get_audit_log(page=1, page_size=50) → AuditLog`

Paginated access to the audit log.

## License

MIT
