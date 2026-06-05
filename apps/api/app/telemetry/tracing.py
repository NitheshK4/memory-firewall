"""OpenTelemetry tracing initialisation for Memory Firewall.

Call `setup_tracing()` once at application startup (in the FastAPI lifespan).
Services can obtain a tracer with `get_tracer(__name__)`.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

_tracer_provider: TracerProvider | None = None


def setup_tracing(
    service_name: str = "memory-firewall",
    otlp_endpoint: str | None = None,
    console_fallback: bool = True,
) -> None:
    """Initialise the global OTEL tracer provider.

    Parameters
    ----------
    service_name:
        Logical name shown in traces.
    otlp_endpoint:
        gRPC endpoint for the OTEL collector (e.g. ``"http://otel-collector:4317"``).
        If *None*, falls back to console exporter when *console_fallback* is True.
    console_fallback:
        Emit spans to stdout when no OTLP endpoint is configured.
    """
    global _tracer_provider

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    elif console_fallback:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def get_tracer(name: str) -> trace.Tracer:
    """Return a named tracer from the global provider."""
    return trace.get_tracer(name)
