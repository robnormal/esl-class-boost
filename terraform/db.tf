# 1. Users Table
resource "aws_dynamodb_table" "users_table" {
  name         = "Users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"
  range_key    = "email"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # GSI for email lookups
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    range_key       = "userId"
    projection_type = "ALL"
  }

  tags = merge(local.common_tags, {
    Name = "Users-Table"
  })
}

# 2. Submissions Table
resource "aws_dynamodb_table" "submissions_table" {
  name         = "Submissions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "submissionId"
  range_key    = "userId"

  attribute {
    name = "submissionId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "N"
  }

  # GSI for getting all submissions for a user in descending order
  global_secondary_index {
    name            = "user-submissions-index"
    hash_key        = "userId"
    range_key       = "createdAt"
    projection_type = "ALL"
  }

  tags = merge(local.common_tags, {
    Name = "Submissions-Table"
  })
}

# 3. Summaries Table
resource "aws_dynamodb_table" "summaries_table" {
  name         = "Summaries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "submissionId"
  range_key    = "SK"

  attribute {
    name = "submissionId"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  tags = merge(local.common_tags, {
    Name = "Summaries-Table"
  })
}

# 4. Vocabulary Table
resource "aws_dynamodb_table" "vocabulary_table" {
  name         = "Vocabulary"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "submissionId"
  range_key    = "SK"

  attribute {
    name = "submissionId"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  tags = merge(local.common_tags, {
    Name = "Vocabulary-Table"
  })
}
