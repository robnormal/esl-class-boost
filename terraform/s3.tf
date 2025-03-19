resource "aws_s3_bucket" "submissions" {
  bucket = "rhr79-history-learning-submissions"
}

resource "aws_s3_bucket" "paragraphs" {
  bucket = "rhr79-history-learning-paragraphs"
}

resource "aws_s3_bucket" "summaries" {
  bucket = "rhr79-history-learning-summaries"
}

# S3 bucket for website hosting
resource "aws_s3_bucket" "website" {
  bucket = "rhr79-history-learning-website"
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
