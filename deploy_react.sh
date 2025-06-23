#!/bin/bash

# Stop on error
set -e

# Get configuration variables from Terraform
cd "$(dirname "${BASH_SOURCE[0]}")"/infra

USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
USER_POOL_CLIENT_ID=$(terraform output -raw cognito_user_pool_client_id)
COGNITO_DOMAIN=$(terraform output -raw cognito_domain)
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name)
CLOUDFRONT_DIST_ID=$(terraform output -raw cloudfront_distribution_id)
WEBSITE_BUCKET=$(terraform output -raw website_bucket_name)

# Build the React app
cd ../frontend

VITE_COGNITO_USER_POOL_ID="$USER_POOL_ID" \
  VITE_COGNITO_USER_POOL_CLIENT_ID="$USER_POOL_CLIENT_ID" \
  VITE_COGNITO_DOMAIN="$COGNITO_DOMAIN" \
  VITE_BACKEND_URL="https://$CLOUDFRONT_DOMAIN/api" \
  npm run build

# Upload to S3 (sync deletes files no longer in the build folder)
aws s3 sync dist/ "s3://$WEBSITE_BUCKET" --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id "$CLOUDFRONT_DIST_ID" --paths "/*"
