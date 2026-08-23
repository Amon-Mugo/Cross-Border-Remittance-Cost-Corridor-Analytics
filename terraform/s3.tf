resource "aws_s3_bucket" "remittance_cost_corridor_analytics_raw" {
    bucket = var.raw_bucket_name
    tags = {
        Project = var.project_name
        Layer   = "Raw"
        Environment = "prod"
    }
}

resource "aws_s3_bucket_ownership_controls" "remittance_cost_corridor_analytics_raw" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_raw.id

    rule {
        object_ownership = "BucketOwnerEnforced"
    }
}

resource "aws_s3_bucket_public_access_block" "remittance_cost_corridor_analytics_raw" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_raw.id

    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "remittance_cost_corridor_analytics_raw" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_raw.id
    versioning_configuration {
        status = "Enabled"  
    }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "remittance_cost_corridor_analytics_raw" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_raw.id
    rule {
        apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
        }
    }
}

#cost control and clean up
resource "aws_s3_bucket_lifecycle_configuration" "remittance_cost_corridor_analytics_raw" {

    depends_on = [aws_s3_bucket_versioning.remittance_cost_corridor_analytics_raw] # apply versioning first
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_raw.id
    rule {
        id = "raw-data-cleanup"
        status = "Enabled"
        filter {}
        transition {
            days          = 90
            storage_class = "INTELLIGENT_TIERING"
        }
        noncurrent_version_expiration {
            noncurrent_days = 30
        }
        abort_incomplete_multipart_upload {
            days_after_initiation = 6
        }
       

    }
}

#curated bucket

resource "aws_s3_bucket" "remittance_cost_corridor_analytics_curated" {
    bucket = var.curated_bucket_name
    tags = {
        Project = var.project_name
        Layer  = "curated"
        Environment = "prod"
    }
}

resource "aws_s3_bucket_ownership_controls" "remittance_cost_corridor_analytics_curated" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_curated.id

    rule {
        object_ownership = "BucketOwnerEnforced"
    }
}

resource "aws_s3_bucket_public_access_block" "remittance_cost_corridor_analytics_curated" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_curated.id

    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "remittance_cost_corridor_analytics_curated" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_curated.id
    versioning_configuration {
        status = "Enabled"  
    }

}

resource "aws_s3_bucket_server_side_encryption_configuration" "remittance_cost_corridor_analytics_curated" {
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_curated.id
    rule {
        apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
        }
    }
}

# cost control and clean up
resource "aws_s3_bucket_lifecycle_configuration" "remittance_cost_corridor_analytics_curated" {
    depends_on = [aws_s3_bucket_versioning.remittance_cost_corridor_analytics_curated] # apply versioning first
    bucket = aws_s3_bucket.remittance_cost_corridor_analytics_curated.id
    rule {
        id = "curated-data-cleanup"
        status = "Enabled"
        filter {}
        transition {
            days          = 90
            storage_class = "INTELLIGENT_TIERING"
        }
        noncurrent_version_expiration {
            noncurrent_days = 30
        }
        abort_incomplete_multipart_upload {
            days_after_initiation = 6
        }
        
    }
}