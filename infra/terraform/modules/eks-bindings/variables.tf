variable "enabled" {
  description = "Whether to create EKS binding resources"
  type        = bool
  default     = false
}

variable "eks_cluster_name" {
  description = "Name of the existing EKS cluster"
  type        = string
  default     = ""
}

variable "namespace" {
  description = "Kubernetes namespace for the application"
  type        = string
  default     = "subscription-offer-app"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}
