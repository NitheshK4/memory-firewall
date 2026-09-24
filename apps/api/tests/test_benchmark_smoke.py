"""Smoke test to ensure benchmarking suite executes cleanly."""

from evals.benchmarks.benchmark_pipeline import run_benchmarks


def test_benchmark_suite_smoke():
    results = run_benchmarks(iterations=5)
    assert "sanitisation" in results
    assert "claim_extraction" in results
    assert "write_firewall_safe" in results
    assert "write_firewall_attack" in results
    assert "read_firewall" in results

    for name, stats in results.items():
        assert stats["iterations"] == 5
        assert stats["p50_ms"] >= 0.0
        assert stats["throughput_ops_sec"] > 0.0
