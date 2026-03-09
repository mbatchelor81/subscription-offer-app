"""Tests for the POST /decide API endpoint."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_decide_returns_offer():
    payload = {
        "subscriber_id": "SUB-001",
        "tenure_months": 36,
        "monthly_spend": 150.0,
        "churn_risk": 0.9,
        "current_plan": "Premium",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscriber_id"] == "SUB-001"
    assert body["offer_name"] == "Premium Loyalty Save"
    assert body["discount_pct"] == 25
    assert isinstance(body["explanation"], str)
    assert len(body["explanation"]) > 0
    assert "ai_explanation" in body
    assert body["ai_explanation"] is None  # no API key in test env


def test_decide_validation_churn_out_of_range():
    payload = {
        "subscriber_id": "SUB-002",
        "tenure_months": 12,
        "monthly_spend": 50.0,
        "churn_risk": 1.5,
        "current_plan": "Basic",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_missing_fields():
    resp = client.post("/decide", json={})
    assert resp.status_code == 422


def test_decide_low_churn_basic():
    payload = {
        "subscriber_id": "SUB-003",
        "tenure_months": 3,
        "monthly_spend": 25.0,
        "churn_risk": 0.1,
        "current_plan": "Starter",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["offer_name"] == "Mid-Tier Bundle"
    assert body["discount_pct"] == 5
    assert "ai_explanation" in body


@patch("app.main.enhance_explanation", new_callable=AsyncMock)
def test_decide_with_ai_explanation(mock_enhance):
    mock_enhance.return_value = "AI-polished explanation text."
    payload = {
        "subscriber_id": "SUB-AI",
        "tenure_months": 36,
        "monthly_spend": 150.0,
        "churn_risk": 0.9,
        "current_plan": "Premium",
    }
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["offer_name"] == "Premium Loyalty Save"
    assert body["discount_pct"] == 25
    assert body["ai_explanation"] == "AI-polished explanation text."
    mock_enhance.assert_called_once()
