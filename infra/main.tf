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
    # This bucket must already exist. It cannot be generated from this config
    bucket       = "rhr79-terraform-state"
    key          = "history-learning/terraform.tfstate"
    region       = "us-east-2"
    use_lockfile = true
  }
  required_version = "~> 1.10"
}
