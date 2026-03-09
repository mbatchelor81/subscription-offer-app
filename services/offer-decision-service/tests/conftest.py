"""
Shared fixtures for the test suite.

The ``mock_openai_client`` fixture is applied to every test automatically
(autouse=True) so that no test accidentally calls the real OpenAI API.
Individual tests can still override the mock via their own patches.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_openai_client():
    """Prevent any real OpenAI calls during the test suite.

    By default the mock client returns ``None`` from ``_client()``,
    which mirrors the "no API key" path and makes ``enhance_explanation``
    return ``None`` quickly.
    """
    with patch("app.ai_explain._client", return_value=None) as m:
        yield m


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear the in-memory rate limiter between tests so tests don't
    interfere with each other."""
    from app.main import _rate_buckets

    _rate_buckets.clear()
    yield
    _rate_buckets.clear()


@pytest.fixture(autouse=True)
def reset_openai_client_singleton():
    """Reset the singleton OpenAI client between tests so that tests
    which manipulate OPENAI_API_KEY get a fresh initialization."""
    import app.ai_explain as ai_mod

    ai_mod._cached_client = None
    ai_mod._client_initialized = False
    yield
    ai_mod._cached_client = None
    ai_mod._client_initialized = False
