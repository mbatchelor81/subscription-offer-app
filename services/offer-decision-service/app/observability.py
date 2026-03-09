"""
Observability bootstrap: structured logging, OpenTelemetry tracing, Prometheus metrics.

Call ``setup()`` once at application startup (before any requests are served).
"""

from __future__ import annotations

import logging
import os
import uuid
from contextvars import ContextVar

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Context variable for per-request ID
# ---------------------------------------------------------------------------
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

SERVICE_NAME = "offer-decision-service"


def get_request_id() -> str:
    """Return the current request ID (or ``'-'`` outside a request)."""
    return _request_id_ctx.get()


# ---------------------------------------------------------------------------
# Structured logging configuration
# ---------------------------------------------------------------------------


def _add_otel_context(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: dict,
) -> dict:
    """Inject trace_id, span_id, and request_id into every log entry."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = f"{ctx.trace_id:032x}"
        event_dict["span_id"] = f"{ctx.span_id:016x}"
    else:
        event_dict.setdefault("trace_id", "")
        event_dict.setdefault("span_id", "")
    event_dict["request_id"] = get_request_id()
    return event_dict


def _configure_logging(log_level: str) -> None:
    """Set up structlog with JSON rendering and stdlib integration."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_otel_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level.upper())

    # Quieten noisy third-party loggers
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True


# ---------------------------------------------------------------------------
# OpenTelemetry tracing
# ---------------------------------------------------------------------------


def _configure_tracing() -> None:
    """Set up OTEL tracing with OTLP exporter (or no-op if no endpoint)."""
    resource = Resource.create({"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


# ---------------------------------------------------------------------------
# Request-ID middleware
# ---------------------------------------------------------------------------


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique ``X-Request-ID`` to every request."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        token = _request_id_ctx.set(rid)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            _request_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# Public bootstrap helper
# ---------------------------------------------------------------------------


def setup(app) -> None:  # noqa: ANN001
    """Wire logging, tracing, and metrics into a FastAPI application.

    Parameters
    ----------
    app:
        The ``FastAPI`` instance to instrument.
    """
    log_level = os.getenv("LOG_LEVEL", "info")

    # 1. Structured logging (must come first so later init logs are captured)
    _configure_logging(log_level)

    # 2. OpenTelemetry tracing
    _configure_tracing()

    # 3. Auto-instrument FastAPI for tracing
    FastAPIInstrumentor.instrument_app(app)

    # 4. Request-ID middleware
    app.add_middleware(RequestIDMiddleware)

    # 5. Prometheus metrics (exposes /metrics)
    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
