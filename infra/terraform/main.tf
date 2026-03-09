################################################################################
# Root Module – wires together ECR, IAM, and (optionally) EKS bindings
################################################################################

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── ECR ──────────────────────────────────────────────────────────────────────

module "ecr" {
  source = "./modules/ecr"

  repository_name = var.ecr_repository_name
  encryption_type = var.ecr_encryption_type
  tags            = local.common_tags
}

# ── IAM ──────────────────────────────────────────────────────────────────────

module "iam" {
  source = "./modules/iam"

  project_name              = var.project_name
  create_oidc_provider      = var.create_oidc_provider
  existing_oidc_provider_arn = var.existing_oidc_provider_arn
  github_repositories       = var.github_repositories
  ecr_repository_arns  = [module.ecr.repository_arn]
  eks_cluster_arns     = var.eks_cluster_arns

  # IRSA (disabled by default – enable when EKS cluster exists)
  create_irsa_role      = var.create_irsa_role
  eks_oidc_provider_arn = var.eks_oidc_provider_arn
  eks_oidc_provider_url = var.eks_oidc_provider_url
  k8s_namespace         = var.k8s_namespace

  tags = local.common_tags
}

# ── EKS Bindings (optional) ─────────────────────────────────────────────────
# Uncomment when a Kubernetes provider is configured and an EKS cluster exists.
#
# module "eks_bindings" {
#   source = "./modules/eks-bindings"
#
#   namespace            = var.k8s_namespace
#   irsa_role_arn        = module.iam.irsa_role_arn
#   service_account_name = "offer-decision-service"
# }
