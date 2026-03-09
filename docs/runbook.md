# Runbook — Subscription Offer App

## Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Backend API | `GET /healthz` | `{"status":"ok"}` (HTTP 200) |
| Frontend | `GET /` | HTML page (HTTP 200) |

### Kubernetes Probes

Both liveness and readiness probes point to `/healthz` on the backend.
A failing liveness probe triggers a pod restart; a failing readiness probe
removes the pod from the Service load balancer.

```bash
# Quick cluster health check
kubectl -n subscription-offer-app get pods
kubectl -n subscription-offer-app logs -l app=offer-decision-service --tail=50
```

---

## Key Configuration Values

| Variable | Location | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | `.env` / K8s Secret | API key for AI explanation enhancement |
| `APP_ENV` | `.env` / ConfigMap | Environment identifier (`local`, `dev`, `prod`) |
| `LOG_LEVEL` | `.env` / ConfigMap | Logging verbosity (`debug`, `info`, `warning`) |
| `NEXT_PUBLIC_API_URL` | `.env` / ConfigMap | Backend URL the frontend calls |
| `DATABASE_URL` | `.env` / K8s Secret | PostgreSQL connection string (future) |

### AWS Resources

| Resource | ARN / URL |
|----------|-----------|
| ECR — backend | `599083837640.dkr.ecr.us-east-1.amazonaws.com/offer-decision-service` |
| ECR — frontend | `599083837640.dkr.ecr.us-east-1.amazonaws.com/demo-ui` |
| IAM CI/CD role | `arn:aws:iam::599083837640:role/subscription-offer-app-cicd` |
| OIDC provider | `arn:aws:iam::599083837640:oidc-provider/token.actions.githubusercontent.com` |

---

## Rollback Procedures

### 1. Helm Rollback (Preferred)

```bash
# List release history
helm -n subscription-offer-app history offer-decision-service

# Roll back to the previous revision
helm -n subscription-offer-app rollback offer-decision-service

# Or roll back to a specific revision
helm -n subscription-offer-app rollback offer-decision-service <REVISION>

# Verify
kubectl -n subscription-offer-app rollout status deployment/offer-decision-service
```

### 2. Image Tag Rollback

If the Helm chart hasn't changed but the image is bad:

```bash
# Find a known-good image tag (commit SHA)
aws ecr describe-images --repository-name offer-decision-service \
  --query 'sort_by(imageDetails,&imagePushedAt)[-5:].imageTags' \
  --region us-east-1

# Redeploy with the good tag
helm -n subscription-offer-app upgrade offer-decision-service helm/offer-decision-service \
  --set image.tag=<GOOD_SHA> --wait
```

### 3. Emergency: Scale to Zero

If the service is causing cascading failures:

```bash
kubectl -n subscription-offer-app scale deployment/offer-decision-service --replicas=0
```

Restore once the fix is ready:

```bash
kubectl -n subscription-offer-app scale deployment/offer-decision-service --replicas=2
```

---

## Troubleshooting

### Pod CrashLoopBackOff

```bash
# Check pod events
kubectl -n subscription-offer-app describe pod <POD_NAME>

# Check recent logs
kubectl -n subscription-offer-app logs <POD_NAME> --previous
```

**Common causes:**
- Missing `OPENAI_API_KEY` → the app starts but AI explanations fail
- Wrong `NEXT_PUBLIC_API_URL` → frontend cannot reach backend
- Port conflict → verify `containerPort` matches Dockerfile `EXPOSE`

### ImagePullBackOff

```bash
# Verify the image exists in ECR
aws ecr describe-images --repository-name offer-decision-service \
  --image-ids imageTag=<TAG> --region us-east-1

# Verify the node can authenticate to ECR
kubectl -n subscription-offer-app describe pod <POD_NAME> | grep -A5 Events
```

**Common causes:**
- Image tag doesn't exist (typo or failed build)
- IRSA role not bound to the service account
- ECR lifecycle policy expired the image

### 502 / 503 from Load Balancer

1. Check readiness probe: `kubectl -n subscription-offer-app get endpoints`
2. Verify the service selector matches pod labels
3. Check backend logs for startup errors

### SonarCloud Quality Gate Failure

The CI pipeline blocks deployment when SonarCloud fails.

```bash
# View the quality gate status
# Go to: https://sonarcloud.io/project/overview?id=mbatchelor81_subscription-offer-app

# Common fixes:
# - Add missing test coverage
# - Fix code smells flagged in the report
# - Address security hotspots
```

### Terraform State Drift

```bash
cd infra/terraform
terraform plan   # Review drift

# If resources were changed outside Terraform, re-import:
terraform import '<RESOURCE_ADDRESS>' '<RESOURCE_ID>'
```

---

## Incident Response Checklist

1. **Assess** — Is the service down or degraded? Check `/healthz`.
2. **Communicate** — Notify the team in Slack.
3. **Mitigate** — Rollback or scale to zero if needed.
4. **Diagnose** — Collect logs, check recent deployments.
5. **Fix** — Apply the fix via a PR through the normal CI/CD pipeline.
6. **Postmortem** — Document root cause and preventive actions.
