##
# Lambdas
##

# Lambda function for the Flask application
resource "aws_lambda_function" "flask_lambda" {
  function_name = "flask-api-lambda"
  runtime       = "python3.13"
  handler       = "app.lambda_handler"  # Update based on your Flask app structure
  filename      = "flask_lambda.zip"  # You'll need to create this deployment package

  # You can also use S3 for larger deployment packages
  # s3_bucket     = "my-lambda-deployments"
  # s3_key        = "lambda_function.zip"

  role          = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      FLASK_ENV = var.stage_name == "prod" ? "production" : "development"
      # Add other environment variables as needed
    }
  }

  timeout     = 30  # Adjust based on your needs
  memory_size = 256  # Adjust based on your needs
}

resource "aws_lambda_function" "paragraphs_lambda" {
  function_name    = "history-learning-paragraphs"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  runtime         = "python3.13"
  filename        = "paragraphs_lambda.zip" # Ensure this file is packaged correctly
}

resource "aws_lambda_function" "vocabulary_lambda" {
  function_name    = "history-learning-vocabulary"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  runtime         = "python3.13"
  filename        = "vocabulary_lambda.zip"
}

resource "aws_lambda_function" "summaries_lambda" {
  function_name    = "history-learning-summaries"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  runtime         = "python3.13"
  filename        = "summaries_lambda.zip"
}

##
# Associated SQS queues
##

resource "aws_sqs_queue" "vocabulary_queue" {
  name =  "history-learning-vocabulary-queue"
}

resource "aws_sqs_queue" "summaries_queue" {
  name =  "history-learning-summaries-queue"
}

##
# Lambda triggers
##

resource "aws_s3_bucket_notification" "submissions_s3_upload_trigger" {
  bucket = aws_s3_bucket.submissions.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.paragraphs_lambda.arn
    events             = ["s3:ObjectCreated:*"]
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
