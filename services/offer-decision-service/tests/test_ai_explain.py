"""Tests for the AI explanation enhancement layer."""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ai_explain import enhance_explanation

BASE_KWARGS = {
    "base_explanation": "Test base explanation text.",
    "offer_name": "Premium Loyalty Save",
    "discount_pct": 25,
    "tenure_months": 36,
    "monthly_spend": 150.0,
    "churn_risk": 0.9,
    "current_plan": "Premium",
}


# -- No API key scenarios --


@pytest.mark.asyncio
async def test_returns_none_when_api_key_not_set():
    """When OPENAI_API_KEY is not in env, return None."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("OPENAI_API_KEY", None)
        result = await enhance_explanation(**BASE_KWARGS)
    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_api_key_empty():
    """When OPENAI_API_KEY is empty string, return None."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        result = await enhance_explanation(**BASE_KWARGS)
    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_api_key_whitespace():
    """When OPENAI_API_KEY is only whitespace, return None."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "   "}):
        result = await enhance_explanation(**BASE_KWARGS)
    assert result is None


# -- Successful OpenAI response --


def _make_openai_response(content: str):
    """Build a mock OpenAI chat completion response."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


@pytest.mark.asyncio
async def test_returns_ai_text_on_success():
    """When OpenAI returns valid text, it should be returned stripped."""
    mock_create = AsyncMock(
        return_value=_make_openai_response("  Polished explanation.  ")
    )

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    assert result == "Polished explanation."
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_openai_called_with_correct_model():
    """Verify the correct model name is passed to OpenAI."""
    mock_create = AsyncMock(return_value=_make_openai_response("Some text"))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            await enhance_explanation(**BASE_KWARGS)

    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-5-mini-2025-08-07"


@pytest.mark.asyncio
async def test_openai_receives_system_and_user_messages():
    """Verify both system and user messages are sent."""
    mock_create = AsyncMock(return_value=_make_openai_response("text"))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            await enhance_explanation(**BASE_KWARGS)

    call_kwargs = mock_create.call_args.kwargs
    messages = call_kwargs["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    # Verify subscriber context appears in user message
    assert "36 months" in messages[1]["content"]
    assert "$150.00" in messages[1]["content"]
    assert "Premium" in messages[1]["content"]


# -- Empty / whitespace OpenAI response --


@pytest.mark.asyncio
async def test_returns_none_when_openai_returns_empty():
    """When OpenAI returns empty content, return None."""
    mock_create = AsyncMock(return_value=_make_openai_response(""))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_openai_returns_whitespace():
    """When OpenAI returns only whitespace, return None."""
    mock_create = AsyncMock(return_value=_make_openai_response("   "))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_openai_returns_none_content():
    """When OpenAI message content is None, return None."""
    mock_create = AsyncMock(return_value=_make_openai_response(None))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    assert result is None


# -- OpenAI error / fallback scenarios --


@pytest.mark.asyncio
async def test_returns_none_on_openai_api_error():
    """When OpenAI raises an exception, gracefully return None."""
    mock_create = AsyncMock(side_effect=Exception("API rate limit exceeded"))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_on_connection_error():
    """When network is unavailable, return None."""
    mock_create = AsyncMock(side_effect=ConnectionError("Network unreachable"))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_on_timeout():
    """When OpenAI request times out, return None."""
    mock_create = AsyncMock(side_effect=TimeoutError("Request timed out"))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    assert result is None


# -- AI never changes the offer decision --


@pytest.mark.asyncio
async def test_ai_does_not_change_offer_decision():
    """AI explanation is only text -- offer_name and discount_pct are
    determined by the policy engine, not by the AI layer. The
    enhance_explanation function only returns a string (or None),
    never an OfferDecision."""
    mock_create = AsyncMock(
        return_value=_make_openai_response(
            "We are pleased to offer you a 50% discount on our Diamond plan!"
        )
    )

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)

    # The return value is just a string -- no offer_name / discount_pct
    assert isinstance(result, str)
    # The caller (main.py) uses the policy engine's offer_name and
    # discount_pct, not anything from this string.


@pytest.mark.asyncio
async def test_enhance_explanation_return_type_is_str_or_none():
    """The function signature returns str | None, never a dict or object."""
    # Case 1: success
    mock_create = AsyncMock(return_value=_make_openai_response("Nice explanation"))
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create
            result = await enhance_explanation(**BASE_KWARGS)
    assert isinstance(result, str)

    # Case 2: failure
    mock_create_fail = AsyncMock(side_effect=Exception("fail"))
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create = mock_create_fail
            result = await enhance_explanation(**BASE_KWARGS)
    assert result is None

    # Case 3: no key
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("OPENAI_API_KEY", None)
        result = await enhance_explanation(**BASE_KWARGS)
    assert result is None
