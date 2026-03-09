"""Pydantic request/response models with strict input validation."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Allowed plan names (case-insensitive match)
ALLOWED_PLANS = frozenset(
    {
        "basic",
        "standard",
        "standard plus",
        "premium",
        "premium plus",
        "unlimited",
    }
)

_SUBSCRIBER_ID_RE = re.compile(r"^[A-Za-z0-9\-_]{1,64}$")


class SubscriberRequest(BaseModel):
    """Incoming subscriber attributes for offer decisioning."""

    subscriber_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique subscriber identifier (alphanumeric, hyphens, underscores)",
    )
    tenure_months: int = Field(
        ...,
        ge=0,
        le=1200,
        description="How long the subscriber has been a customer (0–1200 months)",
    )
    avg_monthly_spend: float = Field(
        ...,
        ge=0,
        le=100_000,
        description="Average monthly spend in dollars (0–100 000)",
    )
    churn_risk: float = Field(
        ...,
        ge=0,
        le=1,
        description="Churn risk score between 0.0 and 1.0",
    )
    current_plan: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Current subscription plan name",
    )

    @field_validator("subscriber_id")
    @classmethod
    def validate_subscriber_id(cls, v: str) -> str:
        v = v.strip()
        if not _SUBSCRIBER_ID_RE.match(v):
            raise ValueError(
                "subscriber_id must contain only alphanumeric characters, "
                "hyphens, or underscores (1–64 chars)"
            )
        return v

    @field_validator("current_plan")
    @classmethod
    def validate_current_plan(cls, v: str) -> str:
        v = v.strip()
        if v.lower() not in ALLOWED_PLANS:
            allowed = ", ".join(sorted(ALLOWED_PLANS))
            raise ValueError(
                f"current_plan must be one of: {allowed} (case-insensitive)"
            )
        return v


class OfferResponse(BaseModel):
    """Offer recommendation returned to the caller."""

    subscriber_id: str
    recommended_offer: str
    discount_pct: int = Field(..., ge=0, le=100)
    explanation: str
    ai_explanation: Optional[str] = Field(
        None,
        description="AI-polished version of the explanation (None if unavailable)",
    )
