# Changelog

All notable changes to **Memory Firewall** are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- `CONTRIBUTING.md` — developer setup guide, coding conventions, and PR process.
- `CHANGELOG.md` — this file; tracks all notable changes going forward.
- `updated_at` field on `StoredMemory`; stamped on every status transition
  (approve, reject, edit, block) so consumers can detect stale caches.
- Pagination support on `GET /api/v1/memories`: `limit`, `offset` query
  parameters and a `MemoryListResponse` envelope returning `total`, `offset`,
  `limit`, and `items`.
- Burst-write detection in `AuditService` (`check_burst_write`, `burst_write_count`)
  with configurable rolling window and threshold (default: 10 writes / 60 s).
- 6 unit tests for burst-write detection (`test_audit_burst.py`).
- `QuarantineService.quarantine()` method; wires `AuditService` into
  quarantine and review decision paths so the full lifecycle is auditable.
- `AuditService.log_deletion()` — dedicated audit event for soft-delete
  (block) operations so API deletions are distinguishable from firewall
  verdict blocks in the log.
- `AuditService.clear_log()` — resets the in-memory log; intended for test
  teardown use to avoid state bleed between test cases.
- `AuditService.get_actor_stats()` — per-actor write summary (total writes,
  recent writes, last write timestamp, burst flag); exposed via new
  `GET /api/v1/audit/actors` endpoint.
- `packages/shared/utils/sanitise.py` — shared content-sanitisation helpers:
  `strip_control_chars`, `normalise_unicode`, `truncate`, `sanitise_content`.
  Applied automatically in `ClaimExtractor.extract()`.
- `medium` threat level in `RetrievalService._detect_threat()`: credential-fishing
  queries from trusted actors now receive filtered results (trust ≥
  `RETRIEVAL_MEDIUM_TRUST_FLOOR`) rather than unrestricted access.
- `burst_window_seconds`, `burst_max_writes`, and `retrieval_medium_trust_floor`
  settings fields; all three are configurable via environment variables and
  documented in `.env.example`.

### Changed
- `GET /api/v1/memories` response shape is now a `MemoryListResponse` object
  instead of a bare array (breaking change for existing API consumers).
- `QuarantineService.__init__` now accepts an optional `audit_service` argument.
- Review endpoint (`POST /api/v1/review/{id}/decision`) now records every
  approve/reject/edit action in the audit log.
- `DELETE /memories/{id}` now calls `log_deletion()` instead of `log_verdict()`
  to produce a correctly typed `memory_deleted` audit event.
- Credential-fishing retrieval queries from non-untrusted actors now return
  `"medium"` threat level instead of `"low"`, triggering the trust-floor filter.

---

## [0.1.0] — 2026-05-01

Initial MVP release.

### Added
- FastAPI service with write and read memory firewall pipelines.
- LangGraph-based `WriteFirewall` and `ReadFirewall` state machines.
- Heuristic claim extractor with optional OpenAI (`gpt-4.1-mini`) upgrade path.
- Provenance tagging with authority scoring (system > tool > user > web/email).
- Risk scoring engine: pattern-flag matching + contradiction detection + LLM merge.
- Policy engine with four verdict actions: ALLOW, LOW_TRUST, QUARANTINE, BLOCK.
- In-memory repository with keyword-overlap vector fallback.
- Streamlit dashboard for quarantine review.
- Audit service with per-event and per-memory-id log retrieval.
- Docker Compose stack: Postgres (pgvector), Neo4j, OpenTelemetry Collector.
- Kubernetes manifests with health probes and Neo4j bootstrap job.
- `GET /memories/{id}` and `DELETE /memories/{id}` (soft-block) endpoints.
- `min_trust_score` filter on retrieval requests.
- Audit log exposed via `GET /api/v1/audit`.
- GitHub Actions CI pipeline running pytest on every push.
- Evaluation datasets: memory poisoning, benign memory, retrieval attacks.
- 31 unit tests for `RiskService` heuristic scoring.

[Unreleased]: https://github.com/NitheshK4/memory-firewall/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/NitheshK4/memory-firewall/releases/tag/v0.1.0
