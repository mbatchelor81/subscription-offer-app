# Subscriber Offer Decisioning

A TMT demo application that personalises retention and upsell offers for
telecom / media subscribers. The offer decision is **policy-driven and
deterministic**; AI is used only to polish the explanation text.

---

## Architecture

```
┌─────────────┐        ┌──────────────────────────┐
│  demo-ui    │  HTTP   │  offer-decision-service   │
│  (Next.js)  │───────▶ │  (FastAPI / Uvicorn)      │
│  :3000      │        │  :8000                     │
└─────────────┘        │                            │
                       │  /healthz ─ liveness probe │
                       │  /api/v1/offer ─ main API  │
                       │  /docs ─ Swagger UI        │
                       └──────────┬─────────────────┘
                                  │ (optional)
                                  ▼
                       ┌──────────────────────┐
                       │  OpenAI API          │
                       │  (explanation only)   │
                       └──────────────────────┘
```

**Production target (AWS):**

```
GitHub Actions (OIDC)
       │
       ▼
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│  ECR         │────▶│  EKS Cluster  │────▶│  Pods            │
│  (container  │     │  (Kubernetes) │     │  - backend       │
│   registry)  │     │               │     │  - frontend      │
└──────────────┘     └───────────────┘     └──────────────────┘
       ▲                                          │
       │            ┌──────────────┐              │ IRSA
       └────────────│  IAM / OIDC  │◀─────────────┘
                    └──────────────┘
```

---

## Project Structure

```
services/offer-decision-service/   FastAPI backend
web/demo-ui/                       Next.js frontend
helm/offer-decision-service/       Helm chart (placeholder)
infra/terraform/                   Terraform modules (ECR, IAM, EKS bindings)
  ├── modules/ecr/                 ECR repository + lifecycle policy
  ├── modules/iam/                 GitHub OIDC, CI/CD role, IRSA role
  └── modules/eks-bindings/        K8s namespace + service account (optional)
.github/workflows/                 CI/CD (placeholder)
docs/
  ├── runbook.md                   Operations runbook
  └── backlog.md                   Phase 3+ backlog
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker & Docker Compose | latest | Local development |
| Python | 3.12+ | Backend (if running outside Docker) |
| Node.js | 20+ | Frontend (if running outside Docker) |
| Terraform | >= 1.5 | Infrastructure provisioning |
| AWS CLI | v2 | AWS resource management |
| kubectl | latest | Kubernetes cluster access |
| Helm | 3.x | Kubernetes deployments |

---

## Local Development Quickstart

```bash
# 1. Clone and enter the repo
git clone https://github.com/mbatchelor81/subscription-offer-app.git
cd subscription-offer-app

# 2. Copy env file and set your OpenAI key
cp .env.example .env
# Edit .env → set OPENAI_API_KEY (optional — app works without it)

# 3. Start all services
make up          # builds and starts backend (:8000) + frontend (:3000)

# 4. Verify
curl http://localhost:8000/healthz   # → {"status": "ok"}
open http://localhost:3000           # → demo UI

# 5. Run tests / lint
make test        # pytest
make lint        # ruff check
make fmt         # ruff format
```

### Running Without Docker

```bash
# Backend
cd services/offer-decision-service
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd web/demo-ui
npm install && npm run dev
```

---

## CI/CD Pipeline Overview

The CI/CD pipeline runs on **GitHub Actions** and has four stages:

| Stage | Trigger | What it Does |
|-------|---------|--------------|
| **1. Lint & Test** | Every PR | `ruff check`, `pytest --cov`, upload `coverage.xml` |
| **2. SonarQube Scan** | Every PR | Analyse code quality, enforce quality gate |
| **3. Build & Push** | Merge to `main` | Docker build → push to ECR (tagged with `${{ github.sha }}`) |
| **4. Deploy** | Merge to `main` | Helm upgrade to EKS cluster |

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | CI/CD IAM role ARN (from `terraform output cicd_role_arn`) |
| `SONAR_TOKEN` | SonarCloud authentication token |

---

## Infrastructure (Terraform)

All infrastructure code lives in `infra/terraform/`.

### Quick Start

```bash
cd infra/terraform

# Initialise providers and modules
terraform init

# Review what will be created
terraform plan

# Apply (creates ECR repo, OIDC provider, IAM roles)
terraform apply
```

### Modules

| Module | Resources | Purpose |
|--------|-----------|---------|
| `modules/ecr` | ECR repository, lifecycle policy | Container image registry with AES-256 encryption. Keeps last 10 tagged images; expires untagged after 7 days. |
| `modules/iam` | OIDC provider, CI/CD role + policy, IRSA role (optional) | GitHub Actions assumes the CI/CD role via OIDC to push images and read EKS. IRSA role lets pods pull from ECR. |
| `modules/eks-bindings` | K8s namespace, service account | Creates the application namespace and an IRSA-annotated service account. Requires a configured Kubernetes provider. |

### Key Outputs

```bash
terraform output ecr_repository_url   # → 123456789012.dkr.ecr.us-east-1.amazonaws.com/offer-decision-service
terraform output cicd_role_arn         # → arn:aws:iam::123456789012:role/subscription-offer-app-cicd
terraform output irsa_role_arn         # → (empty unless create_irsa_role = true)
```

### Remote State (Optional)

Edit `backend.tf` to enable S3 + DynamoDB state locking, then run
`terraform init -reconfigure`.

---

## Deploying to EKS

### 1. Provision Infrastructure

```bash
cd infra/terraform
terraform apply                       # creates ECR, IAM roles
```

### 2. Build & Push the Docker Image

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(terraform output -raw ecr_repository_url | cut -d/ -f1)

# Build and tag
docker build -t offer-decision-service:latest \
  services/offer-decision-service/

docker tag offer-decision-service:latest \
  $(terraform output -raw ecr_repository_url):latest

# Push
docker push $(terraform output -raw ecr_repository_url):latest
```

### 3. Deploy with Helm

```bash
helm upgrade --install offer-decision-service \
  helm/offer-decision-service/ \
  --namespace offer-decision \
  --create-namespace \
  --set image.repository=$(terraform output -raw ecr_repository_url) \
  --set image.tag=latest \
  --set env.OPENAI_API_KEY=<your-key>
```

### 4. Verify

```bash
kubectl -n offer-decision get pods
kubectl -n offer-decision port-forward svc/offer-decision-service 8000:8000
curl http://localhost:8000/healthz
```

> For rollback, troubleshooting, and configuration details see
> [docs/runbook.md](docs/runbook.md).

---

## Health Check

```bash
curl http://localhost:8000/healthz
# → {"status": "ok"}
```

---

## Further Reading

- [Operations Runbook](docs/runbook.md) — rollback, troubleshooting, config reference
- [Phase 3 Backlog](docs/backlog.md) — upcoming features (A/B testing, database, feature flags, etc.)
- [Product Requirements](BASIC_PRD.md) — business context and acceptance criteria
