output "website_bucket_name" {
  value = aws_s3_bucket.website.id
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.website.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.website.domain_name
}

output "api_gateway_url" {
  value = aws_api_gateway_deployment.api_deployment.invoke_url
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.user_pool.id
}

output "cognito_user_pool_client_id" {
  value = aws_cognito_user_pool_client.user_pool_client.id
}

# Update outputs to include the domain
output "cognito_domain" {
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
  description = "The domain URL for the Cognito hosted UI"
}

# # This output will show the commands to deploy your react app
# output "deployment_commands" {
#   value = <<-EOT
#     # Build your React app
#     npm run build
#
#     # Sync to S3
#     aws s3 sync build/ s3://${aws_s3_bucket.website.bucket} --delete
#
#     # Invalidate CloudFront cache
#     aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.website.id} --paths "/*"
#   EOT
# }
