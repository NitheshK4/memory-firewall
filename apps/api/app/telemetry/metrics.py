"""Prometheus-compatible metrics collection for Memory Firewall."""

from __future__ import annotations

import threading
from typing import Dict


class MetricsRegistry:
    """Thread-safe metrics registry with Prometheus exposition output."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}

    def inc_counter(self, name: str, amount: float = 1.0, labels: Dict[str, str] | None = None) -> None:
        key = self._format_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + amount

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        key = self._format_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def get_counter(self, name: str, labels: Dict[str, str] | None = None) -> float:
        key = self._format_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Dict[str, str] | None = None) -> float:
        key = self._format_key(name, labels)
        with self._lock:
            return self._gauges.get(key, 0.0)

    def reset(self) -> None:
        """Reset all metrics (primarily for test isolation)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()

    def generate_prometheus_text(self) -> str:
        """Render metrics in standard Prometheus exposition format."""
        lines: list[str] = [
            "# HELP memory_firewall_writes_total Total number of memory write requests evaluated",
            "# TYPE memory_firewall_writes_total counter",
            "# HELP memory_firewall_retrievals_total Total number of memory retrieval requests evaluated",
            "# TYPE memory_firewall_retrievals_total counter",
            "# HELP memory_firewall_dedup_skips_total Total number of duplicate writes skipped",
            "# TYPE memory_firewall_dedup_skips_total counter",
            "# HELP memory_firewall_active_memories Gauge of currently stored active memories",
            "# TYPE memory_firewall_active_memories gauge",
        ]

        with self._lock:
            for key, val in sorted(self._counters.items()):
                lines.append(f"{key} {val}")
            for key, val in sorted(self._gauges.items()):
                lines.append(f"{key} {val}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_key(name: str, labels: Dict[str, str] | None = None) -> str:
        if not labels:
            return name
        formatted_labels = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{formatted_labels}}}"


# Global default registry instance
metrics = MetricsRegistry()
