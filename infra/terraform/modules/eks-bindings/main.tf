# ------------------------------------------------------------
# EKS Bindings (optional)
# ------------------------------------------------------------
# This module assumes an existing EKS cluster and creates an
# IRSA IAM role that Kubernetes workloads can assume.
#
# Enable by setting var.eks_cluster_name to a non-empty value
# in the root module.  When disabled (default), no resources
# are created.
#
# Namespace and service-account creation are handled by the
# Helm chart (helm/offer-decision-service) at deploy time.
# ------------------------------------------------------------

data "aws_caller_identity" "current" {}

data "aws_eks_cluster" "this" {
  count = var.enabled ? 1 : 0
  name  = var.eks_cluster_name
}

# ------------------------------------------------------------
# IRSA — IAM Role for Service Account
# ------------------------------------------------------------

resource "aws_iam_role" "workload" {
  count = var.enabled ? 1 : 0
  name  = "${var.project_name}-workload"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.this[0].identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(data.aws_eks_cluster.this[0].identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:${var.namespace}:${var.project_name}"
          }
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-workload"
  }
}
