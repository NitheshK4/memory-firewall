#!/usr/bin/env python3
"""Eval scorer — aggregates write and read eval result files.

Reads all JSONL files in evals/reports/ and prints:
  1. A summary table with a visual accuracy bar for each file.
  2. A per-file failure breakdown listing each failing case with its
     expected vs actual verdict and the risk flags that drove the decision.

Usage:
    python evals/runners/score_results.py           # all report files
    python evals/runners/score_results.py --verbose # include flag details
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPORTS_DIR = Path("evals/reports")
BAR_WIDTH = 20  # characters for the accuracy bar


def _accuracy_bar(accuracy: float, width: int = BAR_WIDTH) -> str:
    """Return a Unicode block-bar representing *accuracy* (0–1)."""
    filled = round(accuracy * width)
    empty = width - filled
    colour = "\033[92m" if accuracy >= 0.9 else "\033[93m" if accuracy >= 0.7 else "\033[91m"
    reset = "\033[0m"
    return f"{colour}{'█' * filled}{'░' * empty}{reset}"


def score_file(path: Path) -> dict:
    results: list[dict] = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    total = len(results)
    passed = sum(1 for r in results if r.get("pass", False))
    failures = [r for r in results if not r.get("pass", False)]

    # Build confusion breakdown: how many are false-positives vs false-negatives.
    false_positives: list[dict] = []  # expected benign, got blocked/quarantine
    false_negatives: list[dict] = []  # expected block/quarantine, got allow

    benign_labels = {"allow", "low_trust"}
    threat_labels = {"block", "quarantine"}

    for r in failures:
        expected = r.get("expected", "")
        actual = r.get("actual", "")
        if expected in benign_labels and actual in threat_labels:
            false_positives.append(r)
        elif expected in threat_labels and actual in benign_labels:
            false_negatives.append(r)

    return {
        "file": path.name,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy": round(passed / total, 3) if total > 0 else 0.0,
        "failures": failures,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def _print_failures(failures: list[dict], *, show_flags: bool) -> None:
    if not failures:
        return
    print(f"\n  {'ID':<12} {'Expected':<14} {'Actual':<14} Flags")
    print(f"  {'-'*12} {'-'*14} {'-'*14} {'-'*30}")
    for r in failures:
        rid = r.get("id", "?")
        expected = r.get("expected", "?")
        actual = r.get("actual", "?")
        flags = ", ".join(r.get("flags", [])) if show_flags else ""
        print(f"  {rid:<12} {expected:<14} {actual:<14} {flags}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Memory Firewall eval reports.")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include risk flags in the failure breakdown.",
    )
    args = parser.parse_args()

    report_files = sorted(REPORTS_DIR.glob("*.jsonl"))
    if not report_files:
        print("No report files found in evals/reports/. Run the eval runners first.")
        return

    # ── Summary table ──────────────────────────────────────────────────────
    col_w = max(len(p.name) for p in report_files) + 2
    print(f"\n{'File':<{col_w}} {'Total':>6} {'Pass':>6} {'Fail':>6} {'Accuracy':>9}  {'':>{BAR_WIDTH}}")
    print("─" * (col_w + 6 + 6 + 6 + 9 + BAR_WIDTH + 6))

    scores = []
    for path in report_files:
        s = score_file(path)
        scores.append(s)
        bar = _accuracy_bar(s["accuracy"])
        print(
            f"{s['file']:<{col_w}} {s['total']:>6} {s['passed']:>6} "
            f"{s['failed']:>6} {s['accuracy']:>9.1%}  {bar}"
        )
    print()

    # ── Per-file failure breakdown ─────────────────────────────────────────
    for s in scores:
        if not s["failures"]:
            continue
        print(f"{'─' * 70}")
        print(f"  Failures in {s['file']}  ({s['failed']} / {s['total']})")
        _print_failures(s["failures"], show_flags=args.verbose)

        fp = len(s["false_positives"])
        fn = len(s["false_negatives"])
        other = s["failed"] - fp - fn
        print(
            f"\n  Confusion summary:  "
            f"false-positive={fp}  false-negative={fn}  other={other}"
        )
        print()


if __name__ == "__main__":
    main()
