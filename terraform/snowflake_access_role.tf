# Used to allow who can access the s3 curated bucket via Snowflake

resource "aws_iam_role" "remittance_corridor_snowflake_access" {
  name = "remittance-corridor-snowflake-access-${var.aws_account_id}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = var.snowflake_iam_user_arn # who gets access to assume the role
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.snowflake_external_id
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "remittance_corridor_snowflake_s3_read" {
  name = "snowflake-s3-read"
  role = aws_iam_role.remittance_corridor_snowflake_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::${var.curated_bucket_name}/*"
      },
      {
        Effect = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::${var.curated_bucket_name}"
      }
    ]
  })
}