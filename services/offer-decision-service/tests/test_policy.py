"""Tests for the deterministic policy engine."""

import pytest

from app.policy import OfferDecision, decide


# -- Existing basic path tests --


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


# -- OfferDecision dataclass tests --


def test_offer_decision_is_frozen():
    d = decide(tenure_months=12, monthly_spend=50, churn_risk=0.1, current_plan="Basic")
    with pytest.raises(AttributeError):
        d.offer_name = "Tampered Offer"


def test_offer_decision_fields():
    d = decide(
        tenure_months=12, monthly_spend=50, churn_risk=0.9, current_plan="Premium"
    )
    assert isinstance(d, OfferDecision)
    assert isinstance(d.offer_name, str)
    assert isinstance(d.discount_pct, int)
    assert isinstance(d.explanation, str)
    assert len(d.explanation) > 0


# -- Churn-risk boundary tests --


def test_churn_risk_exactly_0_8_high_spend():
    d = decide(
        tenure_months=12, monthly_spend=100, churn_risk=0.8, current_plan="Basic"
    )
    assert d.offer_name == "Premium Loyalty Save"
    assert d.discount_pct == 25


def test_churn_risk_exactly_0_8_low_spend():
    d = decide(
        tenure_months=12, monthly_spend=99.99, churn_risk=0.8, current_plan="Basic"
    )
    assert d.offer_name == "Win-Back Discount"
    assert d.discount_pct == 20


def test_churn_risk_just_below_0_8():
    d = decide(
        tenure_months=30, monthly_spend=200, churn_risk=0.79, current_plan="Premium"
    )
    assert d.offer_name == "Loyalty Reward Upgrade"
    assert d.discount_pct == 15


def test_churn_risk_exactly_0_5_long_tenure():
    d = decide(tenure_months=24, monthly_spend=50, churn_risk=0.5, current_plan="Basic")
    assert d.offer_name == "Loyalty Reward Upgrade"
    assert d.discount_pct == 15


def test_churn_risk_exactly_0_5_short_tenure():
    d = decide(tenure_months=23, monthly_spend=50, churn_risk=0.5, current_plan="Basic")
    assert d.offer_name == "Retention Offer"
    assert d.discount_pct == 10


def test_churn_risk_just_below_0_5():
    d = decide(
        tenure_months=30, monthly_spend=200, churn_risk=0.49, current_plan="Premium"
    )
    assert d.offer_name == "Add-On Services Pack"
    assert d.discount_pct == 0


def test_churn_risk_zero():
    d = decide(tenure_months=12, monthly_spend=75, churn_risk=0.0, current_plan="Basic")
    assert d.offer_name == "Upgrade to Premium"
    assert d.discount_pct == 10


def test_churn_risk_one():
    d = decide(
        tenure_months=12, monthly_spend=200, churn_risk=1.0, current_plan="Premium"
    )
    assert d.offer_name == "Premium Loyalty Save"
    assert d.discount_pct == 25


# -- Spend boundary tests --


def test_high_churn_spend_exactly_100():
    d = decide(
        tenure_months=12, monthly_spend=100, churn_risk=0.9, current_plan="Basic"
    )
    assert d.offer_name == "Premium Loyalty Save"
    assert d.discount_pct == 25


def test_high_churn_spend_just_below_100():
    d = decide(
        tenure_months=12, monthly_spend=99.99, churn_risk=0.9, current_plan="Basic"
    )
    assert d.offer_name == "Win-Back Discount"
    assert d.discount_pct == 20


def test_low_churn_basic_spend_exactly_50():
    d = decide(tenure_months=12, monthly_spend=50, churn_risk=0.1, current_plan="Basic")
    assert d.offer_name == "Upgrade to Premium"
    assert d.discount_pct == 10


def test_low_churn_basic_spend_just_below_50():
    d = decide(
        tenure_months=12, monthly_spend=49.99, churn_risk=0.1, current_plan="Basic"
    )
    assert d.offer_name == "Mid-Tier Bundle"
    assert d.discount_pct == 5


# -- Tenure boundary tests --


def test_medium_churn_tenure_exactly_24():
    d = decide(tenure_months=24, monthly_spend=50, churn_risk=0.6, current_plan="Basic")
    assert d.offer_name == "Loyalty Reward Upgrade"
    assert d.discount_pct == 15


def test_medium_churn_tenure_just_below_24():
    d = decide(tenure_months=23, monthly_spend=50, churn_risk=0.6, current_plan="Basic")
    assert d.offer_name == "Retention Offer"
    assert d.discount_pct == 10


def test_zero_tenure():
    d = decide(
        tenure_months=0, monthly_spend=80, churn_risk=0.3, current_plan="Starter"
    )
    assert d.offer_name == "Upgrade to Premium"
    assert d.discount_pct == 10


def test_very_high_tenure():
    d = decide(
        tenure_months=600, monthly_spend=20, churn_risk=0.6, current_plan="Basic"
    )
    assert d.offer_name == "Loyalty Reward Upgrade"
    assert d.discount_pct == 15


# -- Zero / extreme value tests --


def test_zero_spend():
    d = decide(tenure_months=12, monthly_spend=0, churn_risk=0.3, current_plan="Basic")
    assert d.offer_name == "Mid-Tier Bundle"
    assert d.discount_pct == 5


def test_zero_spend_high_churn():
    d = decide(tenure_months=12, monthly_spend=0, churn_risk=0.9, current_plan="Basic")
    assert d.offer_name == "Win-Back Discount"
    assert d.discount_pct == 20


def test_very_high_spend():
    d = decide(
        tenure_months=12, monthly_spend=10000, churn_risk=0.9, current_plan="Premium"
    )
    assert d.offer_name == "Premium Loyalty Save"
    assert d.discount_pct == 25


def test_all_zeros_except_plan():
    d = decide(tenure_months=0, monthly_spend=0.0, churn_risk=0.0, current_plan="Basic")
    assert d.offer_name == "Mid-Tier Bundle"
    assert d.discount_pct == 5


# -- Plan name handling tests --


class TestPlanNameHandling:
    @pytest.mark.parametrize(
        "plan",
        ["basic", "Basic", "BASIC", "bAsIc"],
    )
    def test_basic_plan_case_insensitive(self, plan: str):
        d = decide(tenure_months=3, monthly_spend=25, churn_risk=0.1, current_plan=plan)
        assert d.offer_name == "Mid-Tier Bundle"

    @pytest.mark.parametrize(
        "plan",
        ["starter", "Starter", "STARTER"],
    )
    def test_starter_plan_case_insensitive(self, plan: str):
        d = decide(tenure_months=3, monthly_spend=25, churn_risk=0.1, current_plan=plan)
        assert d.offer_name == "Mid-Tier Bundle"

    @pytest.mark.parametrize(
        "plan",
        ["essentials", "Essentials", "ESSENTIALS"],
    )
    def test_essentials_plan_case_insensitive(self, plan: str):
        d = decide(tenure_months=3, monthly_spend=25, churn_risk=0.1, current_plan=plan)
        assert d.offer_name == "Mid-Tier Bundle"

    @pytest.mark.parametrize(
        "plan",
        ["premium", "Premium", "PREMIUM"],
    )
    def test_premium_plan_case_insensitive(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=100, churn_risk=0.1, current_plan=plan
        )
        assert d.offer_name == "Add-On Services Pack"

    @pytest.mark.parametrize(
        "plan",
        ["pro", "Pro", "PRO"],
    )
    def test_pro_plan_case_insensitive(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=100, churn_risk=0.1, current_plan=plan
        )
        assert d.offer_name == "Add-On Services Pack"

    @pytest.mark.parametrize(
        "plan",
        ["unlimited", "Unlimited", "UNLIMITED"],
    )
    def test_unlimited_plan_case_insensitive(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=100, churn_risk=0.1, current_plan=plan
        )
        assert d.offer_name == "Add-On Services Pack"

    def test_plan_with_leading_trailing_whitespace(self):
        d = decide(
            tenure_months=12,
            monthly_spend=100,
            churn_risk=0.1,
            current_plan="  Premium  ",
        )
        assert d.offer_name == "Add-On Services Pack"

    def test_plan_with_internal_whitespace_is_unknown(self):
        d = decide(
            tenure_months=12,
            monthly_spend=100,
            churn_risk=0.1,
            current_plan="pre mium",
        )
        assert d.offer_name == "Standard Renewal"


# -- All plan types -- low-churn path --


class TestAllPlanTypesLowChurn:
    @pytest.mark.parametrize("plan", ["basic", "starter", "essentials"])
    def test_basic_tier_high_spend(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=60, churn_risk=0.2, current_plan=plan
        )
        assert d.offer_name == "Upgrade to Premium"
        assert d.discount_pct == 10

    @pytest.mark.parametrize("plan", ["basic", "starter", "essentials"])
    def test_basic_tier_low_spend(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=30, churn_risk=0.2, current_plan=plan
        )
        assert d.offer_name == "Mid-Tier Bundle"
        assert d.discount_pct == 5

    @pytest.mark.parametrize("plan", ["premium", "pro", "unlimited"])
    def test_premium_tier(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=100, churn_risk=0.2, current_plan=plan
        )
        assert d.offer_name == "Add-On Services Pack"
        assert d.discount_pct == 0


# -- High-churn overrides plan-based logic --


class TestHighChurnOverridesPlan:
    @pytest.mark.parametrize(
        "plan",
        ["basic", "starter", "premium", "pro", "unlimited", "unknown"],
    )
    def test_high_churn_high_spend_any_plan(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=200, churn_risk=0.9, current_plan=plan
        )
        assert d.offer_name == "Premium Loyalty Save"
        assert d.discount_pct == 25

    @pytest.mark.parametrize(
        "plan",
        ["basic", "starter", "premium", "pro", "unlimited", "unknown"],
    )
    def test_high_churn_low_spend_any_plan(self, plan: str):
        d = decide(
            tenure_months=12, monthly_spend=30, churn_risk=0.85, current_plan=plan
        )
        assert d.offer_name == "Win-Back Discount"
        assert d.discount_pct == 20


# -- Discount percentage validation --


class TestDiscountPercentageRanges:
    VALID_DISCOUNTS = {0, 5, 10, 15, 20, 25}

    @pytest.mark.parametrize(
        ("tenure", "spend", "churn", "plan"),
        [
            (36, 150, 0.9, "Premium"),
            (6, 30, 0.85, "Basic"),
            (30, 60, 0.6, "Basic"),
            (10, 40, 0.55, "Starter"),
            (12, 75, 0.1, "Basic"),
            (3, 25, 0.2, "Starter"),
            (24, 120, 0.1, "Premium"),
            (12, 50, 0.2, "Legacy Gold"),
            (0, 0, 0.0, "Basic"),
            (600, 10000, 1.0, "Unlimited"),
        ],
    )
    def test_discount_is_valid(
        self, tenure: int, spend: float, churn: float, plan: str
    ):
        d = decide(
            tenure_months=tenure,
            monthly_spend=spend,
            churn_risk=churn,
            current_plan=plan,
        )
        assert d.discount_pct in self.VALID_DISCOUNTS
        assert 0 <= d.discount_pct <= 25


# -- Explanation non-empty --


class TestExplanationsNonEmpty:
    @pytest.mark.parametrize(
        ("tenure", "spend", "churn", "plan"),
        [
            (36, 150, 0.9, "Premium"),
            (6, 30, 0.85, "Basic"),
            (30, 60, 0.6, "Basic"),
            (10, 40, 0.55, "Starter"),
            (12, 75, 0.1, "Basic"),
            (3, 25, 0.2, "Starter"),
            (24, 120, 0.1, "Premium"),
            (12, 50, 0.2, "Legacy Gold"),
            (0, 0, 0.0, "Essentials"),
            (100, 500, 0.1, "Pro"),
            (50, 200, 0.3, "Unlimited"),
        ],
    )
    def test_explanation_is_non_empty(
        self, tenure: int, spend: float, churn: float, plan: str
    ):
        d = decide(
            tenure_months=tenure,
            monthly_spend=spend,
            churn_risk=churn,
            current_plan=plan,
        )
        assert isinstance(d.explanation, str)
        assert len(d.explanation.strip()) > 0
