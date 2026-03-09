"""Tests for security hardening: validation, error handling, headers, rate limiting."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

from app.main import _rate_buckets, app
from app.models import ALLOWED_PLANS

client = TestClient(app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_VALID_PAYLOAD = {
    "subscriber_id": "SUB-001",
    "tenure_months": 36,
    "avg_monthly_spend": 120.0,
    "churn_risk": 0.85,
    "current_plan": "Basic",
}


def _post_offer(overrides: dict | None = None):
    payload = {**_VALID_PAYLOAD, **(overrides or {})}
    return client.post("/api/v1/offer", json=payload)


# ---------------------------------------------------------------------------
# Input validation — subscriber_id
# ---------------------------------------------------------------------------
class TestSubscriberIdValidation:
    def test_valid_id(self):
        assert _post_offer().status_code == 200

    def test_empty_id(self):
        resp = _post_offer({"subscriber_id": ""})
        assert resp.status_code == 422

    def test_too_long_id(self):
        resp = _post_offer({"subscriber_id": "A" * 65})
        assert resp.status_code == 422

    def test_special_chars_rejected(self):
        resp = _post_offer({"subscriber_id": "SUB 001!@#"})
        assert resp.status_code == 422

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped, then validated."""
        resp = _post_offer({"subscriber_id": " SUB-001 "})
        assert resp.status_code == 200
        assert resp.json()["subscriber_id"] == "SUB-001"

    def test_hyphens_underscores_allowed(self):
        resp = _post_offer({"subscriber_id": "SUB_001-abc"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Input validation — tenure_months
# ---------------------------------------------------------------------------
class TestTenureValidation:
    def test_negative(self):
        resp = _post_offer({"tenure_months": -1})
        assert resp.status_code == 422

    def test_too_large(self):
        resp = _post_offer({"tenure_months": 1201})
        assert resp.status_code == 422

    def test_boundary_zero(self):
        resp = _post_offer({"tenure_months": 0})
        assert resp.status_code == 200

    def test_boundary_max(self):
        resp = _post_offer({"tenure_months": 1200})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Input validation — avg_monthly_spend
# ---------------------------------------------------------------------------
class TestSpendValidation:
    def test_negative(self):
        resp = _post_offer({"avg_monthly_spend": -0.01})
        assert resp.status_code == 422

    def test_too_large(self):
        resp = _post_offer({"avg_monthly_spend": 100_001})
        assert resp.status_code == 422

    def test_boundary_max(self):
        resp = _post_offer({"avg_monthly_spend": 100_000})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Input validation — churn_risk
# ---------------------------------------------------------------------------
class TestChurnRiskValidation:
    def test_below_zero(self):
        resp = _post_offer({"churn_risk": -0.01})
        assert resp.status_code == 422

    def test_above_one(self):
        resp = _post_offer({"churn_risk": 1.01})
        assert resp.status_code == 422

    def test_boundary_zero(self):
        resp = _post_offer({"churn_risk": 0.0})
        assert resp.status_code == 200

    def test_boundary_one(self):
        resp = _post_offer({"churn_risk": 1.0})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Input validation — current_plan (enum enforcement)
# ---------------------------------------------------------------------------
class TestCurrentPlanValidation:
    def test_invalid_plan(self):
        resp = _post_offer({"current_plan": "SuperDuper"})
        assert resp.status_code == 422
        body = resp.json()
        assert "current_plan must be one of" in str(body)

    def test_empty_plan(self):
        resp = _post_offer({"current_plan": ""})
        assert resp.status_code == 422

    @pytest.mark.parametrize("plan", sorted(ALLOWED_PLANS))
    def test_all_allowed_plans(self, plan: str):
        resp = _post_offer({"current_plan": plan})
        assert resp.status_code == 200

    def test_case_insensitive(self):
        resp = _post_offer({"current_plan": "PREMIUM"})
        assert resp.status_code == 200

    def test_whitespace_stripped(self):
        resp = _post_offer({"current_plan": " Basic "})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Validation — model-level via Pydantic
# ---------------------------------------------------------------------------
class TestPydanticModel:
    def test_missing_fields_returns_422(self):
        resp = client.post("/api/v1/offer", json={"subscriber_id": "X"})
        assert resp.status_code == 422

    def test_422_body_contains_detail(self):
        resp = client.post("/api/v1/offer", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" in body


# ---------------------------------------------------------------------------
# Global exception handler — 500 with safe message
# ---------------------------------------------------------------------------
class TestGlobalExceptionHandler:
    def test_unhandled_error_returns_500(self):
        with patch("app.main.decide", side_effect=RuntimeError("boom")):
            resp = _post_offer()
        assert resp.status_code == 500
        body = resp.json()
        assert body == {"detail": "Internal server error"}
        # Must NOT contain stack trace
        assert "Traceback" not in str(body)
        assert "boom" not in str(body)


# ---------------------------------------------------------------------------
# OpenAI error handling — graceful degradation
# ---------------------------------------------------------------------------
class TestAIExplainErrorHandling:
    """AI failures should return None (policy explanation used instead)."""

    @pytest.mark.parametrize(
        "exc",
        [
            AuthenticationError(
                message="bad key",
                response=AsyncMock(status_code=401, headers={}),
                body=None,
            ),
            RateLimitError(
                message="rate limited",
                response=AsyncMock(status_code=429, headers={}),
                body=None,
            ),
            APITimeoutError(request=AsyncMock()),
            APIConnectionError(request=AsyncMock()),
        ],
        ids=["auth", "rate_limit", "timeout", "connection"],
    )
    def test_openai_errors_degrade_gracefully(self, exc):
        with patch("app.ai_explain._client") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.chat.completions.create.side_effect = exc
            mock_client.return_value = mock_instance

            resp = _post_offer()

        assert resp.status_code == 200
        body = resp.json()
        # Policy explanation should always be present
        assert len(body["explanation"]) > 0
        # AI explanation should be None on failure
        assert body["ai_explanation"] is None

    def test_no_api_key_returns_none(self):
        """When OPENAI_API_KEY is unset, ai_explanation is None."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            resp = _post_offer()
        assert resp.status_code == 200
        assert resp.json()["ai_explanation"] is None


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
class TestSecurityHeaders:
    def test_healthz_has_security_headers(self):
        resp = client.get("/healthz")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["X-XSS-Protection"] == "1; mode=block"
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in resp.headers["Permissions-Policy"]
        assert resp.headers["Cache-Control"] == "no-store"

    def test_offer_endpoint_has_security_headers(self):
        resp = _post_offer()
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
class TestRateLimiting:
    def setup_method(self):
        """Clear rate-limit buckets before each test."""
        _rate_buckets.clear()

    def test_under_limit_succeeds(self):
        resp = _post_offer()
        assert resp.status_code == 200

    def test_over_limit_returns_429(self):
        with patch("app.main._RATE_LIMIT_MAX", 2):
            _post_offer()
            _post_offer()
            resp = _post_offer()
        assert resp.status_code == 429
        assert "Rate limit" in resp.json()["detail"]
