variable "namespace" {
  description = "Kubernetes namespace to create for the application"
  type        = string
  default     = "offer-decision"
}

variable "app_name" {
  description = "Application name used in Kubernetes labels"
  type        = string
  default     = "offer-decision-service"
}

variable "service_account_name" {
  description = "Name of the Kubernetes service account"
  type        = string
  default     = "offer-decision-service"
}

variable "irsa_role_arn" {
  description = "ARN of the IAM role to associate with the service account (IRSA)"
  type        = string
}

variable "namespace_labels" {
  description = "Additional labels for the namespace"
  type        = map(string)
  default     = {}
}

variable "namespace_annotations" {
  description = "Annotations for the namespace"
  type        = map(string)
  default     = {}
}
