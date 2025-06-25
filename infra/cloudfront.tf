# S3 bucket for website hosting
resource "aws_s3_bucket" "website" {
  bucket = "rhr79-history-learning-website"
  tags   = local.common_tags
}

# S3 bucket ACL (strictly speaking, we're disabling ACLs here)
resource "aws_s3_bucket_ownership_controls" "website" {
  bucket = aws_s3_bucket.website.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket policy allowing CloudFront access
resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "${aws_cloudfront_origin_access_identity.oai.iam_arn}"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.website.arn}/*"
      }
    ]
  })
}

# S3 bucket website configuration
resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html" # For SPA routing, send all errors to index.html
  }
}


# CloudFront Origin Access Identity (OAI)
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for history-learning website"
}

# Create a new cache policy for your CloudFront distribution
resource "aws_cloudfront_cache_policy" "website_cache_policy" {
  name        = "WebsiteCachePolicy"
  comment     = "Cache policy for history learning website"
  default_ttl = 3600
  max_ttl     = 86400
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "all"
    }
    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Authorization"]
      }
    }
    query_strings_config {
      query_string_behavior = "all"
    }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

# Since we're using CloudFront's default domain, we don't need a custom certificate

# CloudFront distribution
resource "aws_cloudfront_distribution" "website" {
  provider = aws.us_east_1

  origin {
    domain_name = aws_lb.app_alb.dns_name
    origin_id   = "ALB-${aws_lb.app_alb.name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

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
  tags                = local.common_tags

  # No aliases needed when using the default CloudFront domain

  # Default cache behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.website.bucket}"

    cache_policy_id            = aws_cloudfront_cache_policy.website_cache_policy.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
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

  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["HEAD", "DELETE", "POST", "GET", "OPTIONS", "PUT", "PATCH"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-${aws_lb.app_alb.name}"

    cache_policy_id            = aws_cloudfront_cache_policy.website_cache_policy.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }
}

# No Route 53 record needed when using the default CloudFront domain

# Add security headers policy for CloudFront
resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name = "history-learning-security-headers"

  security_headers_config {
    content_security_policy {
      content_security_policy = "default-src 'self'; connect-src 'self' https://cognito-idp.us-east-2.amazonaws.com https://*.auth.us-east-2.amazoncognito.com https://${aws_s3_bucket.submissions.bucket_domain_name} https://cxlkv80qo6.execute-api.us-east-2.amazonaws.com; script-src 'self'; object-src 'none';"
      override                = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    strict_transport_security {
      access_control_max_age_sec = 63072000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    xss_protection {
      mode_block = true
      protection = true
      override   = true
    }
  }
}

# Permission to submit to S3 bucket
resource "aws_s3_bucket_cors_configuration" "submissions_cors" {
  bucket = aws_s3_bucket.submissions.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = ["https://${aws_cloudfront_distribution.website.domain_name}"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
