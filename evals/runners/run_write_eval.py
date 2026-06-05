#!/usr/bin/env python3
"""Write-firewall evaluation runner.

Loads memory_poisoning.jsonl and benign_memory.jsonl, runs each sample
through the write firewall, and writes results to evals/reports/write_eval_results.jsonl.

Usage:
    python evals/runners/run_write_eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.api.app.config import Settings
from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.graphs.write_firewall import WriteFirewall
from apps.api.app.models.api import MemoryWriteRequest
from apps.api.app.services.claim_extractor import ClaimExtractor
from apps.api.app.services.contradiction_service import ContradictionService
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.provenance_service import ProvenanceService
from apps.api.app.services.risk_service import RiskService

DATASETS = [
    Path("evals/datasets/memory_poisoning.jsonl"),
    Path("evals/datasets/benign_memory.jsonl"),
]
REPORT_PATH = Path("evals/reports/write_eval_results.jsonl")


def build_firewall() -> WriteFirewall:
    return WriteFirewall(
        repository=InMemoryMemoryRepository(),
        claim_extractor=ClaimExtractor(Settings()),
        provenance_service=ProvenanceService(),
        contradiction_service=ContradictionService(),
        risk_service=RiskService(),
        policy_engine=PolicyEngine(),
    )


def run() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    firewall = build_firewall()
    results: list[dict] = []

    for dataset in DATASETS:
        if not dataset.exists():
            print(f"[WARN] Dataset not found: {dataset}")
            continue
        with dataset.open() as fh:
            for line in fh:
                sample = json.loads(line.strip())
                request = MemoryWriteRequest(
                    content=sample["content"],
                    source_type=sample.get("source_type", "unknown"),
                    actor=sample.get("actor", "unknown"),
                )
                response = firewall.run(request)
                actual = response.verdict.action
                expected = sample.get("expected_action", "?")
                results.append({
                    "id": sample["id"],
                    "expected": expected,
                    "actual": actual,
                    "pass": actual == expected,
                    "trust_score": response.verdict.trust_score,
                    "flags": response.memory.flags,
                    "risk_reasons": response.verdict.reasons,
                })

    with REPORT_PATH.open("w") as out:
        for r in results:
            out.write(json.dumps(r) + "\n")

    passed = sum(1 for r in results if r["pass"])
    print(f"\nWrite eval complete: {passed}/{len(results)} passed")
    print(f"Results saved to {REPORT_PATH}")


if __name__ == "__main__":
    run()
