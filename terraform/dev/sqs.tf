resource "aws_sqs_queue" "paragraphs_queue" {
  name = "history-learning-paragraphs"
  tags = local.common_tags
}

resource "aws_sqs_queue" "vocabulary_queue" {
  name = "history-learning-vocabulary"
  tags = local.common_tags
}

resource "aws_sqs_queue" "summaries_queue" {
  name = "history-learning-summaries"
  tags = local.common_tags
}

# SQS Queue Policy for paragraphs_queue
resource "aws_sqs_queue_policy" "paragraphs_queue_policy" {
  queue_url = aws_sqs_queue.paragraphs_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.paragraphs_queue.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" : aws_s3_bucket.submissions.arn
          }
        }
      }
    ]
  })
}

# Update S3 bucket notification to use SQS
resource "aws_s3_bucket_notification" "submissions_s3_upload_trigger" {
  bucket = aws_s3_bucket.submissions.id

  queue {
    queue_arn = aws_sqs_queue.paragraphs_queue.arn
    events    = ["s3:ObjectCreated:*"]
  }
}
