# Provider requirements for this module.
# Kubernetes namespace and service account creation should be
# handled via Helm or kubectl once the cluster is available.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
