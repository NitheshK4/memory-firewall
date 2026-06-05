"""Structured JSON logging configuration for Memory Firewall.

Call `configure_logging()` once at startup to set up a JSON formatter
compatible with Cloud Logging / Datadog / the OTEL collector log pipeline.
"""

from __future__ import annotations

import logging
import sys

try:
    import json_log_formatter  # type: ignore[import]

    _HAS_JSON_FORMATTER = True
except ImportError:
    _HAS_JSON_FORMATTER = False


def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure root logger with optional JSON output.

    Parameters
    ----------
    level:
        Logging level string (``"DEBUG"``, ``"INFO"``, ``"WARNING"`` …).
    json_format:
        Use structured JSON output when True and *json_log_formatter* is
        installed; otherwise falls back to a human-readable format.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    if json_format and _HAS_JSON_FORMATTER:
        formatter = json_log_formatter.JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "neo4j"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
