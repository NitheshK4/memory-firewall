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
- **Retrieval auditing** — `RetrievalService` now accepts an `AuditService` and
  calls `log_retrieval(memory_id, actor, suppressed=...)` for every candidate
  evaluated during a retrieval query (served or suppressed); previously no
  retrieval events were recorded in the audit log.
- **`AuditService.get_event_stats()`** — returns `dict[str, int]` of event-type
  counts across the entire audit log; useful for dashboard throughput views.
- **`GET /api/v1/audit/stats`** — exposes `get_event_stats()` over HTTP.
- **`obfuscation` risk flag** — `RiskService` now detects base64 blobs
  (`[A-Za-z0-9+/]{20,}`) and long hex literals (`0x[0-9a-fA-F]{8,}`) in
  memory content and raises an `obfuscation` flag (+0.30 risk score).
- **`url_injection` risk flag** — `RiskService` detects `javascript:`,
  `data:text/html`, and `vbscript:` URI schemes (+0.45 risk score).
- **`PolicyEngine` hard-block for `url_injection`** — untrusted sources with
  a `url_injection` flag always receive `BLOCK`; `obfuscation` receives `BLOCK`
  when the combined risk score ≥ 0.58.
- **`RiskAssessment.contradiction_count`** — integer field populated by
  `RiskService` so callers can read the raw contradiction count without
  parsing reason strings.
- **`tags` field** on `MemoryWriteRequest` and `StoredMemory` — optional list
  of string labels; propagated through the write firewall graph.
- **`tags` query filter** on `GET /api/v1/memories` — `?tags=a&tags=b` returns
  only memories whose tag set is a superset of the requested tags.
- **`content_fingerprint()`** already present in `packages/shared/utils/hashing.py`;
  now actively used by `InMemoryMemoryRepository`.
- **Dedup guard** in `InMemoryMemoryRepository.save()` — identical content
  (normalised SHA-256 fingerprint) is detected on write; the existing record is
  returned and no duplicate is stored.
- **`AuditService.log_dedup_skip()`** — records a `dedup_skipped` audit event
  when a write is suppressed by the dedup guard.
- **`GET /api/v1/health/detailed`** — returns a per-component health report with
  `repository`, `audit_log`, and `vector_store` sub-objects including live
  memory counts, entry counts, and event distribution.
- **25 new unit tests** in `test_contributions.py` covering all of the above.

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
- `AuditService` is now constructed before `InMemoryMemoryRepository` in
  `get_container()` so dedup-skip events are logged from the start.
- `RetrievalService.__init__` now accepts an optional `audit_service` argument.

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
