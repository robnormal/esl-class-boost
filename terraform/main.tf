provider "aws" {
  region = "us-east-2"
}

resource "aws_s3_bucket" "uploads" {
  bucket = "rr-history-learning-uploads"
}

resource "aws_s3_bucket" "summaries" {
  bucket = "rr-history-learning-summaries"
}

# Cognito User Pool with admin-only account creation
resource "aws_cognito_user_pool" "user_pool" {
  name = "rr-history-learning-cognito-user-pool"
  auto_verified_attributes = ["email"]

  # Disable self-registration
  admin_create_user_config {
    allow_admin_create_user_only = true
  }
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "user_pool_client" {
  name         = "rr-history-learning-cognito-user-pool-client"
  user_pool_id = aws_cognito_user_pool.user_pool.id
  generate_secret = false

  allowed_oauth_flows = ["implicit", "code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes = ["email", "openid", "profile"]
  callback_urls = ["http://localhost:3000", "http://12124-rhr-test-static-server-ie2n3.s3-website.us-east-2.amazonaws.com/"]
  logout_urls = ["http://localhost:3000/logout", "http://12124-rhr-test-static-server-ie2n3.s3-website.us-east-2.amazonaws.com/logout"]

  explicit_auth_flows = [
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.user_pool.id
}

output "cognito_user_pool_client_id" {
  value = aws_cognito_user_pool_client.user_pool_client.id
}
