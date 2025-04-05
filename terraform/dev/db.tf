# 1. Users Table
resource "aws_dynamodb_table" "users" {
  name         = "prod_history_learning_users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "email"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # GSI for email lookups
  global_secondary_index {
    name            = "email_index"
    hash_key        = "email"
    range_key       = "user_id"
    projection_type = "ALL"
  }

  tags = local.common_tags
}

# 2. Submissions Table
resource "aws_dynamodb_table" "submissions" {
  name         = "prod_history_learning_submissions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "submission_id"
  range_key    = "user_id"

  attribute {
    name = "submission_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  # GSI for getting all submissions for a user in descending order
  global_secondary_index {
    name            = "user_submissions_index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  tags = local.common_tags
}

# 3. Summaries Table
resource "aws_dynamodb_table" "summaries" {
  name         = "prod_history_learning_summaries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "submission_id"
  range_key    = "paragraph"

  attribute {
    name = "submission_id"
    type = "S"
  }

  attribute {
    name = "paragraph" # String like "#SUMMARY#<paragraph number>" - for query flexibility
    type = "S"
  }

  tags = local.common_tags
}

# 4. Vocabulary Table
resource "aws_dynamodb_table" "vocabulary_words" {
  name         = "prod_history_learning_vocabulary"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "submission_id"
  range_key    = "paragraph_word"

  attribute {
    name = "submission_id"
    type = "S"
  }

  attribute {
    name = "paragraph_word" # String like "#VOCAB#<paragraph number>#word" - for query flexibility
    type = "S"
  }

  tags = local.common_tags
}
