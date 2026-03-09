"""
Deterministic offer-decision policy engine.

Rules are evaluated top-to-bottom; the first matching rule wins.
AI is never involved in the decision — only in explanation wording.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfferDecision:
    offer_name: str
    discount_pct: int          # 0 means no discount
    explanation: str


def decide(
    tenure_months: int,
    monthly_spend: float,
    churn_risk: float,
    current_plan: str,
) -> OfferDecision:
    """Return a deterministic offer based on subscriber attributes."""

    plan = current_plan.strip().lower()

    # ── High churn-risk retention offers ────────────────────────
    if churn_risk >= 0.8:
        if monthly_spend >= 100:
            return OfferDecision(
                offer_name="Premium Loyalty Save",
                discount_pct=25,
                explanation=(
                    "This subscriber is a high-value customer at serious risk of "
                    "churning. A 25% loyalty discount on their current plan is "
                    "recommended to retain their significant monthly spend."
                ),
            )
        return OfferDecision(
            offer_name="Win-Back Discount",
            discount_pct=20,
            explanation=(
                "This subscriber shows very high churn risk. A 20% discount is "
                "offered as an incentive to stay and re-engage with the service."
            ),
        )

    # ── Medium churn-risk retention offers ──────────────────────
    if churn_risk >= 0.5:
        if tenure_months >= 24:
            return OfferDecision(
                offer_name="Loyalty Reward Upgrade",
                discount_pct=15,
                explanation=(
                    "A long-tenured subscriber with moderate churn risk qualifies "
                    "for a loyalty reward — a 15% discount to acknowledge their "
                    "continued commitment."
                ),
            )
        return OfferDecision(
            offer_name="Retention Offer",
            discount_pct=10,
            explanation=(
                "Moderate churn risk detected. A 10% retention discount is "
                "recommended to reduce the likelihood of this subscriber leaving."
            ),
        )

    # ── Low churn-risk — focus on upsell ────────────────────────
    if plan in ("basic", "starter", "essentials"):
        if monthly_spend >= 50:
            return OfferDecision(
                offer_name="Upgrade to Premium",
                discount_pct=10,
                explanation=(
                    "This subscriber is on a basic-tier plan but already spends "
                    "well above average. They are a strong candidate for a "
                    "Premium upgrade with a 10% introductory discount."
                ),
            )
        return OfferDecision(
            offer_name="Mid-Tier Bundle",
            discount_pct=5,
            explanation=(
                "A basic-tier subscriber with low churn risk is offered a "
                "mid-tier bundle at a 5% discount to encourage plan growth."
            ),
        )

    if plan in ("premium", "pro", "unlimited"):
        return OfferDecision(
            offer_name="Add-On Services Pack",
            discount_pct=0,
            explanation=(
                "This subscriber is already on a top-tier plan with low churn "
                "risk. Recommend complementary add-on services (e.g. cloud "
                "storage, international roaming) at full price to increase ARPU."
            ),
        )

    # ── Default / catch-all ─────────────────────────────────────
    return OfferDecision(
        offer_name="Standard Renewal",
        discount_pct=0,
        explanation=(
            "No special risk or upsell signals detected. The subscriber is "
            "offered a standard plan renewal at the current rate."
        ),
    )
