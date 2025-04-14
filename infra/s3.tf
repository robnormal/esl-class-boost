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

# We load the code for the Lambdas from here,
# because the size limits are larger than from direct upload
resource "aws_s3_bucket" "lambda_code" {
  bucket = "rhr79-history-learning-lambda-code"
  tags   = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
