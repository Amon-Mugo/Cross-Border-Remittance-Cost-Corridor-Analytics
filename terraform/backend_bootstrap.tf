# use s3+dynamodb as backend

resource "aws_s3_bucket" "tfstate" {
    bucket =  "remittance-corridor-tfstate-011294328070"
    lifecycle {
        prevent_destroy = true
    }
    tags = {
        Project = var.project_name
        Purpose = "Terraform State"
        ManagedBy = "Terraform"
    }
}

resource "aws_s3_bucket_versioning" "tfstate" {
    bucket = aws_s3_bucket.tfstate.id
    versioning_configuration {
        status = "Enabled"
    }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
    bucket = aws_s3_bucket.tfstate.id

    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
    bucket = aws_s3_bucket.tfstate.id
    rule {
        apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
        }
    }
}

# DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_locks" {
    name         = "remittance-corridor-terraform-locks-011294328070"
    billing_mode = "PAY_PER_REQUEST"
    hash_key     = "LockID"
    lifecycle {
        prevent_destroy = true
    }

    attribute {
        name = "LockID"
        type = "S"
    }

    tags = {
        Project   = var.project_name
        Purpose   = "Terraform State Lock"
        ManagedBy = "Terraform"
    }
 }