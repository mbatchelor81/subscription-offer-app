# ------------------------------------------------------------
# Outputs
# ------------------------------------------------------------

output "ecr_repository_urls" {
  description = "Map of ECR repository names to their URLs"
  value       = module.ecr.repository_urls
}

output "ecr_repository_arns" {
  description = "Map of ECR repository names to their ARNs"
  value       = module.ecr.repository_arns
}

output "cicd_role_arn" {
  description = "ARN of the CI/CD IAM role for GitHub Actions"
  value       = module.iam.cicd_role_arn
}

output "cicd_role_name" {
  description = "Name of the CI/CD IAM role"
  value       = module.iam.cicd_role_name
}
