"""Offer Decision Service — FastAPI application."""

from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai_explain import enhance_explanation
from app.models import OfferResponse, SubscriberRequest
from app.policy import decide

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Offer Decision Service",
    version="0.1.0",
    # Do not expose detailed docs in production
    docs_url="/docs" if os.getenv("APP_ENV", "local") != "production" else None,
    redoc_url="/redoc" if os.getenv("APP_ENV", "local") != "production" else None,
)

# ---------------------------------------------------------------------------
# CORS — configurable via ALLOWED_ORIGINS env var (comma-separated)
# ---------------------------------------------------------------------------
_default_origins = ["http://localhost:3000"]
_allowed_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
] or _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------------------
# Simple in-memory rate limiter for the offer endpoint
# ---------------------------------------------------------------------------
_RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
_RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))  # requests per window

# Mapping from client IP → list of request timestamps
_rate_buckets: dict[str, list[float]] = {}


def _is_rate_limited(client_ip: str) -> bool:
    """Return True if *client_ip* has exceeded the rate limit."""
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW
    bucket = _rate_buckets.get(client_ip, [])
    # Prune old entries; evict key entirely when empty
    pruned = [t for t in bucket if t > window_start]
    if not pruned:
        _rate_buckets.pop(client_ip, None)
    else:
        _rate_buckets[client_ip] = pruned
    if len(pruned) >= _RATE_LIMIT_MAX:
        return True
    _rate_buckets.setdefault(client_ip, []).append(now)
    return False


# ---------------------------------------------------------------------------
# Global exception handler — never leak stack traces
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/api/v1/offer", response_model=OfferResponse)
async def get_offer(request: Request, req: SubscriberRequest):
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again later."},
        )

    decision = decide(
        tenure_months=req.tenure_months,
        avg_monthly_spend=req.avg_monthly_spend,
        churn_risk=req.churn_risk,
        current_plan=req.current_plan,
    )

    ai_text = await enhance_explanation(
        subscriber_id=req.subscriber_id,
        tenure_months=req.tenure_months,
        avg_monthly_spend=req.avg_monthly_spend,
        churn_risk=req.churn_risk,
        current_plan=req.current_plan,
        offer_name=decision.offer_name,
        discount_pct=decision.discount_pct,
        policy_explanation=decision.explanation,
    )

    return OfferResponse(
        subscriber_id=req.subscriber_id,
        recommended_offer=decision.offer_name,
        discount_pct=decision.discount_pct,
        explanation=decision.explanation,
        ai_explanation=ai_text,
    )
