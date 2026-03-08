# Phase 2: Terraform (ECR + IAM) + Release Documentation

## Objective
Create Terraform modules for AWS infrastructure and comprehensive release documentation.

## Terraform (`infra/terraform/`)

### Module: ECR
- Create ECR repository for `offer-decision-service`
- Lifecycle policy: keep last 10 tagged images, expire untagged after 7 days
- Encryption enabled (AES-256 or KMS)

### Module: IAM
- IAM role for CI/CD pipeline (GitHub Actions OIDC → assume role)
- Policy: push to ECR, read EKS cluster
- IAM role for EKS workload (IRSA) if applicable

### Module: EKS Bindings (optional)
- Assume an existing EKS cluster
- Create namespace for the app
- IRSA service account binding

### Shared
- `variables.tf` with sensible defaults
- `outputs.tf` exposing ARNs, registry URLs
- `backend.tf` stub for S3 state backend
- `providers.tf` pinning AWS provider version

## Acceptance Criteria (Terraform)
- [ ] `terraform fmt -check` passes
- [ ] `terraform validate` passes
- [ ] `terraform plan` produces expected resources (dry run)

## Release Documentation

### README.md Updates
- Architecture diagram (text-based or Mermaid)
- Local dev quickstart (already exists, verify current)
- CI/CD pipeline overview
- How to deploy to EKS

### Runbook (`docs/runbook.md`)
- How to rollback a deployment
- Key configuration values and where they live
- Troubleshooting common issues
- Health check endpoints

### What's Next (`docs/backlog.md`)
- Phase 3 backlog items (A/B testing, database, feature flags, etc.)

## Context
- `infra/terraform/` currently contains only `.gitkeep`
- Target cloud: AWS (ECR + EKS)
- This is part of Phase 2 industrialization
