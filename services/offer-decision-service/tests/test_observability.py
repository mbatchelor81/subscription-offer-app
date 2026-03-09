"""Tests for the observability layer (metrics, structured logging, tracing)."""

import io
import json
import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Prometheus metrics ────────────────────────────────────────────


def test_metrics_endpoint_returns_prometheus_format():
    """GET /metrics should return Prometheus text exposition format."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"] or (
        "openmetrics" in resp.headers.get("content-type", "")
    )
    body = resp.text
    # Prometheus instrumentator should expose at least these metric families
    assert "http_request_duration_seconds" in body or ("http_requests_total" in body)


def test_metrics_populated_after_requests():
    """After hitting an endpoint, /metrics should reflect the traffic."""
    # Drive some traffic first
    client.get("/healthz")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Should contain histogram buckets from the healthz request
    assert "http_request_duration" in body or "http_requests" in body


# ── Structured logging ────────────────────────────────────────────


def test_structured_logs_are_json():
    """Log output should be valid JSON with expected fields."""
    import structlog

    # Attach a temporary handler with a StringIO buffer so we can capture
    # output reliably (capsys cannot intercept handlers created at import time).
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    # Re-use the same formatter the app configures on the root handler
    root = logging.getLogger()
    if root.handlers:
        handler.setFormatter(root.handlers[0].formatter)
    else:
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
        )

    root.addHandler(handler)
    try:
        log = structlog.stdlib.get_logger("test")
        log.info("test_event", extra_key="extra_value")
        handler.flush()
        output = buf.getvalue().strip()
    finally:
        root.removeHandler(handler)

    assert output, "Expected structured log output but got nothing"
    parsed = json.loads(output)
    assert parsed["event"] == "test_event"
    assert "timestamp" in parsed
    assert "level" in parsed


# ── Request-ID middleware ─────────────────────────────────────────


def test_request_id_generated_when_not_provided():
    """Responses should include X-Request-ID even without one in the request."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    rid = resp.headers.get("x-request-id")
    assert rid is not None
    assert len(rid) > 0


def test_request_id_echoed_when_provided():
    """When a request includes X-Request-ID, the response should echo it."""
    custom_id = "my-custom-request-id-123"
    resp = client.get("/healthz", headers={"x-request-id": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") == custom_id


# ── Healthz still works ──────────────────────────────────────────


def test_healthz_unaffected():
    """Observability should not break the health endpoint."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
