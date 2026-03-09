# Runbook — Offer Decision Service

## Table of Contents

- [Health Check Endpoints](#health-check-endpoints)
- [Key Configuration Values](#key-configuration-values)
- [How to Roll Back a Deployment](#how-to-roll-back-a-deployment)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Health Check Endpoints

| Endpoint | Method | Expected Response | Purpose |
|----------|--------|-------------------|---------|
| `/healthz` | `GET` | `{"status": "ok"}` (HTTP 200) | Liveness & readiness probe |
| `/docs` | `GET` | Swagger UI (HTTP 200) | API documentation |

**Quick check (local):**

```bash
curl -s http://localhost:8000/healthz | jq .
```

**Quick check (Kubernetes):**

```bash
kubectl -n offer-decision exec deploy/offer-decision-service -- \
  curl -s http://localhost:8000/healthz
```

---

## Key Configuration Values

### Environment Variables

| Variable | Where Set | Description |
|----------|-----------|-------------|
| `APP_ENV` | `.env` / ConfigMap | Environment identifier (`local`, `dev`, `staging`, `prod`) |
| `LOG_LEVEL` | `.env` / ConfigMap | Logging verbosity (`debug`, `info`, `warning`, `error`) |
| `OPENAI_API_KEY` | `.env` / K8s Secret | OpenAI API key for AI-enhanced explanations |
| `NEXT_PUBLIC_API_URL` | `.env` / ConfigMap | Backend URL the frontend calls |
| `DATABASE_URL` | `.env` / K8s Secret | PostgreSQL connection string (optional) |

### Infrastructure Values (Terraform)

| Value | Location | Description |
|-------|----------|-------------|
| ECR Repository URL | `terraform output ecr_repository_url` | Docker image registry endpoint |
| CI/CD Role ARN | `terraform output cicd_role_arn` | GitHub Actions assume-role ARN |
| IRSA Role ARN | `terraform output irsa_role_arn` | EKS workload IAM role ARN |

### Helm Values

Key overrides live in `helm/offer-decision-service/values.yaml`:

- `image.repository` — ECR repository URL
- `image.tag` — Git SHA or semver tag
- `replicaCount` — Number of pod replicas
- `resources.requests/limits` — CPU/memory resource bounds
- `env.*` — Runtime environment variables

---

## How to Roll Back a Deployment

### Option 1: Helm Rollback (Preferred)

```bash
# List recent releases
helm -n offer-decision history offer-decision-service

# Roll back to the previous revision
helm -n offer-decision rollback offer-decision-service

# Roll back to a specific revision
helm -n offer-decision rollback offer-decision-service <REVISION_NUMBER>
```

### Option 2: Revert the Git Commit

```bash
# Identify the bad commit
git log --oneline -5

# Create a revert commit
git revert <COMMIT_SHA>
git push origin main
```

This triggers the CI/CD pipeline, which builds and deploys the reverted image.

### Option 3: Force a Known-Good Image

```bash
# Update the deployment image directly (emergency only)
kubectl -n offer-decision set image \
  deployment/offer-decision-service \
  offer-decision-service=<ECR_URL>:<KNOWN_GOOD_TAG>
```

> **Note:** Manual image overrides will be replaced on the next Helm deploy.

---

## Troubleshooting Common Issues

### 1. Backend Returns 500 Errors

**Symptoms:** API calls to `/api/v1/offer` return HTTP 500.

**Steps:**
1. Check application logs:
   ```bash
   kubectl -n offer-decision logs deploy/offer-decision-service --tail=100
   ```
2. Look for Python tracebacks — common causes:
   - Missing or invalid `OPENAI_API_KEY` (AI explanation fails gracefully, but check logs)
   - Invalid request payload (Pydantic validation error)
3. Verify the health endpoint still responds:
   ```bash
   kubectl -n offer-decision exec deploy/offer-decision-service -- \
     curl -s http://localhost:8000/healthz
   ```

### 2. Pods Stuck in CrashLoopBackOff

**Steps:**
1. Describe the pod for events:
   ```bash
   kubectl -n offer-decision describe pod -l app=offer-decision-service
   ```
2. Check previous container logs:
   ```bash
   kubectl -n offer-decision logs deploy/offer-decision-service --previous
   ```
3. Common causes:
   - Port conflict (another process on 8000)
   - Missing environment variable causing startup crash
   - OOMKilled — increase `resources.limits.memory` in Helm values

### 3. Image Pull Errors (ErrImagePull / ImagePullBackOff)

**Steps:**
1. Verify the image exists in ECR:
   ```bash
   aws ecr describe-images \
     --repository-name offer-decision-service \
     --query 'imageDetails[*].imageTags' --output table
   ```
2. Verify IRSA is correctly configured — the service account must have `ecr:BatchGetImage` permission.
3. Check that the ECR repository is in the same region as the EKS cluster.

### 4. Frontend Cannot Reach Backend

**Symptoms:** UI shows network errors or blank offer results.

**Steps:**
1. Verify `NEXT_PUBLIC_API_URL` is set correctly in the frontend pod/ConfigMap.
2. Check that the backend Kubernetes Service is reachable:
   ```bash
   kubectl -n offer-decision get svc
   ```
3. Test connectivity from the frontend pod:
   ```bash
   kubectl -n offer-decision exec deploy/demo-ui -- \
     curl -s http://offer-decision-service:8000/healthz
   ```

### 5. CI/CD Pipeline Fails to Push Image

**Steps:**
1. Verify the GitHub Actions OIDC trust relationship:
   ```bash
   aws iam get-role --role-name subscription-offer-app-cicd \
     --query 'Role.AssumeRolePolicyDocument'
   ```
2. Confirm the repository name matches the OIDC `sub` condition.
3. Check ECR permissions on the CI/CD role:
   ```bash
   aws iam list-role-policies --role-name subscription-offer-app-cicd
   ```

### 6. Terraform State Lock / Conflict

**Steps:**
1. If using DynamoDB locking, check the lock table:
   ```bash
   aws dynamodb scan --table-name subscription-offer-app-tflock
   ```
2. Force-unlock if you're certain no other process is running:
   ```bash
   terraform force-unlock <LOCK_ID>
   ```
