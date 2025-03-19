##
# Lambdas
##

# Lambda function for the Flask application
resource "aws_lambda_function" "flask_lambda" {
  function_name = "history-learning-api-lambda"
  runtime       = "python3.13"
  handler       = "app.lambda_handler" # Update based on your Flask app structure
  filename      = "flask_lambda.zip"   # You'll need to create this deployment package
  tags          = local.common_tags

  # You can also use S3 for larger deployment packages
  # s3_bucket     = "my-lambda-deployments"
  # s3_key        = "lambda_function.zip"

  role = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      FLASK_ENV = var.stage_name == "prod" ? "production" : "development"
      # Add other environment variables as needed
    }
  }

  timeout     = 30  # Adjust based on your needs
  memory_size = 256 # Adjust based on your needs
}

resource "aws_lambda_function" "paragraphs_lambda" {
  function_name = "history-learning-paragraphs"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.13"
  filename      = "paragraphs_lambda.zip" # Ensure this file is packaged correctly
  tags          = local.common_tags
}

resource "aws_lambda_function" "vocabulary_lambda" {
  function_name = "history-learning-vocabulary"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.13"
  filename      = "vocabulary_lambda.zip"
  tags          = local.common_tags
}

resource "aws_lambda_function" "summaries_lambda" {
  function_name = "history-learning-summaries"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.13"
  filename      = "summaries_lambda.zip"
  tags          = local.common_tags
}

##
# Associated SQS queues
##

resource "aws_sqs_queue" "vocabulary_queue" {
  name = "history-learning-vocabulary-queue"
  tags = local.common_tags
}

resource "aws_sqs_queue" "summaries_queue" {
  name = "history-learning-summaries-queue"
  tags = local.common_tags
}

##
# Lambda triggers
##

resource "aws_s3_bucket_notification" "submissions_s3_upload_trigger" {
  bucket = aws_s3_bucket.submissions.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.paragraphs_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }
}

resource "aws_lambda_event_source_mapping" "vocabulary_sqs_trigger" {
  event_source_arn = aws_sqs_queue.vocabulary_queue.arn
  function_name    = aws_lambda_function.vocabulary_lambda.arn
}

resource "aws_lambda_event_source_mapping" "summaries_sqs_trigger" {
  event_source_arn = aws_sqs_queue.summaries_queue.arn
  function_name    = aws_lambda_function.summaries_lambda.arn
}

##
# IAM roles (permissions)
##
resource "aws_iam_role" "lambda_role" {
  name = "lambda-with-s3-sqs-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Basic execution policy for Lambda
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambdaBasicExecutionRole"
}

# Allow Lambdas to access any table in DynamoDB
resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name        = "lambda-dynamodb-access-policy"
  description = "Allows Lambda functions to access all DynamoDB tables in the account"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ],
        Resource = [
          "arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/*",
          "arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/*/index/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}

# Replace broad policies with specific, scoped policies
resource "aws_iam_policy" "lambda_s3_policy" {
  name = "lambda-s3-specific-access"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
        ],
        Resource = [
          aws_s3_bucket.submissions.arn,
          "${aws_s3_bucket.submissions.arn}/*",
          aws_s3_bucket.paragraphs.arn,
          "${aws_s3_bucket.paragraphs.arn}/*",
          aws_s3_bucket.summaries.arn,
          "${aws_s3_bucket.summaries.arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

resource "aws_iam_policy" "lambda_sqs_policy" {
  name        = "lambda-sqs-specific-access"
  description = "Allows Lambda functions to access only specific SQS queues with minimum required permissions"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility",
        ],
        Resource = [
          aws_sqs_queue.vocabulary_queue.arn,
          aws_sqs_queue.summaries_queue.arn
        ]
      },
    ]
  })
}

# Then replace the policy attachment
resource "aws_iam_role_policy_attachment" "lambda_sqs_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_sqs_policy.arn
}
