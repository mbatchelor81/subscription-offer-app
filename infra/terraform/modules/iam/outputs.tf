output "cicd_role_arn" {
  description = "ARN of the CI/CD IAM role for GitHub Actions"
  value       = aws_iam_role.cicd.arn
}

output "cicd_role_name" {
  description = "Name of the CI/CD IAM role"
  value       = aws_iam_role.cicd.name
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = local.oidc_provider_arn
}

output "irsa_role_arn" {
  description = "ARN of the IRSA role (empty string if not created)"
  value       = var.create_irsa_role ? aws_iam_role.irsa[0].arn : ""
}

output "irsa_role_name" {
  description = "Name of the IRSA role (empty string if not created)"
  value       = var.create_irsa_role ? aws_iam_role.irsa[0].name : ""
}
