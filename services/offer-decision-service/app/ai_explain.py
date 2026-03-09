"""
AI-enhanced explanation layer.

Takes the deterministic policy decision and subscriber context, then asks
OpenAI to rewrite the explanation in a polished, personalized tone.

This module is *augmentation only* — it never changes the offer or discount.
If the API key is missing or the call fails, the original policy explanation
is returned unchanged.
"""

from __future__ import annotations

import logging
import os

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful customer-retention copywriter for a telecom company. "
    "You will receive a JSON object with subscriber attributes and the "
    "deterministic offer decision (offer name, discount percentage, and a "
    "plain policy explanation). Your job is to rewrite ONLY the explanation "
    "text so it sounds polished, warm, and personalized — as if a caring "
    "account manager wrote it. "
    "Rules:\n"
    "- Do NOT change the offer name or discount amount.\n"
    "- Do NOT invent new offers, promotions, or promises.\n"
    "- Keep the rewrite to 2–3 concise sentences.\n"
    "- Reference the subscriber's specific attributes (tenure, spend, etc.) "
    "to make it feel personal.\n"
    "- Return ONLY the rewritten explanation text, no extra formatting."
)


# Timeout for OpenAI API calls in seconds
_OPENAI_TIMEOUT_SECONDS = 15.0


def _client() -> AsyncOpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    return AsyncOpenAI(api_key=key, timeout=_OPENAI_TIMEOUT_SECONDS)


async def enhance_explanation(
    *,
    subscriber_id: str,
    tenure_months: int,
    avg_monthly_spend: float,
    churn_risk: float,
    current_plan: str,
    offer_name: str,
    discount_pct: int,
    policy_explanation: str,
) -> str | None:
    """Return an AI-polished explanation, or ``None`` on failure / no key."""

    client = _client()
    if client is None:
        logger.info("OPENAI_API_KEY not set — skipping AI explanation")
        return None

    user_msg = (
        f"Subscriber: {subscriber_id}\n"
        f"Tenure: {tenure_months} months\n"
        f"Avg monthly spend: ${avg_monthly_spend:.2f}\n"
        f"Churn risk: {churn_risk:.0%}\n"
        f"Current plan: {current_plan}\n\n"
        f"Offer: {offer_name}\n"
        f"Discount: {discount_pct}%\n"
        f"Policy explanation: {policy_explanation}"
    )

    try:
        resp = await client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            max_completion_tokens=2048,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or None
    except AuthenticationError:
        logger.error("OpenAI authentication failed — check OPENAI_API_KEY")
        return None
    except RateLimitError:
        logger.warning("OpenAI rate limit reached — falling back to policy text")
        return None
    except APITimeoutError:
        logger.warning(
            "OpenAI request timed out after %ss — falling back to policy text",
            _OPENAI_TIMEOUT_SECONDS,
        )
        return None
    except APIConnectionError:
        logger.warning("Could not connect to OpenAI API — falling back to policy text")
        return None
    except OpenAIError as exc:
        logger.warning("OpenAI call failed — falling back to policy text: %s", exc)
        return None
    except Exception:
        logger.exception(
            "Unexpected error during AI explanation — falling back to policy text"
        )
        return None
