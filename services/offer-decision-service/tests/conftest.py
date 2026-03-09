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
