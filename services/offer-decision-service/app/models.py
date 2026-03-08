from typing import Optional

from pydantic import BaseModel, Field


class SubscriberRequest(BaseModel):
    subscriber_id: str = Field(..., description="Unique subscriber identifier")
    tenure_months: int = Field(..., ge=0, description="How long the subscriber has been a customer")
    avg_monthly_spend: float = Field(..., ge=0, description="Average monthly spend in dollars")
    churn_risk: float = Field(..., ge=0, le=1, description="Churn risk score between 0 and 1")
    current_plan: str = Field(..., description="Current subscription plan name")


class OfferResponse(BaseModel):
    subscriber_id: str
    recommended_offer: str
    discount_pct: int = Field(..., ge=0, le=100)
    explanation: str
    ai_explanation: Optional[str] = Field(
        None,
        description="AI-polished version of the explanation (None if unavailable)",
    )
