#!/usr/bin/env bash
# run_local_eval.sh — Run write + read evals locally and print the score table.
set -euo pipefail

echo "==> Running write-firewall eval..."
python3 evals/runners/run_write_eval.py

echo ""
echo "==> Running read-firewall eval..."
python3 evals/runners/run_read_eval.py

echo ""
echo "==> Scoring results..."
python3 evals/runners/score_results.py
