# Backlog — Phase 3 and Beyond

Items below are prioritised roughly top-to-bottom within each category.
Each item includes a brief rationale and an estimated T-shirt size.

---

## A/B Testing & Experimentation

| # | Item | Size | Notes |
|---|------|------|-------|
| 1 | **Offer A/B framework** — route a percentage of requests to an alternate policy rule set and record which variant was shown | M | Requires a subscriber-variant assignment store (Redis or DynamoDB) |
| 2 | **Metrics pipeline** — emit conversion/accept events from the UI and correlate with variant assignments | M | Feed into a data warehouse or analytics tool for significance testing |
| 3 | **Admin UI for experiments** — create/stop experiments and view live variant splits | L | Nice-to-have; CLI or API-first is acceptable initially |

## Database & Persistence

| # | Item | Size | Notes |
|---|------|------|-------|
| 4 | **PostgreSQL integration** — persist offer decisions for audit trail and analytics | M | Schema: `decisions(subscriber_id, offer, discount, variant, created_at)` |
| 5 | **Alembic migrations** — add a migration framework so schema changes are versioned | S | Keep migrations in `services/offer-decision-service/migrations/` |
| 6 | **Read-replica support** — route analytics queries to a read replica to avoid load on the primary | S | Useful when query volume grows |

## Feature Flags & Configuration

| # | Item | Size | Notes |
|---|------|------|-------|
| 7 | **Feature flag service** — integrate LaunchDarkly, Unleash, or a lightweight in-house toggle store | M | Wrap policy rules behind flags so they can be enabled per-segment |
| 8 | **Dynamic discount ranges** — make discount percentages configurable via flags or a config file instead of hard-coded in `policy.py` | S | Reduces need for code deploys on business-rule changes |

## Observability Enhancements

| # | Item | Size | Notes |
|---|------|------|-------|
| 9 | **Distributed tracing** — add OpenTelemetry auto-instrumentation and export to a collector | M | Trace request through frontend -> backend -> AI call |
| 10 | **Prometheus metrics** — expose `/metrics` endpoint with request latency histograms and offer-type counters | S | Pair with Grafana dashboards |
| 11 | **Structured JSON logging** — switch to `structlog` or `python-json-logger` with `trace_id` injection | S | Required for production log aggregation |
| 12 | **Alerting rules** — define Prometheus alert rules for error rate spikes and latency p99 breaches | S | Ship as a `PrometheusRule` CRD or Grafana alert |

## Security & Compliance

| # | Item | Size | Notes |
|---|------|------|-------|
| 13 | **Secret rotation** — automate rotation of `OPENAI_API_KEY` and database credentials | M | Use AWS Secrets Manager + external-secrets-operator |
| 14 | **Network policies** — restrict pod-to-pod traffic within the namespace | S | Allow only frontend -> backend and backend -> external (OpenAI) |
| 15 | **SBOM generation** — produce a Software Bill of Materials on every image build | S | Integrate Syft or Trivy into the CI pipeline |

## Performance & Scaling

| # | Item | Size | Notes |
|---|------|------|-------|
| 16 | **Load testing** — create a k6 or Locust test suite targeting `/api/v1/offer` | S | Establish baseline latency and throughput |
| 17 | **HPA tuning** — enable and calibrate Horizontal Pod Autoscaler based on load test results | S | Start with CPU target; consider custom metrics later |
| 18 | **Response caching** — cache deterministic offer decisions (same inputs = same output) with a short TTL | M | Redis sidecar or in-process LRU; skip caching when AI explanation is requested |

## Developer Experience

| # | Item | Size | Notes |
|---|------|------|-------|
| 19 | **Devcontainer / Codespaces config** — one-click cloud dev environment | S | `.devcontainer/devcontainer.json` with Docker Compose |
| 20 | **E2E tests** — Playwright or Cypress tests covering the Input -> Offer -> Result flow | M | Run in CI on every PR |
| 21 | **Makefile improvements** — add `make plan`, `make apply`, `make deploy` targets for Terraform and Helm | S | Reduces onboarding friction |

---

> **How to pick up an item:** Create a GitHub issue referencing the backlog number,
> assign it, and move it to the current sprint / iteration board.
