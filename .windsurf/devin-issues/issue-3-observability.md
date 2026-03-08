# Phase 2: Observability Baseline (OpenTelemetry + Prometheus)

## Objective
Instrument the offer-decision-service with OpenTelemetry tracing, Prometheus metrics, and structured logging.

## Tracing (OpenTelemetry)
- Add dependencies: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-exporter-otlp`
- Auto-instrument FastAPI so every HTTP request produces a span
- Configure OTEL exporter endpoint via env var (`OTEL_EXPORTER_OTLP_ENDPOINT`), default to no-op in local dev
- Ensure trace/span IDs appear in log output

## Metrics (Prometheus)
- Add `prometheus-fastapi-instrumentator` (or equivalent)
- Expose `/metrics` endpoint for Prometheus scraping
- Default metrics: request count, latency histogram, in-flight requests

## Structured Logging
- Switch to structured **JSON logs** (use `python-json-logger` or `structlog`)
- Include: timestamp, level, request_id, trace_id, span_id, message
- Configurable log level via `LOG_LEVEL` env var (already in `.env.example`)

## Helm Chart Updates
- Add OTEL collector endpoint to `values.yaml` as a configurable value
- Add Prometheus scrape annotations to the Service/Pod template

## Optional
- Basic Grafana dashboard JSON in `infra/grafana/` (nice-to-have)

## Acceptance Criteria
- [ ] `/metrics` endpoint returns Prometheus-format metrics
- [ ] Logs are structured JSON with request IDs
- [ ] OTEL traces are emitted when a collector is configured
- [ ] No performance regression on `/healthz` (trivial endpoint still < 10ms)
- [ ] Existing tests still pass

## Context
- Backend is FastAPI/Uvicorn (Python 3.12)
- `AGENTS.md` describes project conventions
- This is part of Phase 2 industrialization
