"""Request / response schemas for the offer-decision API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SubscriberRequest(BaseModel):
    subscriber_id: str = Field(..., min_length=1, description="Unique subscriber identifier")
    tenure_months: int = Field(..., ge=0, description="Months the subscriber has been active")
    monthly_spend: float = Field(..., ge=0, description="Average monthly spend in dollars")
    churn_risk: float = Field(..., ge=0, le=1, description="Churn probability score (0–1)")
    current_plan: str = Field(..., min_length=1, description="Name of the subscriber's current plan")


class OfferResponse(BaseModel):
    subscriber_id: str
    offer_name: str
    discount_pct: int
    explanation: str
    ai_explanation: str | None = None
