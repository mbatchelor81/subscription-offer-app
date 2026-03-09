################################################################################
# Global / Shared Variables
################################################################################

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used as a prefix for resource naming"
  type        = string
  default     = "subscription-offer-app"
}

################################################################################
# ECR
################################################################################

variable "ecr_repository_name" {
  description = "Name of the ECR repository for the offer-decision-service"
  type        = string
  default     = "offer-decision-service"
}

variable "ecr_encryption_type" {
  description = "Encryption type for ECR (AES256 or KMS)"
  type        = string
  default     = "AES256"
}

################################################################################
# IAM / OIDC
################################################################################

variable "create_oidc_provider" {
  description = "Whether to create the GitHub Actions OIDC provider"
  type        = bool
  default     = true
}

variable "github_repositories" {
  description = "GitHub repos allowed to assume the CI/CD role (owner/repo format)"
  type        = list(string)
  default     = ["mbatchelor81/subscription-offer-app"]
}

################################################################################
# EKS (optional – only needed when deploying to an existing cluster)
################################################################################

variable "eks_cluster_arns" {
  description = "ARNs of EKS clusters the CI/CD role can describe"
  type        = list(string)
  default     = ["*"]
}

variable "create_irsa_role" {
  description = "Whether to create an IRSA role for EKS workloads"
  type        = bool
  default     = false
}

variable "eks_oidc_provider_arn" {
  description = "ARN of the EKS OIDC provider (required when create_irsa_role = true)"
  type        = string
  default     = ""
}

variable "eks_oidc_provider_url" {
  description = "URL of the EKS OIDC provider (required when create_irsa_role = true)"
  type        = string
  default     = ""
}

variable "k8s_namespace" {
  description = "Kubernetes namespace for the application"
  type        = string
  default     = "offer-decision"
}
