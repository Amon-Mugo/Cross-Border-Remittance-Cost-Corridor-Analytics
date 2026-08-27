
# Defines the GitHub Actions OIDC trust relationship and a read-only IAM role
# used exclusively by the `terraform-plan` CI job to run init/fmt/validate/plan.

variable "github_repo" {
  description = "GitHub repo in OWNER/REPO form, used to scope the OIDC trust policy"
  type        = string
  default     = "Amon-Mugo/Cross-Border-Remittance-Cost-Corridor-Analytics"
}

variable "terraform_state_bucket" {
  description = "S3 bucket holding the terraform remote state"
  type        = string
  default     = "remittance-corridor-tfstate-011294328070"
}

variable "terraform_locks_table_name" {
  description = "Existing DynamoDB table used for terraform state locking"
  type        = string
  default     = "remittance-corridor-terraform-locks-011294328070"
}

# Reference to the DynamoDB locks table that already exists created outside

data "aws_dynamodb_table" "terraform_locks" {
  name = var.terraform_locks_table_name
}

# GitHub's OIDC TLS certificate thumbprint, fetched dynamically so it never
# goes stale if GitHub rotates their cert chain.
data "tls_certificate" "github_actions" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github_actions.certificates[0].sha1_fingerprint]

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
    Purpose   = "github-actions-oidc-provider"
  }
}

# Trust policy: only this repo's `main` branch pushes and pull requests may
# assume the role. aud = audience (always sts.amazonaws.com); sub = identity
# (repo/branch/PR claim).
data "aws_iam_policy_document" "ci_plan_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repo}:ref:refs/heads/main",
        "repo:${var.github_repo}:pull_request"
      ]
    }
  }
}

resource "aws_iam_role" "ci_plan_role" {
  name                 = "remittance-corridor-ci-plan-role"
  assume_role_policy   = data.aws_iam_policy_document.ci_plan_trust.json
  max_session_duration = 3600

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
    Purpose   = "ci-terraform-plan-readonly-role"
  }
}

# Read-only permissions: S3 state read + DynamoDB lock read/write/delete.
# No apply/write access to any project infra resources.
data "aws_iam_policy_document" "ci_plan_permissions" {
  statement {
    sid    = "AllowStateRead"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.terraform_state_bucket}",
      "arn:aws:s3:::${var.terraform_state_bucket}/*",
    ]
  }

  statement {
    sid    = "AllowStateLock"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
    ]
    resources = [
      data.aws_dynamodb_table.terraform_locks.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ci_plan_permissions" {
  name   = "ci-plan-readonly-permissions"
  role   = aws_iam_role.ci_plan_role.id
  policy = data.aws_iam_policy_document.ci_plan_permissions.json
}

output "ci_plan_role_arn" {
  description = "ARN to set as the AWS_CI_PLAN_ROLE_ARN GitHub Actions secret"
  value       = aws_iam_role.ci_plan_role.arn
}