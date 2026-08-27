#this is the EMR Serverless application
#used for running spark jobs

resource "aws_emrserverless_application" "remittance_corridor_emr" {
  name          = var.emr_application_name
  release_label = "emr-7.1.0"
  type          = "SPARK"

  image_configuration {
    image_uri = "${aws_ecr_repository.remittance_corridor_ecr.repository_url}:${var.emr_image_tag}"
  }

  maximum_capacity {
    cpu    = "4 vCPU"
    memory = "16 GB"
  }

  auto_start_configuration {
    enabled = true
  }

  auto_stop_configuration {
    enabled              = true
    idle_timeout_minutes = 15
  }

  depends_on = [aws_ecr_repository_policy.remittance_corridor_ecr] # because of the ECR repository policy

  tags = {
    Project   = var.project_name
    Purpose   = "EMR Serverless Application"
    ManagedBy = "Terraform"
  }
}