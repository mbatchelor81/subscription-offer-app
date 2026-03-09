"""Prometheus metrics instrumentation for FastAPI."""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app: FastAPI) -> None:
    """Instrument *app* and expose ``/metrics`` for Prometheus scraping.

    Default metrics include request count, latency histogram, and
    in-flight request gauge.
    """
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        excluded_handlers=["/healthz", "/metrics"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
