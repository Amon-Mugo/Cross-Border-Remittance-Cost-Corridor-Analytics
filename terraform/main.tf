terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "remittance-corridor-tfstate-011294328070"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "remittance-corridor-terraform-locks-011294328070"
    encrypt        = true
  }
}