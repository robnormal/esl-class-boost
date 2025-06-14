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

# Function to create ECR repository if it doesn't exist
create_ecr_repository() {
    local repository_name="$1"
    if ! aws ecr describe-repositories --repository-names "$repository_name" --region "$AWS_REGION" >/dev/null 2>&1; then
        echo "📦 Creating ECR repository: $repository_name"
        aws ecr create-repository --repository-name "$repository_name" --region "$AWS_REGION"
    fi
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
    REGISTRY_TAG="rhr-learning-tool-$service-service"

    # Create ECR repository if it doesn't exist
    create_ecr_repository "$REGISTRY_TAG"

    # Build Docker image
    echo "🏗️  Building Docker image for $service..."
    docker build -f "Dockerfile.$service" -t "$REGISTRY_TAG" .

    # Tag image for ECR
    echo "🏷️  Tagging image for ECR..."
    docker tag "$REGISTRY_TAG:latest" "$ECR_REGISTRY/$REGISTRY_TAG:latest"

    # Push to ECR
    echo "⬆️  Pushing image to ECR..."
    docker push "$ECR_REGISTRY/$REGISTRY_TAG:latest"

    echo "✅ Completed processing $service service"
done

echo "🎉 All services have been successfully built and pushed to ECR"
