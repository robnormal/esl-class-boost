resource "aws_s3_bucket" "submissions" {
  bucket = "submissions"
}

resource "aws_s3_bucket" "paragraphs" {
  bucket = "paragraphs"
}

resource "aws_s3_bucket" "summaries" {
  bucket = "summaries"
}

resource "aws_sqs_queue" "vocabulary_queue" {
  name = "vocabulary-queue"
}

resource "aws_sqs_queue" "summaries_queue" {
  name = "summaries-queue"
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "lambda_s3_sqs" {
  name       = "lambda_s3_sqs_attachment"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = "arn:aws:iam::aws:policy/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "s3_upload_lambda" {
  function_name    = "s3_upload_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  runtime         = "python3.8"
  filename        = "lambda.zip" # Ensure this file is packaged correctly
}

resource "aws_s3_bucket_notification" "s3_upload_trigger" {
  bucket = aws_s3_bucket.submissions.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_upload_lambda.arn
    events             = ["s3:ObjectCreated:*"]
  }
}

resource "aws_lambda_function" "vocabulary_lambda" {
  function_name    = "vocabulary_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  runtime         = "python3.8"
  filename        = "lambda.zip"
}

resource "aws_lambda_function" "summaries_lambda" {
  function_name    = "summaries_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  runtime         = "python3.8"
  filename        = "lambda.zip"
}

resource "aws_lambda_event_source_mapping" "vocabulary_sqs_trigger" {
  event_source_arn = aws_sqs_queue.vocabulary_queue.arn
  function_name    = aws_lambda_function.vocabulary_lambda.arn
}

resource "aws_lambda_event_source_mapping" "summaries_sqs_trigger" {
  event_source_arn = aws_sqs_queue.summaries_queue.arn
  function_name    = aws_lambda_function.summaries_lambda.arn
}
