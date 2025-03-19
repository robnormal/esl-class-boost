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


# 1. PARAGRAPHS BUCKET - Lambda access only
resource "aws_s3_bucket" "paragraphs" {
  bucket = "rhr79-history-learning-paragraphs"
  tags   = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "paragraphs" {
  bucket = aws_s3_bucket.paragraphs.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "paragraphs" {
  bucket = aws_s3_bucket.paragraphs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "paragraphs" {
  bucket = aws_s3_bucket.paragraphs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_role.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.paragraphs.arn}",
          "${aws_s3_bucket.paragraphs.arn}/*"
        ]
      }
    ]
  })
}

# 2. SUMMARIES BUCKET - Lambda access only
resource "aws_s3_bucket" "summaries" {
  bucket = "rhr79-history-learning-summaries"
  tags   = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "summaries" {
  bucket = aws_s3_bucket.summaries.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "summaries" {
  bucket = aws_s3_bucket.summaries.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "summaries" {
  bucket = aws_s3_bucket.summaries.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_role.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.summaries.arn}",
          "${aws_s3_bucket.summaries.arn}/*"
        ]
      }
    ]
  })
}

# 3. SUBMISSIONS BUCKET - Lambda access + presigned URLs
resource "aws_s3_bucket" "submissions" {
  bucket = "rhr79-history-learning-submissions"
  tags   = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "submissions" {
  bucket = aws_s3_bucket.submissions.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "submissions" {
  bucket = aws_s3_bucket.submissions.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# No explicit bucket policy needed for submissions bucket
# Using IAM roles for Lambda access and presigned URLs for uploads
# The permissions to generate presigned URLs are granted at the IAM level
