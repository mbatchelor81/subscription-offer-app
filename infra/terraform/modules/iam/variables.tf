variable "project_name" {
  description = "Project name used as a prefix for IAM resources"
  type        = string
}

# ── GitHub Actions OIDC ──────────────────────────────────────────────────────

variable "create_oidc_provider" {
  description = "Whether to create the GitHub OIDC provider (set to false if it already exists in the account)"
  type        = bool
  default     = true
}

variable "existing_oidc_provider_arn" {
  description = "ARN of an existing GitHub OIDC provider (used when create_oidc_provider = false)"
  type        = string
  default     = ""
}

variable "github_oidc_thumbprint" {
  description = "Thumbprint for the GitHub OIDC provider"
  type        = string
  default     = "6938fd4d98bab03faadb97b34396831e3780aea1"
}

variable "github_repositories" {
  description = "List of GitHub repositories allowed to assume the CI/CD role (format: owner/repo)"
  type        = list(string)
}

# ── CI/CD Policy Targets ─────────────────────────────────────────────────────

variable "ecr_repository_arns" {
  description = "List of ECR repository ARNs the CI/CD role can push to"
  type        = list(string)
}

variable "eks_cluster_arns" {
  description = "List of EKS cluster ARNs the CI/CD role can read"
  type        = list(string)
  default     = ["*"]
}

# ── IRSA ─────────────────────────────────────────────────────────────────────

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
  description = "Kubernetes namespace where the service account lives"
  type        = string
  default     = "offer-decision"
}

variable "k8s_service_account_name" {
  description = "Kubernetes service account name for IRSA binding"
  type        = string
  default     = "offer-decision-service"
}

# ── Common ───────────────────────────────────────────────────────────────────

variable "tags" {
  description = "Tags to apply to IAM resources"
  type        = map(string)
  default     = {}
}
