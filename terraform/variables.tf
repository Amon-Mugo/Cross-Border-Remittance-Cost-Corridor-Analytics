variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  type        = string
  default     = ""
  description = "AWS Profile to use for the AWS CLI"
}

variable "project_name" {
  type = string
}

variable "ingestion_role_name" {
  type = string
}

variable "emr_execution_role_name" {
  type = string
}

variable "ecr_repository_name" {
  type = string
}

variable "emr_application_name" {
  type = string
}

variable "raw_bucket_name" {
  type        = string
  description = "Name of the S3 bucket to store raw data"
}

variable "curated_bucket_name" {
  type        = string
  description = "Name of the S3 bucket to store curated data"
}

variable "emr_image_tag" {
  type        = string
  default     = "V5"
  description = "EMR image tag"
}

variable "tfstate_bucket_name" {
  description = "S3 bucket name for Terraform state"
  type        = string
}

variable "tfstate_lock_table_name" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
}

variable "snowflake_iam_user_arn" {
  description = "Snowflake's generated IAM user ARN (from DESC INTEGRATION)"
  type        = string
}

variable "snowflake_external_id" {
  description = "Snowflake's generated external ID (from DESC INTEGRATION)"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}