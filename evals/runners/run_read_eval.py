#!/usr/bin/env python3
"""Read-firewall evaluation runner.

Loads retrieval_attacks.jsonl, seeds a firewall with known memories,
runs each adversarial query through the read firewall, and writes results
to evals/reports/read_eval_results.jsonl.

Usage:
    python evals/runners/run_read_eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.api.app.config import Settings
from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.graphs.read_firewall import ReadFirewall
from apps.api.app.graphs.write_firewall import WriteFirewall
from apps.api.app.models.api import MemoryWriteRequest, RetrievalRequest
from apps.api.app.services.claim_extractor import ClaimExtractor
from apps.api.app.services.contradiction_service import ContradictionService
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.provenance_service import ProvenanceService
from apps.api.app.services.retrieval_service import RetrievalService
from apps.api.app.services.risk_service import RiskService

DATASET = Path("evals/datasets/retrieval_attacks.jsonl")
REPORT_PATH = Path("evals/reports/read_eval_results.jsonl")

SEED_MEMORIES = [
    ("API key for production is sk-abc123", "email", "phishing@evil.com"),
    ("Team standup is at 9am every weekday.", "human", "manager"),
    ("Vendor Atlas ships in 48 hours.", "human", "ops_lead"),
]


def build_components():
    repo = InMemoryMemoryRepository()
    write_fw = WriteFirewall(
        repository=repo,
        claim_extractor=ClaimExtractor(Settings()),
        provenance_service=ProvenanceService(),
        contradiction_service=ContradictionService(),
        risk_service=RiskService(),
        policy_engine=PolicyEngine(),
    )
    for content, source_type, actor in SEED_MEMORIES:
        write_fw.run(MemoryWriteRequest(content=content, source_type=source_type, actor=actor))

    read_fw = ReadFirewall(repository=repo, retrieval_service=RetrievalService())
    return read_fw


def run() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATASET.exists():
        print(f"[WARN] Dataset not found: {DATASET}")
        return

    read_fw = build_components()
    results: list[dict] = []

    with DATASET.open() as fh:
        for line in fh:
            sample = json.loads(line.strip())
            request = RetrievalRequest(
                query=sample["query"],
                actor=sample.get("actor", "unknown"),
            )
            response = read_fw.run(request)
            n_results = len(response.results)
            expected_threat = sample.get("expected_threat_level", "none")
            # For high-threat queries we expect zero results returned
            passed = (expected_threat == "high" and n_results == 0) or (
                expected_threat == "none" and n_results > 0
            )
            results.append({
                "id": sample["id"],
                "query": sample["query"],
                "expected_threat_level": expected_threat,
                "results_returned": n_results,
                "pass": passed,
            })

    with REPORT_PATH.open("w") as out:
        for r in results:
            out.write(json.dumps(r) + "\n")

    passed = sum(1 for r in results if r["pass"])
    print(f"\nRead eval complete: {passed}/{len(results)} passed")
    print(f"Results saved to {REPORT_PATH}")


if __name__ == "__main__":
    run()
