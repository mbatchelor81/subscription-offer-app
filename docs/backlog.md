# Backlog — Phase 3+ Features

Items below are planned enhancements beyond the current Phase 2 milestone.
Priority is indicative; re-evaluate during sprint planning.

---

## High Priority

### A/B Testing Framework
- Implement experiment assignment (subscriber → variant) in the policy engine
- Track conversion metrics per variant
- Admin UI to create/view/stop experiments
- Statistical significance calculator

### Database Integration
- Add PostgreSQL for persisting offer decisions and subscriber history
- Alembic migrations for schema management
- Connection pooling via `asyncpg`
- Add `DATABASE_URL` to Helm secrets

### Feature Flags
- Integrate a feature flag service (e.g., LaunchDarkly, Unleash, or a simple
  config-map-based toggle)
- Gate new offer strategies behind flags
- Support gradual rollout percentages

---

## Medium Priority

### Enhanced Observability
- Grafana dashboards for key business metrics (offers served, discount
  distribution, churn-risk breakdown)
- Alerting rules in Prometheus/Alertmanager for error rate spikes
- Distributed tracing with Jaeger or AWS X-Ray

### Multi-Environment Promotion
- Separate Terraform workspaces or accounts for `dev`, `staging`, `prod`
- Promotion pipeline: dev → staging (auto) → prod (manual approval)
- Environment-specific Helm value overrides

### Caching Layer
- Redis or ElastiCache for caching offer decisions per subscriber
- Cache invalidation strategy on policy changes
- Measure latency improvement

---

## Lower Priority

### Authentication & Authorization
- OAuth 2.0 / OIDC login for the demo UI
- RBAC: viewer vs. admin roles
- API key management for programmatic access

### Batch Offer Generation
- CSV upload of subscriber attributes → bulk offer decisions
- Async job queue (Celery / SQS) for large batches
- Downloadable results report

### Audit Log
- Immutable log of every offer decision with timestamp, inputs, and outputs
- Queryable via API for compliance reporting
- Retention policy aligned with data governance requirements

### Advanced AI Explanations
- Multi-language explanation support
- Tone adjustment (formal / casual) per brand
- Explanation A/B testing (AI wording variants)

### Cost Optimization
- Spot / Fargate for non-critical workloads
- Right-size EKS node groups based on usage data
- ECR image cleanup automation beyond current lifecycle policy

---

## Tech Debt

- [ ] Replace `.gitkeep` placeholders in `helm/` with full chart templates
- [ ] Add integration / end-to-end tests (e.g., Playwright for the frontend)
- [ ] Pin all Python and Node dependency versions for reproducible builds
- [ ] Set up Dependabot or Renovate for automated dependency updates
- [ ] Add pre-commit hooks (ruff, terraform fmt, hadolint)
