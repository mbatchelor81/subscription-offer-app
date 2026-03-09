"""Tests for the deterministic policy engine."""

from app.policy import decide


def test_high_churn_high_spend():
    d = decide(
        tenure_months=36, monthly_spend=150, churn_risk=0.9, current_plan="Premium"
    )
    assert d.offer_name == "Premium Loyalty Save"
    assert d.discount_pct == 25


def test_high_churn_low_spend():
    d = decide(tenure_months=6, monthly_spend=30, churn_risk=0.85, current_plan="Basic")
    assert d.offer_name == "Win-Back Discount"
    assert d.discount_pct == 20


def test_medium_churn_long_tenure():
    d = decide(tenure_months=30, monthly_spend=60, churn_risk=0.6, current_plan="Basic")
    assert d.offer_name == "Loyalty Reward Upgrade"
    assert d.discount_pct == 15


def test_medium_churn_short_tenure():
    d = decide(
        tenure_months=10, monthly_spend=40, churn_risk=0.55, current_plan="Starter"
    )
    assert d.offer_name == "Retention Offer"
    assert d.discount_pct == 10


def test_low_churn_basic_high_spend():
    d = decide(tenure_months=12, monthly_spend=75, churn_risk=0.1, current_plan="Basic")
    assert d.offer_name == "Upgrade to Premium"
    assert d.discount_pct == 10


def test_low_churn_basic_low_spend():
    d = decide(
        tenure_months=3, monthly_spend=25, churn_risk=0.2, current_plan="Starter"
    )
    assert d.offer_name == "Mid-Tier Bundle"
    assert d.discount_pct == 5


def test_low_churn_premium_plan():
    d = decide(
        tenure_months=24, monthly_spend=120, churn_risk=0.1, current_plan="Premium"
    )
    assert d.offer_name == "Add-On Services Pack"
    assert d.discount_pct == 0


def test_default_unknown_plan():
    d = decide(
        tenure_months=12, monthly_spend=50, churn_risk=0.2, current_plan="Legacy Gold"
    )
    assert d.offer_name == "Standard Renewal"
    assert d.discount_pct == 0
