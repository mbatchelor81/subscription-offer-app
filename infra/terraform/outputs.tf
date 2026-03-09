################################################################################
# Root Outputs
################################################################################

# ── ECR ──────────────────────────────────────────────────────────────────────

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = module.ecr.repository_arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository (use for docker push)"
  value       = module.ecr.repository_url
}

output "ecr_registry_id" {
  description = "The ECR registry ID"
  value       = module.ecr.registry_id
}

# ── IAM ──────────────────────────────────────────────────────────────────────

output "cicd_role_arn" {
  description = "ARN of the GitHub Actions CI/CD role"
  value       = module.iam.cicd_role_arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = module.iam.oidc_provider_arn
}

output "irsa_role_arn" {
  description = "ARN of the IRSA role (empty if not created)"
  value       = module.iam.irsa_role_arn
}
