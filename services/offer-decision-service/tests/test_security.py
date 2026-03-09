"""Security-focused tests for hardened middleware and validation."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Validation — subscriber_id regex & length
# ---------------------------------------------------------------------------


def test_subscriber_id_rejects_special_chars():
    payload = {
        "subscriber_id": "SUB <script>alert(1)</script>",
        "tenure_months": 12,
        "monthly_spend": 50.0,
        "churn_risk": 0.5,
        "current_plan": "Basic",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_subscriber_id_max_length():
    payload = {
        "subscriber_id": "A" * 65,  # exceeds 64-char limit
        "tenure_months": 12,
        "monthly_spend": 50.0,
        "churn_risk": 0.5,
        "current_plan": "Basic",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Validation — numeric bounds
# ---------------------------------------------------------------------------


def test_tenure_months_upper_bound():
    payload = {
        "subscriber_id": "SUB-001",
        "tenure_months": 1201,  # exceeds 1200
        "monthly_spend": 50.0,
        "churn_risk": 0.5,
        "current_plan": "Basic",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_monthly_spend_upper_bound():
    payload = {
        "subscriber_id": "SUB-001",
        "tenure_months": 12,
        "monthly_spend": 100_001.0,
        "churn_risk": 0.5,
        "current_plan": "Basic",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_negative_tenure_rejected():
    payload = {
        "subscriber_id": "SUB-001",
        "tenure_months": -1,
        "monthly_spend": 50.0,
        "churn_risk": 0.5,
        "current_plan": "Basic",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Error response shape — no stack traces
# ---------------------------------------------------------------------------


def test_validation_error_hides_internals():
    """422 responses should not contain stack traces or file paths."""
    resp = client.post("/decide", json={})
    assert resp.status_code == 422
    body = resp.json()
    # Should have our safe error format
    assert "detail" in body
    for err in body["detail"]:
        assert "field" in err
        assert "message" in err
        assert "type" in err
    # Should NOT contain traceback keywords
    raw = resp.text
    assert "Traceback" not in raw
    assert "File " not in raw


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


def test_security_headers_on_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "max-age=" in resp.headers.get("Strict-Transport-Security", "")


# ---------------------------------------------------------------------------
# Request body size limit
# ---------------------------------------------------------------------------


def test_oversized_request_rejected():
    """Content-Length > 1 MiB should be rejected with 413."""
    resp = client.post(
        "/decide",
        content=b"x" * (1024 * 1024 + 1),
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(1024 * 1024 + 1),
        },
    )
    assert resp.status_code == 413
