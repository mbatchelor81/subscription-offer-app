"""
API endpoint tests for the offer decision service.

Covers input validation, error responses, HTTP status codes,
and API contract adherence to Pydantic models.
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import OfferResponse

client = TestClient(app)

VALID_PAYLOAD = {
    "subscriber_id": "SUB-100",
    "tenure_months": 36,
    "avg_monthly_spend": 120.0,
    "churn_risk": 0.85,
    "current_plan": "Basic",
}


# ── Successful requests ────────────────────────────────────────────


class TestOfferEndpointSuccess:
    """Valid POST /api/v1/offer returns correct offer decisions."""

    def test_returns_200(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        assert resp.status_code == 200

    def test_response_contains_all_fields(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        body = resp.json()
        assert "subscriber_id" in body
        assert "recommended_offer" in body
        assert "discount_pct" in body
        assert "explanation" in body
        assert "ai_explanation" in body

    def test_subscriber_id_echoed_back(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        assert resp.json()["subscriber_id"] == "SUB-100"

    def test_high_churn_high_spend_offer(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        body = resp.json()
        assert body["recommended_offer"] == "Premium Loyalty Bundle"
        assert body["discount_pct"] == 25

    def test_response_validates_against_pydantic_model(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        body = resp.json()
        # This will raise if the response doesn't match the model
        offer = OfferResponse(**body)
        assert offer.subscriber_id == "SUB-100"
        assert offer.recommended_offer == "Premium Loyalty Bundle"

    def test_explanation_is_non_empty_string(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        body = resp.json()
        assert isinstance(body["explanation"], str)
        assert len(body["explanation"]) > 0

    def test_discount_pct_is_integer(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        assert isinstance(resp.json()["discount_pct"], int)

    @patch("app.main.enhance_explanation", new_callable=AsyncMock)
    def test_ai_explanation_included_when_available(self, mock_ai):
        mock_ai.return_value = "AI-polished text here"
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        body = resp.json()
        assert body["ai_explanation"] == "AI-polished text here"

    def test_ai_explanation_none_without_api_key(self):
        """When OpenAI client is unavailable, ai_explanation should be None."""
        # The autouse conftest fixture already mocks _client() -> None
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        body = resp.json()
        assert body["ai_explanation"] is None


# ── Different policy paths via API ─────────────────────────────────


class TestOfferEndpointPolicyPaths:
    """Verify all policy branches are accessible via the API."""

    def test_loyalty_saver_plan(self):
        payload = {
            "subscriber_id": "SUB-200",
            "tenure_months": 12,
            "avg_monthly_spend": 40,
            "churn_risk": 0.75,
            "current_plan": "Basic",
        }
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.json()["recommended_offer"] == "Loyalty Saver Plan"

    def test_upsell_standard_plus(self):
        payload = {
            "subscriber_id": "SUB-201",
            "tenure_months": 30,
            "avg_monthly_spend": 35,
            "churn_risk": 0.3,
            "current_plan": "Basic",
        }
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.json()["recommended_offer"] == "Upsell to Standard Plus"

    def test_multi_line_family_addon(self):
        payload = {
            "subscriber_id": "SUB-202",
            "tenure_months": 18,
            "avg_monthly_spend": 100,
            "churn_risk": 0.2,
            "current_plan": "Premium",
        }
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.json()["recommended_offer"] == "Multi-Line Family Add-On"

    def test_welcome_booster_pack(self):
        payload = {
            "subscriber_id": "SUB-203",
            "tenure_months": 2,
            "avg_monthly_spend": 60,
            "churn_risk": 0.1,
            "current_plan": "Basic",
        }
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.json()["recommended_offer"] == "Welcome Booster Pack"

    def test_standard_renewal(self):
        payload = {
            "subscriber_id": "SUB-204",
            "tenure_months": 14,
            "avg_monthly_spend": 55,
            "churn_risk": 0.3,
            "current_plan": "Standard",
        }
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.json()["recommended_offer"] == "Standard Renewal"


# ── Input validation (422 errors) ──────────────────────────────────


class TestInputValidation:
    """Missing or invalid fields should return 422 Unprocessable Entity."""

    def test_missing_all_fields(self):
        resp = client.post("/api/v1/offer", json={})
        assert resp.status_code == 422

    def test_missing_subscriber_id(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "subscriber_id"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_missing_tenure_months(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "tenure_months"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_missing_avg_monthly_spend(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "avg_monthly_spend"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_missing_churn_risk(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "churn_risk"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_missing_current_plan(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "current_plan"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_negative_tenure_months(self):
        payload = {**VALID_PAYLOAD, "tenure_months": -1}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_negative_avg_monthly_spend(self):
        payload = {**VALID_PAYLOAD, "avg_monthly_spend": -10.0}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_churn_risk_below_zero(self):
        payload = {**VALID_PAYLOAD, "churn_risk": -0.1}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_churn_risk_above_one(self):
        payload = {**VALID_PAYLOAD, "churn_risk": 1.1}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_tenure_months_wrong_type_string(self):
        payload = {**VALID_PAYLOAD, "tenure_months": "not-a-number"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_churn_risk_wrong_type_string(self):
        payload = {**VALID_PAYLOAD, "churn_risk": "high"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422

    def test_avg_monthly_spend_wrong_type(self):
        payload = {**VALID_PAYLOAD, "avg_monthly_spend": "expensive"}
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 422


# ── Error responses ────────────────────────────────────────────────


class TestErrorResponses:
    """Test various error conditions and HTTP status codes."""

    def test_wrong_http_method_get(self):
        resp = client.get("/api/v1/offer")
        assert resp.status_code == 405

    def test_wrong_content_type(self):
        resp = client.post(
            "/api/v1/offer",
            content="not json",
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code == 422

    def test_empty_body(self):
        resp = client.post(
            "/api/v1/offer",
            content="",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_nonexistent_endpoint(self):
        resp = client.get("/api/v1/nonexistent")
        assert resp.status_code == 404

    def test_422_response_has_detail(self):
        resp = client.post("/api/v1/offer", json={})
        body = resp.json()
        assert "detail" in body
        assert isinstance(body["detail"], list)
        assert len(body["detail"]) > 0


# ── Content-Type and response format ───────────────────────────────


class TestResponseFormat:
    """Verify response headers and JSON structure."""

    def test_response_content_type_is_json(self):
        resp = client.post("/api/v1/offer", json=VALID_PAYLOAD)
        assert "application/json" in resp.headers["content-type"]

    def test_healthz_content_type(self):
        resp = client.get("/healthz")
        assert "application/json" in resp.headers["content-type"]

    def test_cors_headers_present(self):
        resp = client.options(
            "/api/v1/offer",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # CORS allows all origins
        assert resp.headers.get("access-control-allow-origin") in (
            "*",
            "http://localhost:3000",
        )
