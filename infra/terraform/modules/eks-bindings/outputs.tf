output "workload_role_arn" {
  description = "ARN of the IRSA workload IAM role"
  value       = var.enabled ? aws_iam_role.workload[0].arn : ""
}
