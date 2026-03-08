"""
Deterministic offer-policy engine.

Rules are evaluated top-to-bottom; the first matching rule wins.
Every decision is fully explainable — no ML/AI involved in the selection.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfferDecision:
    offer_name: str
    discount_pct: int  # 0-100
    explanation: str


def decide(
    tenure_months: int,
    avg_monthly_spend: float,
    churn_risk: float,
    current_plan: str,
) -> OfferDecision:
    """Return the best offer for a subscriber based on deterministic policy rules."""

    plan = current_plan.strip().lower()

    # ── Rule 1: High churn-risk, high-value subscriber → aggressive retention ──
    if churn_risk >= 0.7 and avg_monthly_spend >= 80:
        return OfferDecision(
            offer_name="Premium Loyalty Bundle",
            discount_pct=25,
            explanation=(
                f"This subscriber has a high churn risk ({churn_risk:.0%}) "
                f"and spends ${avg_monthly_spend:.0f}/mo, making them a high-value "
                "retention target. A 25% loyalty discount on the Premium bundle "
                "is recommended to prevent churn."
            ),
        )

    # ── Rule 2: High churn-risk, lower-value → moderate retention ──
    if churn_risk >= 0.7:
        return OfferDecision(
            offer_name="Loyalty Saver Plan",
            discount_pct=15,
            explanation=(
                f"Churn risk is elevated ({churn_risk:.0%}). A 15% discount "
                "on the Loyalty Saver Plan can help retain this subscriber "
                "without heavy margin impact."
            ),
        )

    # ── Rule 3: Long-tenure, low spend → upsell opportunity ──
    if tenure_months >= 24 and avg_monthly_spend < 50:
        return OfferDecision(
            offer_name="Upsell to Standard Plus",
            discount_pct=10,
            explanation=(
                f"With {tenure_months} months of tenure but only "
                f"${avg_monthly_spend:.0f}/mo average spend, this loyal "
                "subscriber is a good candidate for a 10% introductory "
                "discount on Standard Plus."
            ),
        )

    # ── Rule 4: Already on premium plan, stable → cross-sell add-on ──
    if plan in ("premium", "premium plus", "unlimited"):
        return OfferDecision(
            offer_name="Multi-Line Family Add-On",
            discount_pct=5,
            explanation=(
                f"Subscriber is on the {current_plan} plan with moderate risk "
                f"({churn_risk:.0%}). A 5% discount on the Multi-Line Family "
                "Add-On encourages household expansion."
            ),
        )

    # ── Rule 5: New subscriber (< 6 months) → welcome offer ──
    if tenure_months < 6:
        return OfferDecision(
            offer_name="Welcome Booster Pack",
            discount_pct=20,
            explanation=(
                f"This subscriber joined only {tenure_months} month(s) ago. "
                "A 20% Welcome Booster Pack discount helps cement early loyalty."
            ),
        )

    # ── Default: no special offer ──
    return OfferDecision(
        offer_name="Standard Renewal",
        discount_pct=0,
        explanation=(
            "No special risk or opportunity signals detected. "
            "The subscriber is offered a standard renewal at the current rate."
        ),
    )
