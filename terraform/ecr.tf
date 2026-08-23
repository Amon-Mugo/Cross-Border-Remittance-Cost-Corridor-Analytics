# Purpose: ECR repository hosting the PySpark runtime image consumed by
# the EMR Serverless application. Lifecycle policy caps storage cost by
# expiring stale/untagged images; repository policy grants EMR Serverless
# pull access at the image layer.

resource "aws_ecr_repository" "remittance_corridor_ecr" {
  name                 = var.ecr_repository_name
  force_delete         = true
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
  }

  tags = {
    Project   = var.project_name
    Purpose   = "ECR Repository"
    ManagedBy = "Terraform"
  }
}

resource "aws_ecr_lifecycle_policy" "remittance_corridor_ecr" {
  repository = aws_ecr_repository.remittance_corridor_ecr.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images older than 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 7 images overall"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Allow EMR Serverless to pull the runtime image
resource "aws_ecr_repository_policy" "remittance_corridor_ecr" {
  repository = aws_ecr_repository.remittance_corridor_ecr.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEMRServerlessAccess"
        Effect = "Allow"
        Principal = {
          Service = "emr-serverless.amazonaws.com"
        }
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability",
          "ecr:DescribeImages",
        ]
      }
    ]
  })
}