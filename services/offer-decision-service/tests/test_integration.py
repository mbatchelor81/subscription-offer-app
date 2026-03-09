"""
End-to-end integration tests for the offer decision service.

Exercises the full request -> policy -> explanation -> response flow
via the FastAPI TestClient, with OpenAI mocked to avoid external calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import OfferResponse, SubscriberRequest

client = TestClient(app)


def _mock_openai(ai_text: str = "AI-enhanced explanation."):
    """Create a patch context that mocks the OpenAI client."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=ai_text))
    ]
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return patch("app.ai_explain._client", return_value=mock_client)


# ── Full flow: request -> policy -> AI -> response ─────────────────


class TestFullFlowWithAI:
    """End-to-end tests with AI explanation mocked to return a value."""

    def test_high_churn_high_value_full_flow(self):
        with _mock_openai("Personalized retention message for valued customer."):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-001",
                    "tenure_months": 36,
                    "avg_monthly_spend": 120,
                    "churn_risk": 0.85,
                    "current_plan": "Basic",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["subscriber_id"] == "INT-001"
        assert body["recommended_offer"] == "Premium Loyalty Bundle"
        assert body["discount_pct"] == 25
        assert len(body["explanation"]) > 0
        assert body["ai_explanation"] == "Personalized retention message for valued customer."

    def test_loyalty_saver_full_flow(self):
        with _mock_openai("We value your loyalty and want to help you save."):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-002",
                    "tenure_months": 10,
                    "avg_monthly_spend": 30,
                    "churn_risk": 0.75,
                    "current_plan": "Basic",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_offer"] == "Loyalty Saver Plan"
        assert body["discount_pct"] == 15
        assert body["ai_explanation"] == "We value your loyalty and want to help you save."

    def test_upsell_full_flow(self):
        with _mock_openai("As a long-time customer, you deserve more."):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-003",
                    "tenure_months": 30,
                    "avg_monthly_spend": 35,
                    "churn_risk": 0.3,
                    "current_plan": "Basic",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_offer"] == "Upsell to Standard Plus"
        assert body["discount_pct"] == 10
        assert body["ai_explanation"] == "As a long-time customer, you deserve more."

    def test_cross_sell_premium_full_flow(self):
        with _mock_openai("Expand your premium experience with family."):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-004",
                    "tenure_months": 18,
                    "avg_monthly_spend": 100,
                    "churn_risk": 0.2,
                    "current_plan": "Premium",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_offer"] == "Multi-Line Family Add-On"
        assert body["discount_pct"] == 5

    def test_welcome_pack_full_flow(self):
        with _mock_openai("Welcome aboard! Here's a special gift for you."):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-005",
                    "tenure_months": 2,
                    "avg_monthly_spend": 60,
                    "churn_risk": 0.1,
                    "current_plan": "Basic",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_offer"] == "Welcome Booster Pack"
        assert body["discount_pct"] == 20

    def test_standard_renewal_full_flow(self):
        with _mock_openai("Thank you for being a steady subscriber."):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-006",
                    "tenure_months": 14,
                    "avg_monthly_spend": 55,
                    "churn_risk": 0.3,
                    "current_plan": "Standard",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_offer"] == "Standard Renewal"
        assert body["discount_pct"] == 0


# ── Full flow: AI unavailable (graceful degradation) ───────────────


class TestFullFlowWithoutAI:
    """End-to-end with AI returning None (no key or API failure)."""

    def test_offer_still_returned_when_ai_unavailable(self):
        with patch("app.ai_explain._client", return_value=None):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-010",
                    "tenure_months": 36,
                    "avg_monthly_spend": 120,
                    "churn_risk": 0.85,
                    "current_plan": "Basic",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_offer"] == "Premium Loyalty Bundle"
        assert body["discount_pct"] == 25
        assert body["explanation"] is not None
        assert body["ai_explanation"] is None

    def test_policy_explanation_preserved_when_ai_fails(self):
        from openai import OpenAIError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=OpenAIError("Service down")
        )

        with patch("app.ai_explain._client", return_value=mock_client):
            resp = client.post(
                "/api/v1/offer",
                json={
                    "subscriber_id": "INT-011",
                    "tenure_months": 2,
                    "avg_monthly_spend": 60,
                    "churn_risk": 0.1,
                    "current_plan": "Basic",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["recommended_offer"] == "Welcome Booster Pack"
        assert body["discount_pct"] == 20
        assert len(body["explanation"]) > 0
        assert body["ai_explanation"] is None


# ── Response contract validation ───────────────────────────────────


class TestResponseContract:
    """Ensure the full response always conforms to the Pydantic model."""

    @pytest.mark.parametrize(
        "payload",
        [
            {
                "subscriber_id": "CONTRACT-1",
                "tenure_months": 36,
                "avg_monthly_spend": 120,
                "churn_risk": 0.85,
                "current_plan": "Basic",
            },
            {
                "subscriber_id": "CONTRACT-2",
                "tenure_months": 0,
                "avg_monthly_spend": 0,
                "churn_risk": 0,
                "current_plan": "Basic",
            },
            {
                "subscriber_id": "CONTRACT-3",
                "tenure_months": 100,
                "avg_monthly_spend": 200,
                "churn_risk": 1.0,
                "current_plan": "Unlimited",
            },
        ],
    )
    def test_response_matches_offer_response_model(self, payload):
        resp = client.post("/api/v1/offer", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        # Validate all fields parse correctly
        offer = OfferResponse(**body)
        assert offer.subscriber_id == payload["subscriber_id"]
        assert isinstance(offer.recommended_offer, str)
        assert 0 <= offer.discount_pct <= 100
        assert isinstance(offer.explanation, str)
        assert offer.ai_explanation is None or isinstance(offer.ai_explanation, str)

    def test_request_model_validation(self):
        """Verify SubscriberRequest model enforces field constraints."""
        # Valid
        req = SubscriberRequest(
            subscriber_id="TEST",
            tenure_months=12,
            avg_monthly_spend=50.0,
            churn_risk=0.5,
            current_plan="Basic",
        )
        assert req.subscriber_id == "TEST"

        # Invalid: negative tenure
        with pytest.raises(Exception):
            SubscriberRequest(
                subscriber_id="TEST",
                tenure_months=-1,
                avg_monthly_spend=50.0,
                churn_risk=0.5,
                current_plan="Basic",
            )

        # Invalid: churn_risk > 1
        with pytest.raises(Exception):
            SubscriberRequest(
                subscriber_id="TEST",
                tenure_months=12,
                avg_monthly_spend=50.0,
                churn_risk=1.5,
                current_plan="Basic",
            )


# ── Multiple sequential requests ───────────────────────────────────


class TestSequentialRequests:
    """Verify the service handles multiple sequential requests correctly."""

    def test_different_subscribers_get_different_offers(self):
        payloads = [
            {
                "subscriber_id": "SEQ-1",
                "tenure_months": 36,
                "avg_monthly_spend": 120,
                "churn_risk": 0.85,
                "current_plan": "Basic",
            },
            {
                "subscriber_id": "SEQ-2",
                "tenure_months": 2,
                "avg_monthly_spend": 60,
                "churn_risk": 0.1,
                "current_plan": "Basic",
            },
            {
                "subscriber_id": "SEQ-3",
                "tenure_months": 14,
                "avg_monthly_spend": 55,
                "churn_risk": 0.3,
                "current_plan": "Standard",
            },
        ]
        offers = []
        for payload in payloads:
            resp = client.post("/api/v1/offer", json=payload)
            assert resp.status_code == 200
            offers.append(resp.json()["recommended_offer"])

        assert offers[0] == "Premium Loyalty Bundle"
        assert offers[1] == "Welcome Booster Pack"
        assert offers[2] == "Standard Renewal"

    def test_same_input_yields_same_output(self):
        """Deterministic policy: identical inputs -> identical outputs."""
        payload = {
            "subscriber_id": "DETERM-1",
            "tenure_months": 18,
            "avg_monthly_spend": 100,
            "churn_risk": 0.2,
            "current_plan": "Premium",
        }
        responses = []
        for _ in range(3):
            resp = client.post("/api/v1/offer", json=payload)
            assert resp.status_code == 200
            responses.append(resp.json())

        # All three responses should have the same offer and discount
        for r in responses:
            assert r["recommended_offer"] == responses[0]["recommended_offer"]
            assert r["discount_pct"] == responses[0]["discount_pct"]
            assert r["explanation"] == responses[0]["explanation"]


# ── Health endpoint in integration context ─────────────────────────


class TestHealthIntegration:
    """Health endpoint works alongside offer endpoint."""

    def test_health_and_offer_coexist(self):
        health_resp = client.get("/healthz")
        assert health_resp.status_code == 200
        assert health_resp.json() == {"status": "ok"}

        offer_resp = client.post(
            "/api/v1/offer",
            json={
                "subscriber_id": "HEALTH-1",
                "tenure_months": 12,
                "avg_monthly_spend": 50,
                "churn_risk": 0.3,
                "current_plan": "Basic",
            },
        )
        assert offer_resp.status_code == 200
