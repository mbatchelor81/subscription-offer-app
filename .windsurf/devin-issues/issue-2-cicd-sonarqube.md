# Phase 2: CI/CD Pipeline + SonarQube Quality Gate

## Objective
Create a GitHub Actions CI/CD pipeline with lint, test, build, SonarQube scan, and deploy stages.

## Workflow: `.github/workflows/ci.yml`

### Triggers
- **Pull requests** → all branches
- **Push** → `main` only

### Jobs

#### 1. Lint & Test
- Install Python 3.12 deps (including `.[dev]`)
- Run `ruff check app/ tests/`
- Run `pytest --cov=app --cov-report=xml:coverage.xml tests/`
- Upload `coverage.xml` as artifact

#### 2. SonarQube Scan
- Use the official SonarQube/SonarCloud GitHub Action
- Config file: `sonar-project.properties` (already in repo root with placeholders — fill in the project key)
- Ingest `coverage.xml`
- **Quality gate must pass** — fail the PR if it doesn't
- Required secrets: `SONAR_TOKEN`, `SONAR_HOST_URL`

#### 3. Build & Push Image (main only)
- Build Docker image using the hardened Dockerfile
- Tag: `$ECR_REGISTRY/offer-decision-service:${{ github.sha }}`
- Push to AWS ECR
- Required secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECR_REGISTRY`

#### 4. Deploy (main only, after build)
- `helm upgrade --install` to EKS namespace
- Use image tag from build step
- Required: kubeconfig or IRSA-based auth

## Acceptance Criteria
- [ ] Workflow runs on PR and push to main
- [ ] Lint + test jobs pass (or fail clearly on errors)
- [ ] SonarQube quality gate is enforced on PRs
- [ ] Image push is gated to `main` only
- [ ] Deploy step is gated to `main` only
- [ ] All required secrets are documented in the PR description
- [ ] PR includes instructions for setting up the GitHub secrets

## Context
- `pytest-cov` has been added to `pyproject.toml`
- `sonar-project.properties` exists in repo root with placeholder values
- This is part of Phase 2 industrialization
