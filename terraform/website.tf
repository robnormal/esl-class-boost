# S3 bucket for website hosting
resource "aws_s3_bucket" "website" {
  bucket = "rr-history-learning-website"
}

# S3 bucket ACL
resource "aws_s3_bucket_ownership_controls" "website" {
  bucket = aws_s3_bucket.website.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket website configuration
resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"  # For SPA routing, send all errors to index.html
  }
}

# CloudFront Origin Access Identity (OAI)
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for rr-history-learning website"
}

# S3 bucket policy allowing CloudFront access
resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = {
          AWS = "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity ${aws_cloudfront_origin_access_identity.oai.id}"
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website.arn}/*"
      }
    ]
  })
}

# Since we're using CloudFront's default domain, we don't need a custom certificate

# Add a provider specifically for us-east-1 (CloudFront requires us-east-1)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "website" {
  origin {
    domain_name = aws_s3_bucket.website.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.website.bucket}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  # No aliases needed when using the default CloudFront domain

  # Default cache behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.website.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  # SPA routing - send all non-file paths to index.html
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  # Price class (use only North America and Europe)
  price_class = "PriceClass_100"

  # Using CloudFront's default certificate
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Geo restriction
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}

# No Route 53 record needed when using the default CloudFront domain

# Outputs
output "website_bucket_name" {
  value = aws_s3_bucket.website.id
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.website.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.website.domain_name
}

# This output will show the commands to deploy your react app
output "deployment_commands" {
  value = <<-EOT
    # Build your React app
    npm run build

    # Sync to S3
    aws s3 sync build/ s3://${aws_s3_bucket.website.bucket} --delete

    # Invalidate CloudFront cache
    aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.website.id} --paths "/*"
  EOT
}
