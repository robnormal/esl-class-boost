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

###
# Service IAM policies (access permissions)
###
