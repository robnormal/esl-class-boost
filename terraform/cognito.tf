# Cognito User Pool with admin-only account creation
resource "aws_cognito_user_pool" "user_pool" {
  name                     = "history-learning-cognito-user-pool"
  auto_verified_attributes = ["email"]

  # Disable self-registration
  admin_create_user_config {
    allow_admin_create_user_only = true
  }
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "user_pool_client" {
  name            = "history-learning-cognito-user-pool-client"
  user_pool_id    = aws_cognito_user_pool.user_pool.id
  generate_secret = false

  allowed_oauth_flows                  = ["implicit", "code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  # Use CloudFront domain for production, and localhost for development
  callback_urls = var.stage_name == "prod" ? [
    "https://${aws_cloudfront_distribution.website.domain_name}/auth/callback"
    ] : [
    "http://localhost:3000/auth/callback"
  ]

  logout_urls = var.stage_name == "prod" ? [
    "https://${aws_cloudfront_distribution.website.domain_name}/logout"
    ] : [
    "http://localhost:3000/logout"
  ]

  explicit_auth_flows = [
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
}
