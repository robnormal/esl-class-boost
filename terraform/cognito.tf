# Cognito User Pool with admin-only account creation
resource "aws_cognito_user_pool" "user_pool" {
  name = "history-learning-cognito-user-pool"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  # Disable self-service account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "admin_only"
      priority = 1
    }
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
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "rhr79-history-learning-${var.stage_name}" # This will create a domain like history-learning-prod.auth.us-east-2.amazoncognito.com
  user_pool_id = aws_cognito_user_pool.user_pool.id
}
