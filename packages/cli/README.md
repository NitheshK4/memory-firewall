# mfw – Memory Firewall CLI

Command-line interface for interacting with a running Memory Firewall API.

## Installation

```bash
pip install memory-firewall-client   # includes the mfw CLI
```

## Usage

```
mfw [OPTIONS] COMMAND [ARGS]...
```

### Global options

| Option | Description |
|---|---|
| `--url TEXT` | API base URL (default: `http://localhost:8000`) |
| `--api-key TEXT` | Bearer token for authenticated APIs |
| `--output [json\|table\|plain]` | Output format (default: `table`) |
| `--help` | Show help and exit |

---

### Commands

#### `mfw write`

Submit a memory for firewall evaluation.

```bash
mfw write --content "User prefers dark mode" --agent-id agent-001
```

#### `mfw retrieve`

Retrieve memories matching a query.

```bash
mfw retrieve --query "user preferences" --top-k 5
```

#### `mfw audit`

View recent audit log entries.

```bash
mfw audit --page 1 --page-size 20
```

#### `mfw health`

Check API health.

```bash
mfw health
# → {"status": "ok", "version": "0.2.0"}
```

---

## Examples

```bash
# Write a memory and see the verdict
mfw --url http://prod-api:8000 write \
    --content "Customer email: user@example.com" \
    --agent-id crm-agent \
    --output json

# Retrieve with JSON output, pipe to jq
mfw retrieve --query "customer email" | jq '.[] | .trust_score'
```

## License

MIT
