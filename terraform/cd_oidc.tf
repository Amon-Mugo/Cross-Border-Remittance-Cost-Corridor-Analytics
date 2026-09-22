# Defines the CD-side IAM role assumed by GitHub Actions to run `terraform
# apply`, push images to ECR, and update the EMR Serverless application.
# Reuses the OIDC provider already created in ci_oidc.tf — does not redeclare it.

variable "emr_application_id" {
  description = "EMR Serverless application ID this project deploys to"
  type        = string
}

# Trust policy: only this repository's main branch or its production
# Environment can assume the CD role.
data "aws_iam_policy_document" "cd_trust" {
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
        "repo:Amon-Mugo@205969589/Cross-Border-Remittance-Cost-Corridor-Analytics@1343621611:ref:refs/heads/main",
        "repo:Amon-Mugo@205969589/Cross-Border-Remittance-Cost-Corridor-Analytics@1343621611:environment:production",
      ]
    }
  }
}

resource "aws_iam_role" "cd_role" {
  name                 = "remittance-corridor-cd-deploy-role"
  assume_role_policy   = data.aws_iam_policy_document.cd_trust.json
  max_session_duration = 3600

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
    Purpose   = "cd-deploy-and-apply-role"
  }
}

data "aws_iam_policy_document" "cd_permissions" {
  # Terraform state: same read + write access CI's plan role has for read,
  # plus PutObject/DeleteObject since apply actually writes state back.
  statement {
    sid    = "TerraformStateReadWrite"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.terraform_state_bucket}",
      "arn:aws:s3:::${var.terraform_state_bucket}/*",
    ]
  }

  # Terraform state lock — identical to CI's plan role.
  statement {
    sid    = "TerraformStateLock"
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

  # Data buckets: Terraform manages the bucket resources themselves
  # (versioning/policy/tagging/public-access-block), not their objects.
  statement {
    sid    = "DataBucketManagement"
    effect = "Allow"
    actions = [
      "s3:GetBucketPolicy",
      "s3:PutBucketPolicy",
      "s3:GetBucketVersioning",
      "s3:PutBucketVersioning",
      "s3:GetBucketTagging",
      "s3:PutBucketTagging",
      "s3:GetEncryptionConfiguration",
      "s3:PutEncryptionConfiguration",
      "s3:GetBucketPublicAccessBlock",
      "s3:PutBucketPublicAccessBlock",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.raw_bucket_name}",
      "arn:aws:s3:::${var.raw_bucket_name}/*",
      "arn:aws:s3:::${var.curated_bucket_name}",
      "arn:aws:s3:::${var.curated_bucket_name}/*",
    ]
  }

  # ECR: push the built image plus manage the repository resource itself
  statement {
    sid    = "ECRPushAndManage"
    effect = "Allow"
    actions = [
      # Repository lifecycle (matches ecr.tf's aws_ecr_repository)
      "ecr:CreateRepository",
      "ecr:DeleteRepository",
      "ecr:DescribeRepositories",
      "ecr:PutImageTagMutability",
      "ecr:PutImageScanningConfiguration",
      "ecr:TagResource",
      "ecr:UntagResource",
      # Lifecycle policy (matches aws_ecr_lifecycle_policy)
      "ecr:PutLifecyclePolicy",
      "ecr:GetLifecyclePolicy",
      "ecr:DeleteLifecyclePolicy",
      # Repository policy (matches aws_ecr_repository_policy)
      "ecr:SetRepositoryPolicy",
      "ecr:GetRepositoryPolicy",
      "ecr:DeleteRepositoryPolicy",
      # Image push (the actual CD deploy step, not managed by Terraform)
      "ecr:BatchCheckLayerAvailability",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:DescribeImages",
    ]
    resources = [
      "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${var.ecr_repository_name}",
    ]
  }

  statement {
    sid       = "ECRGetAuthToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # EMR Serverless: update the application to point at the new image and
  # manage the application resource, scoped to this project's app only.
  statement {
    sid    = "EMRServerlessManage"
    effect = "Allow"
    actions = [
      "emr-serverless:GetApplication",
      "emr-serverless:UpdateApplication",
      "emr-serverless:StartApplication",
      "emr-serverless:StopApplication",
      "emr-serverless:TagResource",
      "emr-serverless:ListApplications",
    ]
    resources = [
      "arn:aws:emr-serverless:${var.aws_region}:${data.aws_caller_identity.current.account_id}:/applications/${var.emr_application_id}",
    ]
  }

  # IAM: manage this project's own roles/policies (Terraform-managed
  # resources), not IAM broadly. No wildcard iam:* — scoped actions only.
  statement {
    sid    = "IAMProjectRoleManagement"
    effect = "Allow"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:GetRole",
      "iam:PutRolePolicy",
      "iam:GetRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:ListRolePolicies",
      "iam:ListAttachedRolePolicies",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:PassRole",
      "iam:CreatePolicy",
      "iam:DeletePolicy",
      "iam:GetPolicy",
      "iam:GetPolicyVersion",
      "iam:CreatePolicyVersion",
      "iam:DeletePolicyVersion",
      "iam:ListPolicyVersions",
      "iam:TagPolicy",
    ]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/remittance-corridor-*",
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/remittance-corridor-*",
    ]
  }

  # OIDC provider read/tag access only — CD should never need to modify
  # the provider itself, just reference it.
  statement {
    sid    = "IAMOIDCProviderRead"
    effect = "Allow"
    actions = [
      "iam:GetOpenIDConnectProvider",
      "iam:ListOpenIDConnectProviders",
    ]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com",
    ]
  }

  statement {
    sid       = "STSGetCallerIdentity"
    effect    = "Allow"
    actions   = ["sts:GetCallerIdentity"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "cd_permissions" {
  name   = "cd-deploy-permissions"
  role   = aws_iam_role.cd_role.id
  policy = data.aws_iam_policy_document.cd_permissions.json
}

output "cd_role_arn" {
  description = "ARN to set as the CD_ROLE_ARN GitHub Actions repository variable"
  value       = aws_iam_role.cd_role.arn
}
# Read-only access so `terraform plan`/`apply` can refresh every managed
# resource's state. Mirrors ci_plan_readonly in ci_oidc.tf; write access
# stays limited to the scoped statements in cd_permissions above.
resource "aws_iam_role_policy_attachment" "cd_readonly" {
  role       = aws_iam_role.cd_role.id
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
