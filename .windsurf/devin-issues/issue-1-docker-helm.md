# Phase 2: Docker Hardening + Helm Chart

## Objective
Harden the existing Dockerfiles for production and create a Helm chart for Kubernetes deployment.

## Docker Hardening (both services)

### Backend (`services/offer-decision-service/Dockerfile`)
- Convert to **multi-stage build** (build stage → slim prod stage)
- Run as **non-root user**
- Remove `--reload` from the production CMD
- Add `HEALTHCHECK` instruction pointing to `/healthz`
- Minimize image size (use `python:3.12-slim`, clean up pip cache)
- Document runtime env vars in Dockerfile comments

### Frontend (`web/demo-ui/Dockerfile`)
- Convert to **multi-stage build** (deps → build → serve with nginx or node)
- Run as **non-root user**
- Minimize image size

### `.dockerignore`
- Verify both `.dockerignore` files exclude tests, docs, `.git`, `__pycache__`, etc.

## Helm Chart (`helm/offer-decision-service/`)
- Create standard chart structure: `Chart.yaml`, `values.yaml`, `templates/`
- Templates: **Deployment**, **Service**, **ConfigMap** (for env vars), **Secret** (reference)
- **Liveness probe** → `GET /healthz`
- **Readiness probe** → `GET /healthz`
- Resource requests/limits (sensible defaults in `values.yaml`)
- HPA stub (disabled by default, configurable via values)
- Values for all env var configuration (API keys via Secret refs)

## Acceptance Criteria
- [ ] `docker build` succeeds for both services
- [ ] Container runs without root user at runtime (`docker run ... whoami` → non-root)
- [ ] `helm template ./helm/offer-decision-service` renders valid YAML
- [ ] `helm lint ./helm/offer-decision-service` passes
- [ ] PR includes a summary of image size before/after

## Context
- Current Dockerfiles are dev-only (single stage, root, `--reload`)
- `AGENTS.md` describes the project conventions
- This is part of Phase 2 industrialization — see `BASIC_PRD.md` for background
