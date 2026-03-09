################################################################################
# EKS Bindings – Namespace + IRSA Service Account
#
# This module assumes an existing EKS cluster. Configure kubectl context
# or the Kubernetes provider before using this module.
################################################################################

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.25"
    }
  }
}

################################################################################
# Namespace
################################################################################

resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace

    labels = merge(
      {
        "app.kubernetes.io/managed-by" = "terraform"
        "app.kubernetes.io/part-of"    = var.app_name
      },
      var.namespace_labels,
    )

    annotations = var.namespace_annotations
  }
}

################################################################################
# Service Account with IRSA annotation
################################################################################

resource "kubernetes_service_account" "app" {
  metadata {
    name      = var.service_account_name
    namespace = kubernetes_namespace.app.metadata[0].name

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "app.kubernetes.io/part-of"    = var.app_name
    }

    annotations = {
      "eks.amazonaws.com/role-arn" = var.irsa_role_arn
    }
  }

  automount_service_account_token = true
}
