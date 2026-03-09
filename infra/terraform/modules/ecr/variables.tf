variable "repository_name" {
  description = "Name of the ECR repository"
  type        = string
}

variable "image_tag_mutability" {
  description = "Tag mutability setting (MUTABLE or IMMUTABLE)"
  type        = string
  default     = "MUTABLE"
}

variable "force_delete" {
  description = "Whether to delete the repository even if it contains images"
  type        = bool
  default     = false
}

variable "encryption_type" {
  description = "Encryption type for the repository (AES256 or KMS)"
  type        = string
  default     = "AES256"
}

variable "kms_key_arn" {
  description = "ARN of the KMS key for encryption (only used when encryption_type = KMS)"
  type        = string
  default     = null
}

variable "scan_on_push" {
  description = "Whether images are scanned on push"
  type        = bool
  default     = true
}

variable "untagged_expiry_days" {
  description = "Number of days after which untagged images expire"
  type        = number
  default     = 7
}

variable "max_tagged_image_count" {
  description = "Maximum number of tagged images to retain"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags to apply to ECR resources"
  type        = map(string)
  default     = {}
}
