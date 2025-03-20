# Add these data sources to get current region and account ID
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

provider "aws" {
  region = "us-east-2"
}

# Add a provider specifically for us-east-1 (CloudFront requires us-east-1)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

variable "stage_name" {
  default = "prod"
}

# Define common tags as locals
locals {
  common_tags = {
    Project     = "history-learning"
    Environment = var.stage_name
    ManagedBy   = "terraform"
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.82.2"
    }
  }
  backend "s3" {
    bucket         = "rhr79-history-learning-terraform-state"
    key            = "history-learning/terraform.tfstate"
    region         = "us-east-2"
    key            = "history-learning-terraform.tfstate"
    use_lockfile   = true
  }
  required_version = "~> 1.10"
}

# Create the S3 bucket for state storage
resource "aws_s3_bucket" "terraform_state" {
  bucket = "rhr79-history-learning-terraform-state"
  tags   = local.common_tags

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
}

# Enable versioning for state history
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Create DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_lock" {
  name         = "history-learning-terraform-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
