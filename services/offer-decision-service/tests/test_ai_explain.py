"""
Tests for the AI explanation enhancement module.

All OpenAI interactions are mocked — no real API calls are made.
Verifies fallback behaviour, error handling, and that AI never
changes the offer decision itself.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai_explain import _client, enhance_explanation

# Common kwargs used across tests
_BASE_KWARGS = dict(
    subscriber_id="SUB-001",
    tenure_months=24,
    avg_monthly_spend=100.0,
    churn_risk=0.8,
    current_plan="Basic",
    offer_name="Premium Loyalty Bundle",
    discount_pct=25,
    policy_explanation="High churn risk and high value subscriber.",
)


# ── _client() helper ───────────────────────────────────────────────


class TestClientHelper:
    """Tests for the _client() function that creates an AsyncOpenAI client."""

    def test_returns_none_when_no_api_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            assert _client() is None

    def test_returns_none_when_key_is_whitespace(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "   "}, clear=False):
            assert _client() is None

    def test_returns_none_when_key_not_set(self):
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("OPENAI_API_KEY", None)
            assert _client() is None

    def test_returns_client_when_key_set(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}, clear=False):
            c = _client()
            assert c is not None


# ── enhance_explanation() with mocked OpenAI ───────────────────────


class TestEnhanceExplanationSuccess:
    """Test successful AI enhancement with mocked OpenAI responses."""

    @pytest.mark.asyncio
    async def test_returns_polished_text(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Polished AI explanation text."))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            result = await enhance_explanation(**_BASE_KWARGS)

        assert result == "Polished AI explanation text."

    @pytest.mark.asyncio
    async def test_calls_openai_with_correct_model(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Enhanced text."))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            await enhance_explanation(**_BASE_KWARGS)

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-5-mini-2025-08-07"

    @pytest.mark.asyncio
    async def test_passes_system_and_user_messages(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Enhanced text."))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            await enhance_explanation(**_BASE_KWARGS)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_user_message_contains_subscriber_info(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Enhanced text."))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            await enhance_explanation(**_BASE_KWARGS)

        call_kwargs = mock_client.chat.completions.create.call_args
        user_msg = call_kwargs.kwargs["messages"][1]["content"]
        assert "SUB-001" in user_msg
        assert "24 months" in user_msg
        assert "$100.00" in user_msg
        assert "80%" in user_msg
        assert "Basic" in user_msg
        assert "Premium Loyalty Bundle" in user_msg
        assert "25%" in user_msg

    @pytest.mark.asyncio
    async def test_strips_whitespace_from_response(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="  Polished text with spaces.  "))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            result = await enhance_explanation(**_BASE_KWARGS)

        assert result == "Polished text with spaces."


# ── Fallback behavior ──────────────────────────────────────────────


class TestEnhanceExplanationFallback:
    """Test fallback when OpenAI is unavailable or returns errors."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_api_key(self):
        with patch("app.ai_explain._client", return_value=None):
            result = await enhance_explanation(**_BASE_KWARGS)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_openai_error(self):
        from openai import OpenAIError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=OpenAIError("API error")
        )

        with patch("app.ai_explain._client", return_value=mock_client):
            result = await enhance_explanation(**_BASE_KWARGS)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_response(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=""))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            result = await enhance_explanation(**_BASE_KWARGS)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_whitespace_only_response(self):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="   "))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            result = await enhance_explanation(**_BASE_KWARGS)

        # After strip, empty string is falsy -> returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_logs_warning_on_openai_error(self):
        from openai import OpenAIError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=OpenAIError("Connection timeout")
        )

        with (
            patch("app.ai_explain._client", return_value=mock_client),
            patch("app.ai_explain.logger") as mock_logger,
        ):
            await enhance_explanation(**_BASE_KWARGS)

        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "falling back" in warning_msg.lower() or "failed" in warning_msg.lower()

    @pytest.mark.asyncio
    async def test_logs_info_when_no_api_key(self):
        with (
            patch("app.ai_explain._client", return_value=None),
            patch("app.ai_explain.logger") as mock_logger,
        ):
            await enhance_explanation(**_BASE_KWARGS)

        mock_logger.info.assert_called_once()


# ── AI never changes the offer decision ────────────────────────────


class TestAINeverChangesDecision:
    """Verify that the AI module is augmentation-only: it can change
    explanation wording but never the offer_name or discount_pct."""

    @pytest.mark.asyncio
    async def test_ai_text_is_separate_from_policy_decision(self):
        """The enhance_explanation function returns a string (or None).
        It does NOT return an OfferDecision or modify offer_name/discount_pct."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="A warm personalized message."))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            result = await enhance_explanation(**_BASE_KWARGS)

        # Result is only a string, not an offer decision
        assert isinstance(result, str)
        # The original policy explanation is unchanged (it's a separate input)
        assert _BASE_KWARGS["policy_explanation"] == "High churn risk and high value subscriber."

    @pytest.mark.asyncio
    async def test_enhance_returns_only_text_type(self):
        """Return type is str | None, never a dict or object with offer fields."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Nice explanation."))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.ai_explain._client", return_value=mock_client):
            result = await enhance_explanation(**_BASE_KWARGS)

        assert result is None or isinstance(result, str)
