"""
AI-enhanced explanation layer.

Rewrites the deterministic policy explanation into polished,
customer-friendly language using OpenAI.  Never changes the
offer name or discount — only the wording of the explanation.

Gracefully returns None when the API key is missing or any error occurs.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a telecom customer-experience copywriter. "
    "You will receive a JSON object with subscriber context and a base explanation. "
    "Rewrite ONLY the explanation into a polished, warm, customer-friendly paragraph "
    "(2-4 sentences). Personalize it using the subscriber's tenure, spend, plan name, "
    "offer name, and discount where relevant. "
    "Do NOT change the recommended offer or discount amount — just improve the wording. "
    "Return ONLY the rewritten paragraph, no extra formatting or preamble."
)


async def enhance_explanation(
    *,
    base_explanation: str,
    offer_name: str,
    discount_pct: int,
    tenure_months: int,
    monthly_spend: float,
    churn_risk: float,
    current_plan: str,
) -> str | None:
    """Return an AI-polished explanation, or None on any failure."""

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.debug("OPENAI_API_KEY not set — skipping AI explanation")
        return None

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)

        user_content = (
            f"Subscriber context:\n"
            f"- Tenure: {tenure_months} months\n"
            f"- Avg monthly spend: ${monthly_spend:.2f}\n"
            f"- Churn risk score: {churn_risk}\n"
            f"- Current plan: {current_plan}\n"
            f"- Recommended offer: {offer_name}\n"
            f"- Discount: {discount_pct}%\n\n"
            f"Base explanation to rewrite:\n{base_explanation}"
        )

        response = await client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_completion_tokens=2048,
        )

        text = response.choices[0].message.content
        if text and text.strip():
            return text.strip()

        logger.warning("OpenAI returned empty content")
        return None

    except Exception:
        # Log only the exception type — never the full traceback which
        # could contain the API key in HTTP headers or request bodies.
        logger.error(
            "AI explanation failed (type=%s) — falling back to base",
            type(Exception).__name__,
        )
        return None
