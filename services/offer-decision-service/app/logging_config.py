"""Structured JSON logging with OpenTelemetry trace correlation."""

from __future__ import annotations

import logging
import os
import uuid

from pythonjsonlogger import jsonlogger

from opentelemetry import trace


def _current_trace_ids() -> dict[str, str]:
    """Return trace_id and span_id from the current OTEL span, or empty strings."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id != 0:
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    return {"trace_id": "", "span_id": ""}


class TraceJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that injects trace/span IDs and request_id."""

    def add_fields(
        self,
        log_record: dict,
        record: logging.LogRecord,
        message_dict: dict,
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = self.formatTime(record)
        log_record["level"] = record.levelname
        # Inject OTEL trace context
        ids = _current_trace_ids()
        log_record["trace_id"] = ids["trace_id"]
        log_record["span_id"] = ids["span_id"]
        # request_id is set per-request via middleware
        if not log_record.get("request_id"):
            log_record["request_id"] = getattr(record, "request_id", "")


def setup_logging() -> None:
    """Configure the root logger for structured JSON output."""
    log_level = os.getenv("LOG_LEVEL", "info").upper()

    handler = logging.StreamHandler()
    formatter = TraceJsonFormatter(
        fmt="%(timestamp)s %(level)s %(name)s %(message)s",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level, logging.INFO))

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def generate_request_id() -> str:
    """Generate a short unique request ID."""
    return uuid.uuid4().hex[:12]
