"""Integration tests: full request flow through policy + AI layers."""

from fastapi.testclient import TestClient

from app.main import app
from app.policy import decide
from app.schemas import OfferResponse

client = TestClient(app)


# -- Full flow without AI --


class TestFullFlowWithoutAI:
    """End-to-end: subscriber input -> policy decision -> response (no AI)."""

    def test_high_churn_premium_full_flow(self):
        payload = {
            "subscriber_id": "INT-001",
            "tenure_months": 48,
            "monthly_spend": 200.0,
            "churn_risk": 0.95,
            "current_plan": "Premium",
        }
        resp = client.post("/decide", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        # Verify policy decision is correctly reflected
        expected = decide(
            tenure_months=48,
            monthly_spend=200.0,
            churn_risk=0.95,
            current_plan="Premium",
        )
        assert body["subscriber_id"] == "INT-001"
        assert body["offer_name"] == expected.offer_name
        assert body["discount_pct"] == expected.discount_pct
        assert body["explanation"] == expected.explanation
        assert body["ai_explanation"] is None

    def test_low_churn_starter_full_flow(self):
        payload = {
            "subscriber_id": "INT-002",
            "tenure_months": 6,
            "monthly_spend": 30.0,
            "churn_risk": 0.1,
            "current_plan": "Starter",
        }
        resp = client.post("/decide", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        expected = decide(
            tenure_months=6,
            monthly_spend=30.0,
            churn_risk=0.1,
            current_plan="Starter",
        )
        assert body["offer_name"] == expected.offer_name
        assert body["discount_pct"] == expected.discount_pct
        assert body["explanation"] == expected.explanation

    def test_default_plan_full_flow(self):
        payload = {
            "subscriber_id": "INT-003",
            "tenure_months": 12,
            "monthly_spend": 50.0,
            "churn_risk": 0.2,
            "current_plan": "Legacy Gold",
        }
        resp = client.post("/decide", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["offer_name"] == "Standard Renewal"
        assert body["discount_pct"] == 0


# -- Full flow with mocked AI --


class TestFullFlowWithAI:
    """End-to-end: subscriber input -> policy -> AI explanation -> response."""

    def test_ai_explanation_included_in_response(self, _mock_ai_explanation):
        _mock_ai_explanation.return_value = "A warm, personalized explanation."
        payload = {
            "subscriber_id": "INT-AI-001",
            "tenure_months": 36,
            "monthly_spend": 150.0,
            "churn_risk": 0.9,
            "current_plan": "Premium",
        }
        resp = client.post("/decide", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        # Policy decision unchanged
        assert body["offer_name"] == "Premium Loyalty Save"
        assert body["discount_pct"] == 25
        # AI explanation present
        assert body["ai_explanation"] == "A warm, personalized explanation."
        # Base explanation also present
        assert isinstance(body["explanation"], str)
        assert len(body["explanation"]) > 0

    def test_ai_failure_does_not_break_response(self):
        """When AI returns None, the response still contains the policy decision."""
        payload = {
            "subscriber_id": "INT-AI-002",
            "tenure_months": 12,
            "monthly_spend": 75.0,
            "churn_risk": 0.5,
            "current_plan": "Basic",
        }
        resp = client.post("/decide", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["offer_name"] == "Retention Offer"
        assert body["discount_pct"] == 10
        assert body["ai_explanation"] is None
        assert isinstance(body["explanation"], str)

    def test_ai_does_not_alter_policy_fields(self, _mock_ai_explanation):
        """Even with AI, offer_name and discount_pct come from policy."""
        _mock_ai_explanation.return_value = (
            "Override attempt: offer_name=FreeStuff discount=100"
        )
        payload = {
            "subscriber_id": "INT-AI-003",
            "tenure_months": 3,
            "monthly_spend": 25.0,
            "churn_risk": 0.1,
            "current_plan": "Essentials",
        }
        resp = client.post("/decide", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        # Policy decision is untouched
        assert body["offer_name"] == "Mid-Tier Bundle"
        assert body["discount_pct"] == 5
        # AI text is just the explanation string
        assert (
            body["ai_explanation"]
            == "Override attempt: offer_name=FreeStuff discount=100"
        )


# -- Response schema compliance --


class TestResponseSchemaCompliance:
    """Verify response matches the OfferResponse Pydantic model."""

    def test_response_validates_against_pydantic_model(self):
        payload = {
            "subscriber_id": "SCHEMA-001",
            "tenure_months": 24,
            "monthly_spend": 100.0,
            "churn_risk": 0.5,
            "current_plan": "Pro",
        }
        resp = client.post("/decide", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        # This should not raise ValidationError
        model = OfferResponse(**body)
        assert model.subscriber_id == "SCHEMA-001"
        assert model.offer_name == body["offer_name"]
        assert model.discount_pct == body["discount_pct"]
        assert model.explanation == body["explanation"]

    def test_no_extra_fields_in_response(self):
        payload = {
            "subscriber_id": "SCHEMA-002",
            "tenure_months": 12,
            "monthly_spend": 50.0,
            "churn_risk": 0.3,
            "current_plan": "Basic",
        }
        resp = client.post("/decide", json=payload)
        body = resp.json()
        expected_keys = {
            "subscriber_id",
            "offer_name",
            "discount_pct",
            "explanation",
            "ai_explanation",
        }
        assert set(body.keys()) == expected_keys


# -- Multiple sequential requests --


class TestSequentialRequests:
    """Verify multiple requests produce independent, correct results."""

    def test_sequential_different_inputs(self):
        scenarios = [
            (
                {
                    "subscriber_id": "SEQ-1",
                    "tenure_months": 36,
                    "monthly_spend": 150.0,
                    "churn_risk": 0.9,
                    "current_plan": "Premium",
                },
                "Premium Loyalty Save",
                25,
            ),
            (
                {
                    "subscriber_id": "SEQ-2",
                    "tenure_months": 3,
                    "monthly_spend": 25.0,
                    "churn_risk": 0.1,
                    "current_plan": "Starter",
                },
                "Mid-Tier Bundle",
                5,
            ),
            (
                {
                    "subscriber_id": "SEQ-3",
                    "tenure_months": 30,
                    "monthly_spend": 60.0,
                    "churn_risk": 0.6,
                    "current_plan": "Basic",
                },
                "Loyalty Reward Upgrade",
                15,
            ),
            (
                {
                    "subscriber_id": "SEQ-4",
                    "tenure_months": 12,
                    "monthly_spend": 50.0,
                    "churn_risk": 0.2,
                    "current_plan": "Legacy",
                },
                "Standard Renewal",
                0,
            ),
        ]
        for payload, expected_offer, expected_discount in scenarios:
            resp = client.post("/decide", json=payload)
            assert resp.status_code == 200
            body = resp.json()
            assert body["offer_name"] == expected_offer
            assert body["discount_pct"] == expected_discount
