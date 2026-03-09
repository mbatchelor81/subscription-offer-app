import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai_explain import enhance_explanation
from app.models import OfferResponse, SubscriberRequest
from app.observability import setup as setup_observability
from app.policy import decide

app = FastAPI(title="Offer Decision Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_observability(app)

logger = structlog.stdlib.get_logger(__name__)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/api/v1/offer", response_model=OfferResponse)
async def get_offer(req: SubscriberRequest):
    logger.info(
        "offer_request_received",
        subscriber_id=req.subscriber_id,
        current_plan=req.current_plan,
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

    logger.info(
        "offer_decision_made",
        subscriber_id=req.subscriber_id,
        offer=decision.offer_name,
        discount_pct=decision.discount_pct,
    )

    return OfferResponse(
        subscriber_id=req.subscriber_id,
        recommended_offer=decision.offer_name,
        discount_pct=decision.discount_pct,
        explanation=decision.explanation,
        ai_explanation=ai_text,
    )
