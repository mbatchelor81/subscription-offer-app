"""Tests for observability: /metrics endpoint, structured logging, tracing."""

import io
import json
import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── /metrics endpoint ──────────────────────────────────────────


def test_metrics_endpoint_returns_prometheus_format():
    """/metrics should return Prometheus text exposition format."""
    # Hit another endpoint first so there is at least one metric sample
    client.get("/healthz")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Prometheus exposition must contain HELP / TYPE lines
    assert "# HELP" in body
    assert "# TYPE" in body
    # Should contain standard HTTP metrics
    assert "http_request_duration" in body or "http_requests_total" in body


# ── Structured logging ─────────────────────────────────────────


def test_structured_json_logging():
    """Log output should be valid JSON with required fields."""
    # Attach a temporary stream handler to capture JSON output directly
    root = logging.getLogger()
    buf = io.StringIO()
    # Re-use the same formatter that setup_logging installs
    handler = logging.StreamHandler(buf)
    handler.setFormatter(root.handlers[0].formatter)
    root.addHandler(handler)

    try:
        client.get("/healthz")
    finally:
        root.removeHandler(handler)

    output = buf.getvalue()
    json_lines = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                json_lines.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    assert len(json_lines) > 0, "Expected at least one JSON log line"

    # Check that structured fields are present
    log_entry = json_lines[0]
    assert "timestamp" in log_entry
    assert "level" in log_entry
    assert "message" in log_entry


def test_request_id_in_response_header():
    """Every response should include an X-Request-ID header."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) > 0


def test_custom_request_id_is_echoed():
    """If the client sends X-Request-ID, the server should echo it back."""
    custom_id = "test-req-12345"
    resp = client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == custom_id


# ── Health endpoint performance ────────────────────────────────


def test_healthz_performance():
    """/healthz should respond in under 10ms (no performance regression)."""
    import time

    times = []
    for _ in range(10):
        start = time.perf_counter()
        resp = client.get("/healthz")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        times.append(elapsed_ms)

    avg_ms = sum(times) / len(times)
    assert avg_ms < 10, f"/healthz avg latency {avg_ms:.2f}ms exceeds 10ms"
