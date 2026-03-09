################################################################################
# Data Sources
################################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

################################################################################
# GitHub Actions OIDC Provider
################################################################################

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [var.github_oidc_thumbprint]

  tags = var.tags
}

locals {
  oidc_provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : var.existing_oidc_provider_arn
  account_id        = data.aws_caller_identity.current.account_id
  region            = data.aws_region.current.name
}

################################################################################
# CI/CD Role – assumed by GitHub Actions via OIDC
################################################################################

data "aws_iam_policy_document" "cicd_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [for repo in var.github_repositories : "repo:${repo}:*"]
    }
  }
}

resource "aws_iam_role" "cicd" {
  name               = "${var.project_name}-cicd"
  assume_role_policy = data.aws_iam_policy_document.cicd_assume_role.json

  tags = var.tags
}

################################################################################
# CI/CD Policy – push to ECR + read EKS cluster
################################################################################

data "aws_iam_policy_document" "cicd_permissions" {
  # ECR auth + push
  statement {
    sid    = "ECRAuth"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ECRPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
    ]
    resources = var.ecr_repository_arns
  }

  # EKS read access
  statement {
    sid    = "EKSRead"
    effect = "Allow"
    actions = [
      "eks:DescribeCluster",
      "eks:ListClusters",
    ]
    resources = var.eks_cluster_arns
  }
}

resource "aws_iam_role_policy" "cicd" {
  name   = "${var.project_name}-cicd-policy"
  role   = aws_iam_role.cicd.id
  policy = data.aws_iam_policy_document.cicd_permissions.json
}

################################################################################
# IRSA Role – assumed by Kubernetes service accounts in EKS
################################################################################

data "aws_iam_policy_document" "irsa_assume_role" {
  count = var.create_irsa_role ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.eks_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.eks_oidc_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.k8s_namespace}:${var.k8s_service_account_name}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.eks_oidc_provider_url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "irsa" {
  count = var.create_irsa_role ? 1 : 0

  name               = "${var.project_name}-irsa"
  assume_role_policy = data.aws_iam_policy_document.irsa_assume_role[0].json

  tags = var.tags
}

# Attach a minimal policy – teams can extend as needed
data "aws_iam_policy_document" "irsa_permissions" {
  count = var.create_irsa_role ? 1 : 0

  statement {
    sid    = "ECRPull"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "irsa" {
  count = var.create_irsa_role ? 1 : 0

  name   = "${var.project_name}-irsa-policy"
  role   = aws_iam_role.irsa[0].id
  policy = data.aws_iam_policy_document.irsa_permissions[0].json
}
