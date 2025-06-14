#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

cd "$(dirname "${BASH_SOURCE[0]}")"

# Configuration
AWS_REGION="us-east-2"  # Change this to your region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Array of services
services=("api" "paragraphs" "summaries" "vocabulary")

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
if ! command_exists aws; then
    echo "❌ Error: AWS CLI is not installed"
    exit 1
fi

if ! command_exists docker; then
    echo "❌ Error: Docker is not installed"
    exit 1
fi

# Login to ECR
echo "🔑 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

cd backend

# Process each service
for service in "${services[@]}"; do
    echo "🚀 Processing $service service..."

    # Build Docker image
    echo "🏗️  Building Docker image for $service..."
    docker build -f "Dockerfile.$service" -t "$service-service" .

    # Tag image for ECR
    echo "🏷️  Tagging image for ECR..."
    docker tag "$service-service:latest" "$ECR_REGISTRY/$service-service:latest"

    # Push to ECR
    echo "⬆️  Pushing image to ECR..."
    docker push "$ECR_REGISTRY/$service-service:latest"

    cd ../..
    echo "✅ Completed processing $service service"
done

echo "🎉 All services have been successfully built and pushed to ECR"
