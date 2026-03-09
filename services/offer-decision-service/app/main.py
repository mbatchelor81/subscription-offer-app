"""Offer Decision Service — FastAPI application with security hardening."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.ai_explain import enhance_explanation
from app.policy import decide
from app.schemas import OfferResponse, SubscriberRequest

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ---------------------------------------------------------------------------
# App factory helpers
# ---------------------------------------------------------------------------
_REQUEST_BODY_MAX_BYTES = 1 * 1024 * 1024  # 1 MiB — generous for JSON payloads

# Determine allowed CORS origins from environment; fall back to localhost for
# local development.  In production set ALLOWED_ORIGINS to a comma-separated
# list (e.g. "https://app.example.com,https://admin.example.com").
_DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
_allowed_origins: list[str] = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
] or _DEFAULT_ORIGINS.split(",")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Offer Decision Service",
    version="0.1.0",
    # Hide /docs and /redoc in production to reduce attack surface
    docs_url="/docs" if os.environ.get("APP_ENV") != "production" else None,
    redoc_url="/redoc" if os.environ.get("APP_ENV") != "production" else None,
)

app.state.limiter = limiter


# ---------------------------------------------------------------------------
# Middleware — security headers
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security headers into every response."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
        # Remove the default Server header if present
        if "Server" in response.headers:
            del response.headers["Server"]
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)


# ---------------------------------------------------------------------------
# Middleware — request body size limit
# ---------------------------------------------------------------------------
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured maximum."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"},
                )
            if length > _REQUEST_BODY_MAX_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )
        return await call_next(request)


app.add_middleware(RequestSizeLimitMiddleware)


# ---------------------------------------------------------------------------
# Custom error handlers — never leak internals
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def _validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a safe 422 without exposing stack traces or internal paths."""
    safe_errors: list[dict[str, object]] = []
    for err in exc.errors():
        safe_errors.append(
            {
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )
    return JSONResponse(
        status_code=422,
        content={"detail": safe_errors},
    )


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(
    _request: Request, _exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


@app.exception_handler(Exception)
async def _generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log the real error, return a generic message."""
    logger.exception("Unhandled exception: %s", type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/decide", response_model=OfferResponse)
@limiter.limit("30/minute")
async def decide_offer(request: Request, req: SubscriberRequest) -> OfferResponse:
    decision = decide(
        tenure_months=req.tenure_months,
        monthly_spend=req.monthly_spend,
        churn_risk=req.churn_risk,
        current_plan=req.current_plan,
    )

    ai_text = await enhance_explanation(
        base_explanation=decision.explanation,
        offer_name=decision.offer_name,
        discount_pct=decision.discount_pct,
        tenure_months=req.tenure_months,
        monthly_spend=req.monthly_spend,
        churn_risk=req.churn_risk,
        current_plan=req.current_plan,
    )

    return OfferResponse(
        subscriber_id=req.subscriber_id,
        offer_name=decision.offer_name,
        discount_pct=decision.discount_pct,
        explanation=decision.explanation,
        ai_explanation=ai_text,
    )
