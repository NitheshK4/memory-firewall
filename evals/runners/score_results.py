#!/usr/bin/env python3
"""Eval scorer — aggregates write and read eval result files.

Reads all JSONL files in evals/reports/ and prints a summary table.

Usage:
    python evals/runners/score_results.py
"""

from __future__ import annotations

import json
from pathlib import Path


REPORTS_DIR = Path("evals/reports")


def score_file(path: Path) -> dict:
    results = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    total = len(results)
    passed = sum(1 for r in results if r.get("pass", False))
    return {
        "file": path.name,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy": round(passed / total, 3) if total > 0 else 0.0,
    }


def main() -> None:
    report_files = sorted(REPORTS_DIR.glob("*.jsonl"))
    if not report_files:
        print("No report files found in evals/reports/. Run the eval runners first.")
        return

    print(f"\n{'File':<40} {'Total':>6} {'Pass':>6} {'Fail':>6} {'Accuracy':>9}")
    print("-" * 70)
    for path in report_files:
        s = score_file(path)
        print(f"{s['file']:<40} {s['total']:>6} {s['passed']:>6} {s['failed']:>6} {s['accuracy']:>9.1%}")
    print()


if __name__ == "__main__":
    main()
