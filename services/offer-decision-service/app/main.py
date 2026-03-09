from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai_explain import enhance_explanation
from app.policy import decide
from app.schemas import OfferResponse, SubscriberRequest

app = FastAPI(title="Offer Decision Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
