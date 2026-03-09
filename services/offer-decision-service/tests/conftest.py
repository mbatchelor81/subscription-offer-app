"""Shared fixtures for the test suite."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_ai_explanation():
    """Disable real OpenAI calls for all tests by default.

    Tests in test_ai_explain.py call enhance_explanation directly and
    handle their own mocking, so this fixture only patches the call
    site in app.main where the endpoint invokes the AI layer.
    """
    with patch("app.main.enhance_explanation", new_callable=AsyncMock) as mock:
        mock.return_value = None
        yield mock


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset the slowapi rate limiter storage before each test.

    Without this, tests that call /decide accumulate against the
    30/minute limit and later tests receive 429 responses.
    """
    from app.main import limiter

    yield
    try:
        limiter.reset()
    except Exception:
        # Fallback: clear the in-memory storage directly
        if hasattr(limiter, "_storage") and hasattr(limiter._storage, "storage"):
            limiter._storage.storage.clear()
