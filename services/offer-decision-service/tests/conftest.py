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
