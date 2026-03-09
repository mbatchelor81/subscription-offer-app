# ------------------------------------------------------------
# Global Variables
# ------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "subscription-offer-app"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "github_org" {
  description = "GitHub organisation or user that owns the repository"
  type        = string
  default     = "mbatchelor81"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "subscription-offer-app"
}

variable "ecr_repo_names" {
  description = "List of ECR repository names to create"
  type        = list(string)
  default     = ["offer-decision-service", "demo-ui"]
}

variable "ecr_image_tag_mutability" {
  description = "Tag mutability setting for ECR repos (MUTABLE or IMMUTABLE)"
  type        = string
  default     = "MUTABLE"
}

variable "ecr_scan_on_push" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

variable "ecr_max_tagged_images" {
  description = "Maximum number of tagged images to retain"
  type        = number
  default     = 10
}

variable "ecr_untagged_expiry_days" {
  description = "Days after which untagged images expire"
  type        = number
  default     = 7
}

variable "eks_cluster_name" {
  description = "Name of the existing EKS cluster (leave empty to skip EKS bindings)"
  type        = string
  default     = ""
}

variable "eks_namespace" {
  description = "Kubernetes namespace for the application workloads"
  type        = string
  default     = "subscription-offer-app"
}
