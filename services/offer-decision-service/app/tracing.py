"""OpenTelemetry tracing setup for FastAPI."""

from __future__ import annotations

import os

from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor


def setup_tracing(app: FastAPI) -> None:
    """Configure OpenTelemetry tracing and auto-instrument FastAPI.

    When ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set the SDK exports spans via
    OTLP/gRPC.  Otherwise a no-op provider is used so local development
    works without a collector.
    """
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    resource = Resource.create(
        {
            "service.name": "offer-decision-service",
            "service.version": "0.1.0",
        }
    )

    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        # Lazy import so we don't require grpc when no endpoint is configured
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        # In local dev / tests, use a no-op exporter that simply drops spans
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        # Use SimpleSpanProcessor with no-op-like console exporter only when
        # LOG_LEVEL is DEBUG; otherwise add no processor (spans are created
        # for trace-id propagation but not exported).
        if os.getenv("LOG_LEVEL", "info").upper() == "DEBUG":
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="healthz,metrics",
    )
