# API Gateway REST API
resource "aws_api_gateway_rest_api" "api" {
  name        = "history-learning-api"
  description = "API Gateway for Flask Lambda"
  tags        = local.common_tags

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# API Gateway authorizer
resource "aws_api_gateway_authorizer" "cognito" {
  name          = "cognito-authorizer"
  rest_api_id   = aws_api_gateway_rest_api.api.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [aws_cognito_user_pool.user_pool.arn]
}


# API Gateway resource (root path)
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}" # This creates a catch-all proxy resource
}

# API Gateway method for the proxy resource
resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY" # Catches all HTTP methods
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

# Connect the Lambda function to the API Gateway method
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method

  integration_http_method = "POST" # Lambda always requires POST
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.flask_lambda.invoke_arn
}

# Handle the root path as well
resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_rest_api.api.root_resource_id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.flask_lambda.invoke_arn
}

# Deploy the API Gateway
resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
    aws_api_gateway_integration.lambda_root
  ]

  rest_api_id = aws_api_gateway_rest_api.api.id
  description = "Deployment for history learning API"

  # Note: No stage_name attribute here
  # This creates just the deployment without attaching it to a stage
  # stage_name  = var.stage_name # You can change this or use variables
}

# Then, create a separate stage resource that references the deployment
resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.stage_name

  # You can add stage-specific configurations here
  cache_cluster_enabled = false
  cache_cluster_size    = "0.5" # Only needed if cache_cluster_enabled is true

  # Add any stage variables if needed
  variables = {
    "lambdaAlias" = var.stage_name
  }

  # Adding tags to the stage
  tags = local.common_tags
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.flask_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  # Allow invocation from any path in the current stage API Gateway
  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/${var.stage_name}/*"
}

# Enable CORS for the API (important for your SPA)
resource "aws_api_gateway_method" "options_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.options_method.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# Define locals for reusable values
locals {
  # Common response parameters for method responses
  method_response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  # Common response parameters for integration responses
  integration_response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'https://${aws_cloudfront_distribution.website.domain_name}'"
  }
}

# For the OPTIONS method
resource "aws_api_gateway_method_response" "options_response" {
  rest_api_id         = aws_api_gateway_rest_api.api.id
  resource_id         = aws_api_gateway_resource.proxy.id
  http_method         = aws_api_gateway_method.options_method.http_method
  status_code         = "200"
  response_parameters = local.method_response_parameters
}

resource "aws_api_gateway_integration_response" "options_integration_response" {
  rest_api_id         = aws_api_gateway_rest_api.api.id
  resource_id         = aws_api_gateway_resource.proxy.id
  http_method         = aws_api_gateway_method.options_method.http_method
  status_code         = aws_api_gateway_method_response.options_response.status_code
  response_parameters = local.integration_response_parameters
}

# For the proxy method
resource "aws_api_gateway_method_response" "proxy_response" {
  rest_api_id         = aws_api_gateway_rest_api.api.id
  resource_id         = aws_api_gateway_resource.proxy.id
  http_method         = aws_api_gateway_method.proxy.http_method
  status_code         = "200"
  response_parameters = local.method_response_parameters
}

resource "aws_api_gateway_integration_response" "proxy_integration_response" {
  rest_api_id         = aws_api_gateway_rest_api.api.id
  resource_id         = aws_api_gateway_resource.proxy.id
  http_method         = aws_api_gateway_method.proxy.http_method
  status_code         = aws_api_gateway_method_response.proxy_response.status_code
  response_parameters = local.integration_response_parameters
}

# For the root method
resource "aws_api_gateway_method_response" "proxy_root_response" {
  rest_api_id         = aws_api_gateway_rest_api.api.id
  resource_id         = aws_api_gateway_rest_api.api.root_resource_id
  http_method         = aws_api_gateway_method.proxy_root.http_method
  status_code         = "200"
  response_parameters = local.method_response_parameters
}

resource "aws_api_gateway_integration_response" "proxy_root_integration_response" {
  rest_api_id         = aws_api_gateway_rest_api.api.id
  resource_id         = aws_api_gateway_rest_api.api.root_resource_id
  http_method         = aws_api_gateway_method.proxy_root.http_method
  status_code         = aws_api_gateway_method_response.proxy_root_response.status_code
  response_parameters = local.integration_response_parameters
}

##
# Firewall
##

# WAF (web application firewall) WebACL for the API Gateway
# We use the standard, default rules
resource "aws_wafv2_web_acl" "api_waf" {
  name  = "history-learning-api-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Add AWS managed rule sets
  rule {
    name     = "AWS-AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWS-AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "api-waf"
    sampled_requests_enabled   = true
  }
}

# Associate WAF with API Gateway
resource "aws_wafv2_web_acl_association" "api_waf_association" {
  resource_arn = aws_api_gateway_stage.api_stage.arn
  web_acl_arn  = aws_wafv2_web_acl.api_waf.arn
}
