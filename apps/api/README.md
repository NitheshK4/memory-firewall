# Memory Firewall – API Service

This directory contains the **FastAPI** backend that powers the Memory Firewall REST API.

## Structure

```
apps/api/
├── app/
│   ├── main.py            # FastAPI application factory
│   ├── deps.py            # Dependency injection (ServiceContainer)
│   ├── models/            # Pydantic request/response models
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic (Firewall, Audit, DB)
│   └── telemetry/         # Prometheus metrics
├── tests/                 # Integration & unit tests for the API
├── Dockerfile
└── pyproject.toml
```

## Running locally

```bash
# From the repo root
uvicorn apps.api.app.main:app --reload --port 8000
```

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./dev.db` |
| `LOG_LEVEL` | Python log level | `INFO` |
| `METRICS_ENABLED` | Enable Prometheus `/metrics` endpoint | `true` |

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/memory/write` | Submit memory for firewall evaluation |
| `POST` | `/v1/memory/retrieve` | Retrieve and score memories |
| `GET` | `/v1/audit/logs` | Paginated audit log |
| `GET` | `/health` | Liveness probe |
| `GET` | `/metrics` | Prometheus metrics (if enabled) |

## Running tests

```bash
pytest apps/api/tests/ -v
```
