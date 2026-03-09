"""Tests for the POST /decide API endpoint."""

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "subscriber_id": "SUB-001",
    "tenure_months": 36,
    "monthly_spend": 150.0,
    "churn_risk": 0.9,
    "current_plan": "Premium",
}


# -- Happy path tests --


def test_decide_returns_offer():
    resp = client.post("/decide", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscriber_id"] == "SUB-001"
    assert body["offer_name"] == "Premium Loyalty Save"
    assert body["discount_pct"] == 25
    assert isinstance(body["explanation"], str)
    assert len(body["explanation"]) > 0
    assert "ai_explanation" in body
    assert body["ai_explanation"] is None  # mocked by conftest fixture


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


def test_decide_with_ai_explanation(_mock_ai_explanation):
    _mock_ai_explanation.return_value = "AI-polished explanation text."
    resp = client.post("/decide", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["offer_name"] == "Premium Loyalty Save"
    assert body["discount_pct"] == 25
    assert body["ai_explanation"] == "AI-polished explanation text."
    _mock_ai_explanation.assert_called_once()


# -- Response schema compliance --


def test_response_contains_all_required_fields():
    resp = client.post("/decide", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    required_fields = {
        "subscriber_id",
        "offer_name",
        "discount_pct",
        "explanation",
        "ai_explanation",
    }
    assert required_fields == set(body.keys())


def test_response_field_types():
    resp = client.post("/decide", json=VALID_PAYLOAD)
    body = resp.json()
    assert isinstance(body["subscriber_id"], str)
    assert isinstance(body["offer_name"], str)
    assert isinstance(body["discount_pct"], int)
    assert isinstance(body["explanation"], str)
    assert body["ai_explanation"] is None or isinstance(body["ai_explanation"], str)


def test_response_content_type_is_json():
    resp = client.post("/decide", json=VALID_PAYLOAD)
    assert "application/json" in resp.headers["content-type"]


# -- Validation: missing fields --


def test_decide_validation_missing_all_fields():
    resp = client.post("/decide", json={})
    assert resp.status_code == 422


def test_decide_validation_missing_subscriber_id():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "subscriber_id"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body


def test_decide_validation_missing_tenure_months():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "tenure_months"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_missing_monthly_spend():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "monthly_spend"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_missing_churn_risk():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "churn_risk"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_missing_current_plan():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "current_plan"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


# -- Validation: wrong types --


def test_decide_validation_tenure_as_string():
    payload = {**VALID_PAYLOAD, "tenure_months": "not-a-number"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_monthly_spend_as_string():
    payload = {**VALID_PAYLOAD, "monthly_spend": "expensive"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_churn_risk_as_string():
    payload = {**VALID_PAYLOAD, "churn_risk": "high"}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_subscriber_id_as_number():
    payload = {**VALID_PAYLOAD, "subscriber_id": 12345}
    resp = client.post("/decide", json=payload)
    # Pydantic may coerce int to str; important thing is no crash
    assert resp.status_code in (200, 422)


# -- Validation: out-of-range values --


def test_decide_validation_churn_above_1():
    payload = {**VALID_PAYLOAD, "churn_risk": 1.5}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_churn_below_0():
    payload = {**VALID_PAYLOAD, "churn_risk": -0.1}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_negative_tenure():
    payload = {**VALID_PAYLOAD, "tenure_months": -1}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_negative_spend():
    payload = {**VALID_PAYLOAD, "monthly_spend": -10.0}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_empty_subscriber_id():
    payload = {**VALID_PAYLOAD, "subscriber_id": ""}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


def test_decide_validation_empty_current_plan():
    payload = {**VALID_PAYLOAD, "current_plan": ""}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422


# -- Validation: boundary values that should pass --


def test_decide_churn_risk_exactly_0():
    payload = {**VALID_PAYLOAD, "churn_risk": 0.0}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200


def test_decide_churn_risk_exactly_1():
    payload = {**VALID_PAYLOAD, "churn_risk": 1.0}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200


def test_decide_tenure_zero():
    payload = {**VALID_PAYLOAD, "tenure_months": 0}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200


def test_decide_spend_zero():
    payload = {**VALID_PAYLOAD, "monthly_spend": 0.0}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 200


# -- Pydantic validation error format --


def test_validation_error_has_detail_array():
    resp = client.post("/decide", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert len(body["detail"]) > 0


def test_validation_error_entry_structure():
    resp = client.post("/decide", json={"subscriber_id": "X"})
    assert resp.status_code == 422
    body = resp.json()
    for entry in body["detail"]:
        assert "type" in entry
        # Custom error handler returns "field" (flattened loc) and "message"
        assert "field" in entry
        assert "message" in entry


def test_validation_error_churn_includes_field_location():
    payload = {**VALID_PAYLOAD, "churn_risk": 2.0}
    resp = client.post("/decide", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    # Custom error handler flattens loc into a "field" string
    fields = [e["field"] for e in body["detail"]]
    assert any("churn_risk" in f for f in fields)


# -- Content-type validation --


def test_non_json_content_type_rejected():
    resp = client.post(
        "/decide",
        content="subscriber_id=SUB-001",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 422


def test_invalid_json_body():
    resp = client.post(
        "/decide",
        content="{invalid json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


def test_null_body():
    resp = client.post(
        "/decide",
        content="null",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


# -- Concurrent request handling --


def test_concurrent_requests():
    """Verify the API handles multiple simultaneous requests correctly."""
    payloads = [
        {
            "subscriber_id": f"CONCURRENT-{i}",
            "tenure_months": 12,
            "monthly_spend": 50.0,
            "churn_risk": 0.1,
            "current_plan": "Basic",
        }
        for i in range(10)
    ]

    def make_request(payload):
        return client.post("/decide", json=payload)

    with ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(make_request, payloads))

    for i, resp in enumerate(responses):
        assert resp.status_code == 200
        body = resp.json()
        assert body["subscriber_id"] == f"CONCURRENT-{i}"
        assert body["offer_name"] == "Upgrade to Premium"


# -- HTTP method tests --


def test_get_decide_not_allowed():
    resp = client.get("/decide")
    assert resp.status_code == 405


def test_put_decide_not_allowed():
    resp = client.put("/decide", json=VALID_PAYLOAD)
    assert resp.status_code == 405


def test_delete_decide_not_allowed():
    resp = client.delete("/decide")
    assert resp.status_code == 405
