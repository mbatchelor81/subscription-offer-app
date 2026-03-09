"""
Comprehensive tests for the deterministic policy engine.

Covers all five rules plus the default path, boundary conditions,
edge cases, and plan-type variations.
"""

import pytest

from app.policy import OfferDecision, decide


# ── Rule 1: High churn-risk + high-value subscriber ────────────────


class TestHighChurnHighValue:
    """churn_risk >= 0.7 AND avg_monthly_spend >= 80 -> Premium Loyalty Bundle, 25%."""

    def test_classic_high_churn_high_spend(self):
        d = decide(tenure_months=36, avg_monthly_spend=120, churn_risk=0.85, current_plan="Basic")
        assert d.offer_name == "Premium Loyalty Bundle"
        assert d.discount_pct == 25

    def test_boundary_churn_0_7_spend_80(self):
        """Exact boundary values for both thresholds."""
        d = decide(tenure_months=12, avg_monthly_spend=80, churn_risk=0.7, current_plan="Basic")
        assert d.offer_name == "Premium Loyalty Bundle"
        assert d.discount_pct == 25

    def test_churn_1_0_max_risk(self):
        d = decide(tenure_months=6, avg_monthly_spend=100, churn_risk=1.0, current_plan="Standard")
        assert d.offer_name == "Premium Loyalty Bundle"
        assert d.discount_pct == 25

    def test_very_high_spend(self):
        d = decide(tenure_months=48, avg_monthly_spend=500, churn_risk=0.9, current_plan="Basic")
        assert d.offer_name == "Premium Loyalty Bundle"
        assert d.discount_pct == 25

    def test_rule1_takes_priority_over_premium_plan_crosssell(self):
        """Even if the subscriber is on a premium plan, Rule 1 fires first."""
        d = decide(tenure_months=24, avg_monthly_spend=100, churn_risk=0.8, current_plan="Premium")
        assert d.offer_name == "Premium Loyalty Bundle"
        assert d.discount_pct == 25

    def test_rule1_takes_priority_over_new_subscriber(self):
        """New subscriber with high churn + high spend -> Rule 1, not Rule 5."""
        d = decide(tenure_months=2, avg_monthly_spend=90, churn_risk=0.75, current_plan="Basic")
        assert d.offer_name == "Premium Loyalty Bundle"
        assert d.discount_pct == 25

    def test_rule1_takes_priority_over_upsell(self):
        """Long tenure + low spend, but high churn + high spend -> Rule 1."""
        d = decide(tenure_months=30, avg_monthly_spend=85, churn_risk=0.7, current_plan="Basic")
        assert d.offer_name == "Premium Loyalty Bundle"
        assert d.discount_pct == 25

    def test_explanation_mentions_churn_and_spend(self):
        d = decide(tenure_months=12, avg_monthly_spend=100, churn_risk=0.9, current_plan="Basic")
        assert "churn" in d.explanation.lower()
        assert "$100" in d.explanation
        assert "25%" in d.explanation


# ── Rule 2: High churn-risk, lower-value ───────────────────────────


class TestHighChurnLowValue:
    """churn_risk >= 0.7 AND avg_monthly_spend < 80 -> Loyalty Saver Plan, 15%."""

    def test_classic_high_churn_low_spend(self):
        d = decide(tenure_months=12, avg_monthly_spend=30, churn_risk=0.75, current_plan="Basic")
        assert d.offer_name == "Loyalty Saver Plan"
        assert d.discount_pct == 15

    def test_boundary_churn_0_7_spend_below_80(self):
        d = decide(tenure_months=10, avg_monthly_spend=79.99, churn_risk=0.7, current_plan="Basic")
        assert d.offer_name == "Loyalty Saver Plan"
        assert d.discount_pct == 15

    def test_zero_spend_high_churn(self):
        d = decide(tenure_months=6, avg_monthly_spend=0, churn_risk=0.8, current_plan="Basic")
        assert d.offer_name == "Loyalty Saver Plan"
        assert d.discount_pct == 15

    def test_churn_exactly_0_7_spend_zero(self):
        d = decide(tenure_months=0, avg_monthly_spend=0, churn_risk=0.7, current_plan="Basic")
        assert d.offer_name == "Loyalty Saver Plan"
        assert d.discount_pct == 15

    def test_explanation_mentions_churn(self):
        d = decide(tenure_months=12, avg_monthly_spend=40, churn_risk=0.75, current_plan="Basic")
        assert "churn" in d.explanation.lower() or "risk" in d.explanation.lower()
        assert "15%" in d.explanation


# ── Rule 3: Long-tenure, low spend -> Upsell ──────────────────────


class TestLongTenureLowSpendUpsell:
    """tenure_months >= 24 AND avg_monthly_spend < 50 -> Upsell to Standard Plus, 10%."""

    def test_classic_upsell(self):
        d = decide(tenure_months=30, avg_monthly_spend=35, churn_risk=0.3, current_plan="Basic")
        assert d.offer_name == "Upsell to Standard Plus"
        assert d.discount_pct == 10

    def test_boundary_tenure_24_spend_49(self):
        d = decide(tenure_months=24, avg_monthly_spend=49, churn_risk=0.2, current_plan="Basic")
        assert d.offer_name == "Upsell to Standard Plus"
        assert d.discount_pct == 10

    def test_boundary_tenure_24_spend_0(self):
        d = decide(tenure_months=24, avg_monthly_spend=0, churn_risk=0.1, current_plan="Basic")
        assert d.offer_name == "Upsell to Standard Plus"
        assert d.discount_pct == 10

    def test_very_long_tenure(self):
        d = decide(tenure_months=120, avg_monthly_spend=20, churn_risk=0.4, current_plan="Basic")
        assert d.offer_name == "Upsell to Standard Plus"
        assert d.discount_pct == 10

    def test_spend_exactly_50_does_not_match(self):
        """avg_monthly_spend must be strictly < 50 for Rule 3."""
        d = decide(tenure_months=36, avg_monthly_spend=50, churn_risk=0.3, current_plan="Basic")
        # spend=50 is NOT < 50, so Rule 3 does not fire; falls to default
        assert d.offer_name != "Upsell to Standard Plus"

    def test_tenure_23_does_not_match(self):
        """tenure_months must be >= 24 for Rule 3."""
        d = decide(tenure_months=23, avg_monthly_spend=30, churn_risk=0.3, current_plan="Basic")
        assert d.offer_name != "Upsell to Standard Plus"

    def test_explanation_mentions_tenure_and_spend(self):
        d = decide(tenure_months=30, avg_monthly_spend=35, churn_risk=0.3, current_plan="Basic")
        assert "30" in d.explanation
        assert "$35" in d.explanation
        assert "10%" in d.explanation


# ── Rule 4: Premium plan -> Cross-sell ─────────────────────────────


class TestPremiumPlanCrossSell:
    """plan in (premium, premium plus, unlimited) -> Multi-Line Family Add-On, 5%."""

    def test_premium_plan(self):
        d = decide(tenure_months=18, avg_monthly_spend=100, churn_risk=0.2, current_plan="Premium")
        assert d.offer_name == "Multi-Line Family Add-On"
        assert d.discount_pct == 5

    def test_premium_plus_plan(self):
        d = decide(tenure_months=18, avg_monthly_spend=80, churn_risk=0.3, current_plan="Premium Plus")
        assert d.offer_name == "Multi-Line Family Add-On"
        assert d.discount_pct == 5

    def test_unlimited_plan(self):
        d = decide(tenure_months=18, avg_monthly_spend=90, churn_risk=0.2, current_plan="Unlimited")
        assert d.offer_name == "Multi-Line Family Add-On"
        assert d.discount_pct == 5

    def test_case_insensitive_premium(self):
        d = decide(tenure_months=18, avg_monthly_spend=70, churn_risk=0.2, current_plan="PREMIUM")
        assert d.offer_name == "Multi-Line Family Add-On"
        assert d.discount_pct == 5

    def test_case_insensitive_unlimited_mixed(self):
        d = decide(tenure_months=18, avg_monthly_spend=70, churn_risk=0.2, current_plan="UnLiMiTeD")
        assert d.offer_name == "Multi-Line Family Add-On"
        assert d.discount_pct == 5

    def test_whitespace_trimming(self):
        d = decide(tenure_months=18, avg_monthly_spend=70, churn_risk=0.2, current_plan="  premium  ")
        assert d.offer_name == "Multi-Line Family Add-On"
        assert d.discount_pct == 5

    def test_premium_overridden_by_high_churn(self):
        """High churn (Rule 1/2) takes priority over premium plan (Rule 4)."""
        d = decide(tenure_months=18, avg_monthly_spend=100, churn_risk=0.8, current_plan="Premium")
        assert d.offer_name == "Premium Loyalty Bundle"

    def test_explanation_mentions_plan_and_discount(self):
        d = decide(tenure_months=18, avg_monthly_spend=90, churn_risk=0.2, current_plan="Premium")
        assert "Premium" in d.explanation
        assert "5%" in d.explanation


# ── Rule 5: New subscriber -> Welcome offer ────────────────────────


class TestNewSubscriberWelcome:
    """tenure_months < 6 -> Welcome Booster Pack, 20%."""

    def test_classic_new_subscriber(self):
        d = decide(tenure_months=2, avg_monthly_spend=60, churn_risk=0.1, current_plan="Basic")
        assert d.offer_name == "Welcome Booster Pack"
        assert d.discount_pct == 20

    def test_zero_tenure(self):
        d = decide(tenure_months=0, avg_monthly_spend=50, churn_risk=0.1, current_plan="Basic")
        assert d.offer_name == "Welcome Booster Pack"
        assert d.discount_pct == 20

    def test_tenure_5_months(self):
        d = decide(tenure_months=5, avg_monthly_spend=60, churn_risk=0.3, current_plan="Standard")
        assert d.offer_name == "Welcome Booster Pack"
        assert d.discount_pct == 20

    def test_tenure_6_does_not_match(self):
        """tenure_months must be strictly < 6."""
        d = decide(tenure_months=6, avg_monthly_spend=60, churn_risk=0.3, current_plan="Standard")
        assert d.offer_name != "Welcome Booster Pack"

    def test_new_subscriber_high_churn_goes_to_rule1(self):
        """High churn overrides the new-subscriber rule."""
        d = decide(tenure_months=1, avg_monthly_spend=100, churn_risk=0.9, current_plan="Basic")
        assert d.offer_name == "Premium Loyalty Bundle"

    def test_explanation_mentions_tenure(self):
        d = decide(tenure_months=3, avg_monthly_spend=60, churn_risk=0.1, current_plan="Basic")
        assert "3" in d.explanation
        assert "20%" in d.explanation


# ── Default: Standard Renewal ──────────────────────────────────────


class TestDefaultStandardRenewal:
    """No rules match -> Standard Renewal, 0%."""

    def test_classic_default(self):
        d = decide(tenure_months=14, avg_monthly_spend=55, churn_risk=0.3, current_plan="Standard")
        assert d.offer_name == "Standard Renewal"
        assert d.discount_pct == 0

    def test_mid_tenure_mid_spend_low_churn(self):
        d = decide(tenure_months=12, avg_monthly_spend=60, churn_risk=0.5, current_plan="Basic")
        assert d.offer_name == "Standard Renewal"
        assert d.discount_pct == 0

    def test_tenure_6_spend_50_churn_below_0_7(self):
        """All boundaries just miss every rule."""
        d = decide(tenure_months=6, avg_monthly_spend=50, churn_risk=0.69, current_plan="Basic")
        assert d.offer_name == "Standard Renewal"
        assert d.discount_pct == 0

    def test_explanation_is_present(self):
        d = decide(tenure_months=14, avg_monthly_spend=55, churn_risk=0.3, current_plan="Standard")
        assert len(d.explanation) > 0
        assert "standard renewal" in d.explanation.lower()


# ── OfferDecision dataclass ────────────────────────────────────────


class TestOfferDecisionDataclass:
    """Verify the OfferDecision dataclass behaves correctly."""

    def test_fields_accessible(self):
        od = OfferDecision(offer_name="Test", discount_pct=10, explanation="Reason")
        assert od.offer_name == "Test"
        assert od.discount_pct == 10
        assert od.explanation == "Reason"

    def test_frozen_immutable(self):
        od = OfferDecision(offer_name="Test", discount_pct=10, explanation="Reason")
        with pytest.raises(AttributeError):
            od.offer_name = "Changed"

    def test_equality(self):
        a = OfferDecision(offer_name="X", discount_pct=5, explanation="E")
        b = OfferDecision(offer_name="X", discount_pct=5, explanation="E")
        assert a == b


# ── Discount percentage range verification ─────────────────────────


class TestDiscountPercentageRanges:
    """Verify all possible discount_pct values are within 0-100."""

    @pytest.mark.parametrize(
        "tenure,spend,churn,plan",
        [
            (36, 120, 0.85, "Basic"),      # Rule 1 -> 25%
            (12, 30, 0.75, "Basic"),        # Rule 2 -> 15%
            (30, 35, 0.3, "Basic"),         # Rule 3 -> 10%
            (18, 100, 0.2, "Premium"),      # Rule 4 -> 5%
            (2, 60, 0.1, "Basic"),          # Rule 5 -> 20%
            (14, 55, 0.3, "Standard"),      # Default -> 0%
        ],
    )
    def test_discount_in_valid_range(self, tenure, spend, churn, plan):
        d = decide(tenure_months=tenure, avg_monthly_spend=spend, churn_risk=churn, current_plan=plan)
        assert 0 <= d.discount_pct <= 100


# ── Extreme / edge-case inputs ─────────────────────────────────────


class TestExtremeValues:
    """Edge cases with extreme or unusual input values."""

    def test_zero_everything(self):
        d = decide(tenure_months=0, avg_monthly_spend=0, churn_risk=0, current_plan="Basic")
        # tenure=0 < 6 -> Welcome Booster Pack
        assert d.offer_name == "Welcome Booster Pack"

    def test_very_large_tenure(self):
        d = decide(tenure_months=9999, avg_monthly_spend=60, churn_risk=0.3, current_plan="Basic")
        # tenure >= 24 but spend >= 50, not premium, tenure >= 6 -> default
        assert d.offer_name == "Standard Renewal"

    def test_very_large_spend(self):
        d = decide(tenure_months=12, avg_monthly_spend=99999, churn_risk=0.3, current_plan="Basic")
        # churn < 0.7, tenure < 24 or spend >= 50, not premium, tenure >= 6 -> default
        assert d.offer_name == "Standard Renewal"

    def test_churn_exactly_zero(self):
        d = decide(tenure_months=12, avg_monthly_spend=60, churn_risk=0.0, current_plan="Basic")
        assert d.offer_name == "Standard Renewal"

    def test_empty_plan_string(self):
        """Empty plan after strip won't match premium/unlimited."""
        d = decide(tenure_months=12, avg_monthly_spend=60, churn_risk=0.3, current_plan="")
        assert d.offer_name == "Standard Renewal"


# ── Rule priority / ordering verification ──────────────────────────


class TestRulePriority:
    """Ensure rules are evaluated top-to-bottom and first match wins."""

    def test_rule1_beats_rule2(self):
        """High churn + high spend = Rule 1, not Rule 2."""
        d = decide(tenure_months=12, avg_monthly_spend=80, churn_risk=0.7, current_plan="Basic")
        assert d.offer_name == "Premium Loyalty Bundle"

    def test_rule2_beats_rule3(self):
        """High churn + long tenure + low spend = Rule 2, not Rule 3."""
        d = decide(tenure_months=36, avg_monthly_spend=30, churn_risk=0.8, current_plan="Basic")
        assert d.offer_name == "Loyalty Saver Plan"

    def test_rule3_beats_rule4(self):
        """Long tenure + low spend on premium = Rule 3, not Rule 4."""
        d = decide(tenure_months=36, avg_monthly_spend=30, churn_risk=0.3, current_plan="Premium")
        assert d.offer_name == "Upsell to Standard Plus"

    def test_rule4_beats_rule5(self):
        """Premium plan + new subscriber = Rule 4, not Rule 5."""
        d = decide(tenure_months=3, avg_monthly_spend=80, churn_risk=0.2, current_plan="Premium")
        assert d.offer_name == "Multi-Line Family Add-On"

    def test_rule5_beats_default(self):
        """New subscriber that doesn't match 1-4 = Rule 5, not default."""
        d = decide(tenure_months=4, avg_monthly_spend=55, churn_risk=0.4, current_plan="Basic")
        assert d.offer_name == "Welcome Booster Pack"
