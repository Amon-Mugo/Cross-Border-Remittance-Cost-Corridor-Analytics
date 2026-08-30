
# Purpose: IAM roles for the pipeline — an ingestion role (assumed locally
# for landing raw data to S3) and the EMR Serverless execution role, with
# scoped policies for S3 read/write, CloudWatch logging, and ECR image pull.

data "aws_caller_identity" "current" {} # retrieve AWS account id

# Ingestion role — assumed by the data-corp-admin profile / CI to land raw
# files into the raw bucket.
resource "aws_iam_role" "remittance_corridor_ingestion" {
  name = var.ingestion_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_ce243a96ce57c86d"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project = var.project_name
    Purpose = "EMR Serverless Ingestion Role"
  }
}
resource "aws_iam_policy" "remittance_corridor_ingestion_s3_write" {
  name        = "remittance-corridor-ingestion-s3-write-policy"
  description = "IAM policy for writing to S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.remittance_cost_corridor_analytics_raw.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "remittance_corridor_ingestion_s3_write" {
  role       = aws_iam_role.remittance_corridor_ingestion.name
  policy_arn = aws_iam_policy.remittance_corridor_ingestion_s3_write.arn
}

# EMR Serverless execution role — assumed by the EMR Serverless service to
# run the PySpark job. Trust policy scoped to the emr-serverless principal.
resource "aws_iam_role" "remittance_corridor_emr_execution" {
  name = var.emr_execution_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "emr-serverless.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project = var.project_name
    Purpose = "EMR Serverless Execution Role"
  }
}

# Read raw / write+read+delete curated
resource "aws_iam_policy" "remittance_corridor_emr_s3_access" {
  name        = "remittance-corridor-emr-s3-access-policy"
  description = "IAM policy for EMR Serverless to access S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.remittance_cost_corridor_analytics_raw.arn,
          "${aws_s3_bucket.remittance_cost_corridor_analytics_raw.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.remittance_cost_corridor_analytics_curated.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.remittance_cost_corridor_analytics_curated.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "remittance_corridor_emr_s3_access" {
  role       = aws_iam_role.remittance_corridor_emr_execution.name
  policy_arn = aws_iam_policy.remittance_corridor_emr_s3_access.arn
}

# CloudWatch logging for the EMR Serverless application
resource "aws_iam_policy" "remittance_corridor_emr_s3_logging" {
  name        = "remittance-corridor-emr-s3-logging-policy"
  description = "IAM policy for EMR Serverless to write logs to CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "logs:DescribeLogGroups"
        ]
        Resource = "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:log-group:/aws/emr-serverless/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "remittance_corridor_emr_s3_logging" {
  role       = aws_iam_role.remittance_corridor_emr_execution.name
  policy_arn = aws_iam_policy.remittance_corridor_emr_s3_logging.arn
}

# ECR pull access — required for EMR Serverless to retrieve the runtime
resource "aws_iam_policy" "remittance_corridor_emr_ecr_pull" {
  name        = "remittance-corridor-emr-ecr-pull-policy"
  description = "IAM policy allowing EMR Serverless execution role to pull the runtime image from ECR"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability",
          "ecr:DescribeImages"
        ]
        Resource = aws_ecr_repository.remittance_corridor_ecr.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "remittance_corridor_emr_ecr_pull" {
  role       = aws_iam_role.remittance_corridor_emr_execution.name
  policy_arn = aws_iam_policy.remittance_corridor_emr_ecr_pull.arn
}