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
  type    = string
  default = "remittance-corridor-011294328070"
}

variable "ingestion_role_name" {
  type    = string
  default = "remittance-corridor-ingestion-role-011294328070"
}

variable "emr_execution_role_name" {
  type    = string
  default = "remittance-corridor-emr-execution-role-011294328070"
}

variable "ecr_repository_name" {
  type    = string
  default = "remittance-corridor-ecr-repository-011294328070"
}

variable "emr_application_name" {
  type    = string
  default = "remittance-corridor-emr-application-011294328070"
}

variable "raw_bucket_name" {
  type        = string
  default     = "remittance-corridor-raw-data-bucket-011294328070"
  description = "Name of the S3 bucket to store raw data"
}

variable "curated_bucket_name" {
  type        = string
  default     = "remittance-corridor-curated-data-bucket-011294328070"
  description = "Name of the S3 bucket to store curated data"
}

variable "emr_image_tag" {
  type        = string
  default     = "V5"
  description = "EMR image tag"
}
