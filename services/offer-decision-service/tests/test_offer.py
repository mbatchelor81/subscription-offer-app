from fastapi.testclient import TestClient

from app.main import app
from app.policy import decide

client = TestClient(app)


# ── Policy unit tests ──────────────────────────────────────────────


def test_high_churn_high_value():
    d = decide(
        tenure_months=36, avg_monthly_spend=120, churn_risk=0.85, current_plan="Basic"
    )
    assert d.offer_name == "Premium Loyalty Bundle"
    assert d.discount_pct == 25


def test_high_churn_low_value():
    d = decide(
        tenure_months=12, avg_monthly_spend=30, churn_risk=0.75, current_plan="Basic"
    )
    assert d.offer_name == "Loyalty Saver Plan"
    assert d.discount_pct == 15


def test_long_tenure_low_spend_upsell():
    d = decide(
        tenure_months=30, avg_monthly_spend=35, churn_risk=0.3, current_plan="Basic"
    )
    assert d.offer_name == "Upsell to Standard Plus"
    assert d.discount_pct == 10


def test_premium_plan_cross_sell():
    d = decide(
        tenure_months=18, avg_monthly_spend=100, churn_risk=0.2, current_plan="Premium"
    )
    assert d.offer_name == "Multi-Line Family Add-On"
    assert d.discount_pct == 5


def test_new_subscriber_welcome():
    d = decide(
        tenure_months=2, avg_monthly_spend=60, churn_risk=0.1, current_plan="Basic"
    )
    assert d.offer_name == "Welcome Booster Pack"
    assert d.discount_pct == 20


def test_default_standard_renewal():
    d = decide(
        tenure_months=14, avg_monthly_spend=55, churn_risk=0.3, current_plan="Standard"
    )
    assert d.offer_name == "Standard Renewal"
    assert d.discount_pct == 0


# ── API integration tests ─────────────────────────────────────────


def test_offer_endpoint_success():
    resp = client.post(
        "/api/v1/offer",
        json={
            "subscriber_id": "SUB-001",
            "tenure_months": 36,
            "avg_monthly_spend": 120,
            "churn_risk": 0.85,
            "current_plan": "Basic",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscriber_id"] == "SUB-001"
    assert body["recommended_offer"] == "Premium Loyalty Bundle"
    assert body["discount_pct"] == 25
    assert len(body["explanation"]) > 0
    # ai_explanation is None when OPENAI_API_KEY is not set
    assert "ai_explanation" in body


def test_offer_endpoint_validation_error():
    resp = client.post(
        "/api/v1/offer",
        json={"subscriber_id": "SUB-002"},
    )
    assert resp.status_code == 422
