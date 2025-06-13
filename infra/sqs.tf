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

# Create SNS topic for paragraphs bucket notifications
resource "aws_sns_topic" "paragraphs_notifications" {
  name = "history-learning-paragraphs-notifications"
  tags = local.common_tags
}

# Allow S3 to publish to the SNS topic
resource "aws_sns_topic_policy" "paragraphs_notifications" {
  arn = aws_sns_topic.paragraphs_notifications.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.paragraphs_notifications.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" : aws_s3_bucket.paragraphs.arn
          }
        }
      }
    ]
  })
}

# Subscribe vocabulary queue to SNS topic
resource "aws_sns_topic_subscription" "vocabulary_queue_subscription" {
  topic_arn = aws_sns_topic.paragraphs_notifications.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.vocabulary_queue.arn
}

# Subscribe summaries queue to SNS topic
resource "aws_sns_topic_subscription" "summaries_queue_subscription" {
  topic_arn = aws_sns_topic.paragraphs_notifications.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.summaries_queue.arn
}

# Allow SNS to send messages to vocabulary queue
resource "aws_sqs_queue_policy" "vocabulary_queue_policy" {
  queue_url = aws_sqs_queue.vocabulary_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.vocabulary_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" : aws_sns_topic.paragraphs_notifications.arn
          }
        }
      }
    ]
  })
}

# Allow SNS to send messages to summaries queue
resource "aws_sqs_queue_policy" "summaries_queue_policy" {
  queue_url = aws_sqs_queue.summaries_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.summaries_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" : aws_sns_topic.paragraphs_notifications.arn
          }
        }
      }
    ]
  })
}

# Send notification to paragraphs_queue when file uploaded to submissions bucket
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

# Update S3 bucket notification to use SQS for submissions bucket
resource "aws_s3_bucket_notification" "submissions_s3_upload_trigger" {
  bucket = aws_s3_bucket.submissions.id

  queue {
    queue_arn = aws_sqs_queue.paragraphs_queue.arn
    events    = ["s3:ObjectCreated:*"]
  }
}

# Update S3 bucket notification to use SNS for paragraphs bucket
resource "aws_s3_bucket_notification" "paragraphs_s3_upload_trigger" {
  bucket = aws_s3_bucket.paragraphs.id

  topic {
    topic_arn = aws_sns_topic.paragraphs_notifications.arn
    events    = ["s3:ObjectCreated:*"]
  }
}
