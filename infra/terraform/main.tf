# ------------------------------------------------------------
# Root Module — Subscription Offer App Infrastructure
# ------------------------------------------------------------

module "ecr" {
  source = "./modules/ecr"

  repository_names     = var.ecr_repo_names
  image_tag_mutability = var.ecr_image_tag_mutability
  scan_on_push         = var.ecr_scan_on_push
  max_tagged_images    = var.ecr_max_tagged_images
  untagged_expiry_days = var.ecr_untagged_expiry_days
}

module "iam" {
  source = "./modules/iam"

  project_name   = var.project_name
  aws_region     = var.aws_region
  github_org     = var.github_org
  github_repo    = var.github_repo
  ecr_repo_names = var.ecr_repo_names
}

# ------------------------------------------------------------
# EKS Bindings (optional — disabled by default)
# ------------------------------------------------------------
# Enable by setting eks_cluster_name to the name of your
# existing EKS cluster.  When disabled, no Kubernetes
# resources are created and the kubernetes provider is not
# required.
# ------------------------------------------------------------

module "eks_bindings" {
  source = "./modules/eks-bindings"

  enabled          = var.eks_cluster_name != ""
  eks_cluster_name = var.eks_cluster_name
  namespace        = var.eks_namespace
  project_name     = var.project_name
}
