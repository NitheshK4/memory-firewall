# Contributing to Memory Firewall

Thank you for your interest in improving Memory Firewall! This document explains
how to set up the project locally, run tests, and follow our conventions when
submitting changes.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Running the Stack](#running-the-stack)
4. [Testing](#testing)
5. [Code Style](#code-style)
6. [Commit Conventions](#commit-conventions)
7. [Pull Request Process](#pull-request-process)

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Python | 3.11 |
| pip | 23.x |
| Docker + Compose | 24.x (optional, for full stack) |
| Git | 2.40 |

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/NitheshK4/memory-firewall.git
cd memory-firewall

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install the project in editable mode (all dependencies included)
pip install -e .

# 4. Copy the example env file and fill in any optional values
cp .env.example .env
```

### Optional: Enable OpenAI-powered scoring

Set the following in your `.env` to enable LLM-based claim extraction and risk
scoring instead of the deterministic heuristic fallbacks:

```env
USE_OPENAI=true
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
```

---

## Running the Stack

### API only (heuristic mode, no external services required)

```bash
make run-api
# API is available at http://localhost:8000
# Interactive docs: http://localhost:8000/docs
```

### Dashboard (Streamlit)

```bash
make run-dashboard
# Dashboard is available at http://localhost:8501
```

### Full Docker stack (Postgres + Neo4j + OTEL + API + Dashboard)

```bash
make run
```

---

## Testing

All tests are in `apps/api/tests/`. Run the full suite with:

```bash
pytest
# or via Make
make test
```

Run a specific test file:

```bash
pytest apps/api/tests/test_risk_service.py -v
```

Run with coverage:

```bash
pip install pytest-cov
pytest --cov=apps --cov-report=term-missing
```

### Writing tests

- Place new test files under `apps/api/tests/`.
- Prefer unit tests that import service classes directly; avoid spinning up
  the full FastAPI app unless you are testing HTTP behaviour.
- Use `InMemoryMemoryRepository` for repository-level tests — it has zero
  external dependencies.

---

## Code Style

- **Formatter**: [Ruff](https://docs.astral.sh/ruff/) (format + lint).
  ```bash
  pip install ruff
  ruff format .
  ruff check .
  ```
- **Type hints**: All public functions must carry full type annotations.
- **Docstrings**: Google style for classes; single-line docstrings are fine for
  simple helpers.
- **Imports**: Standard library → third-party → first-party, separated by blank
  lines.

---

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```

**Common types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`

**Examples**

```
feat(risk): add entropy-based flag for high-randomness content
fix(repo): prevent duplicate vector indexing on status update
docs: add CONTRIBUTING guide
test(policy): cover LOW_TRUST threshold boundary cases
```

---

## Pull Request Process

1. Fork the repo and create a feature branch:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes, add tests, and ensure the test suite passes.
3. Push and open a PR against `main`.
4. Fill in the PR template — describe *why* the change is needed, not just what
   it does.
5. A maintainer will review within 48 hours. Address comments, squash fixup
   commits, and request a re-review when ready.

---

## Project Layout Quick Reference

```
apps/api/app/
  services/     # Core firewall logic (risk, policy, claims, provenance…)
  graphs/       # LangGraph state-machine pipelines (write + read firewall)
  routers/      # FastAPI route handlers
  models/       # Pydantic schemas (API, claim, verdict, provenance)
  db/           # Repository and vector store implementations
  prompts/      # LLM prompt templates
packages/
  shared/       # Cross-app schemas and utilities
  connectors/   # Source connectors (email, Slack, docs, tool-trace)
infra/          # Docker Compose, Kubernetes, Postgres/Neo4j init scripts
evals/          # Evaluation datasets and scoring runners
```
