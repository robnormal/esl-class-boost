#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

cd "$(dirname "${BASH_SOURCE[0]}")"

# Configuration
AWS_REGION="us-east-2"  # Change this to your region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
BUILD_CONTEXT=$(pwd) # Docker build context has to include both the service code and `common`
SERVICES_DIR=services

# Array of services
ALL_SERVICES=("api" "paragraphs" "summaries" "vocabulary")

if [[ $# -ge 1 && -n "$1" ]]; then
    if [[ ! -d "$SERVICES_DIR/$1" ]]; then
        echo "❌ Error: Service directory '$SERVICES_DIR/$1' does not exist."
        exit 1
    else
        SERVICES=("$1")
        VERSION="${2:-latest}"
    fi
else
    SERVICES=("${ALL_SERVICES[@]}")
fi

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
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"

cd "$SERVICES_DIR"

# Process each service
for service in "${SERVICES[@]}"; do
    echo "🚀 Processing $service service..."
    REGISTRY_TAG="learning-tool-$service"

    # Build Docker image
    echo "🏗️  Building Docker image for $service..."
    docker build -f "Dockerfile.$service" -t "$REGISTRY_TAG:$VERSION" "$BUILD_CONTEXT"

    # Tag image for ECR
    echo "🏷️  Tagging image for ECR..."
    docker tag "$REGISTRY_TAG:$VERSION" "$ECR_REGISTRY/$REGISTRY_TAG:$VERSION"

    # Push to ECR
    echo "⬆️  Pushing image to ECR..."
    docker push "$ECR_REGISTRY/$REGISTRY_TAG:$VERSION"

    echo "✅ Completed processing $service service"
done

echo "🎉 All services have been successfully built and pushed to ECR"
