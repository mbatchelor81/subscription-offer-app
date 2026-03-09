"""Request / response schemas for the offer-decision API."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------
_MAX_SUBSCRIBER_ID_LEN = 64
_MAX_PLAN_LEN = 64
_MAX_TENURE_MONTHS = 1200  # 100 years
_MAX_MONTHLY_SPEND = 100_000.0  # generous upper bound


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------
class SubscriberRequest(BaseModel):
    """Validated subscriber attributes for the offer-decision endpoint."""

    subscriber_id: str = Field(
        ...,
        min_length=1,
        max_length=_MAX_SUBSCRIBER_ID_LEN,
        pattern=r"^[A-Za-z0-9_\-]+$",
        description="Unique subscriber identifier (alphanumeric, hyphens, underscores)",
    )
    tenure_months: int = Field(
        ...,
        ge=0,
        le=_MAX_TENURE_MONTHS,
        description="Months the subscriber has been active (0–1200)",
    )
    monthly_spend: float = Field(
        ...,
        ge=0,
        le=_MAX_MONTHLY_SPEND,
        description="Average monthly spend in dollars (0–100 000)",
    )
    churn_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Churn probability score (0.0–1.0)",
    )
    current_plan: str = Field(
        ...,
        min_length=1,
        max_length=_MAX_PLAN_LEN,
        description="Name of the subscriber's current plan",
    )

    @model_validator(mode="after")
    def _strip_strings(self) -> "SubscriberRequest":
        """Normalise whitespace on string fields."""
        stripped_id = self.subscriber_id.strip()
        stripped_plan = self.current_plan.strip()
        if not stripped_id or not stripped_plan:
            raise ValueError("subscriber_id and current_plan must not be blank")
        object.__setattr__(self, "subscriber_id", stripped_id)
        object.__setattr__(self, "current_plan", stripped_plan)
        return self


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------
class OfferResponse(BaseModel):
    """Serialised offer recommendation returned by the API."""

    subscriber_id: str
    offer_name: str
    discount_pct: int = Field(..., ge=0, le=100)
    explanation: str
    ai_explanation: str | None = None
