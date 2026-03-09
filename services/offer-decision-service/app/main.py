import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.ai_explain import enhance_explanation
from app.logging_config import generate_request_id, setup_logging
from app.metrics import setup_metrics
from app.policy import decide
from app.schemas import OfferResponse, SubscriberRequest
from app.tracing import setup_tracing

# ── Bootstrap structured logging before anything else ──────────
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Offer Decision Service", version="0.1.0")

# ── Observability setup ────────────────────────────────────────
setup_tracing(app)
setup_metrics(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a unique request_id to every request and log it."""
    request_id = request.headers.get("X-Request-ID", generate_request_id())
    request.state.request_id = request_id

    # Inject request_id into log records for this request
    old_factory = logging.getLogRecordFactory()

    def _factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id  # type: ignore[attr-defined]
        return record

    logging.setLogRecordFactory(_factory)

    logger.info(
        "request_started",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        "request_completed",
        extra={
            "status_code": response.status_code,
        },
    )

    # Restore original factory
    logging.setLogRecordFactory(old_factory)
    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/decide", response_model=OfferResponse)
async def decide_offer(req: SubscriberRequest) -> OfferResponse:
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
