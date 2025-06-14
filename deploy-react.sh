#!/bin/bash
# build-and-deploy.sh

# Stop on error
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"/infra
CLOUDFRONT_DIST_ID=$(terraform output -raw cloudfront_distribution_id)

cd ../frontend

# Step 1: Build the React app
npm run build

# Step 2: Upload to S3 (sync deletes files no longer in the build folder)
aws s3 sync dist/ s3://rhr79-history-learning-website --delete

# Step 3: Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DIST_ID --paths "/*"
