#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <service-name>"
  echo "Example: $0 vocab_extractor"
  exit 1
fi

SERVICE_NAME=$1
SERVICE_DIR="backend/${SERVICE_NAME}"
REQS_FILE="${SERVICE_DIR}/requirements.txt"
ZIP_FILE="${SERVICE_NAME}_lambda.zip"
ROOT_DIR=$(pwd)
SOURCE_BUCKET=rhr79-history-learning-lambda-code

# Validate service and requirements
if [[ ! -d "$SERVICE_DIR" ]]; then
  echo "❌ Error: Service directory '$SERVICE_DIR' does not exist."
  exit 1
fi

# Switch to correct virtual environment
if command -v deactivate >/dev/null 2>&1; then
  deactivate
fi
source "$SERVICE_DIR/.venv/bin/activate"
echo "- Using virtual environment: $(which python)"

# Compile requirements
cd "$SERVICE_DIR"
pip-compile
cd "$ROOT_DIR"

echo "📦 Packaging Lambda deployment for service: $SERVICE_NAME"

# Create clean temp staging dir
STAGING_DIR=$(mktemp -d)
echo "📁 Created staging dir: $STAGING_DIR"

# Copy Python source files
echo "📄 Copying Python files from $SERVICE_DIR"
cp "$SERVICE_DIR"/*.py "$STAGING_DIR/"

# Install dependencies into staging dir
echo "📦 Installing dependencies to staging dir"
pip install -r "$REQS_FILE" --target "$STAGING_DIR"

# RHR - Manually remove binary `lxml` package, which will be found in a layer on AWS
if [ "$SERVICE_NAME" == paragraphs ]; then
  echo "X Removing binary lxml library from $STAGING_DIR"
  rm -rf "$STAGING_DIR"/lxml -rf "$STAGING_DIR"/lxml-*.dist-info
fi

# Create ZIP file
echo "🗜️  Creating ZIP file: $ZIP_FILE"
cd "$STAGING_DIR"
if [ -f "$ROOT_DIR/$ZIP_FILE" ]; then
  rm "$ROOT_DIR/$ZIP_FILE" # just in case still there
fi
zip -r9 "$ROOT_DIR/$ZIP_FILE" . > /dev/null
cd "$ROOT_DIR"

# Cleanup
rm -rf "$STAGING_DIR"

echo "📤 Uploading ZIP file: $ZIP_FILE"

# Create bucket if it doesn't exist
aws s3api head-bucket --bucket $SOURCE_BUCKET || \
  aws s3 mb "s3://$SOURCE_BUCKET"

# Upload Lambda package files
aws s3 cp "$ROOT_DIR/$ZIP_FILE" "s3://$SOURCE_BUCKET/lambda-packages/"

echo "✅ Lambda package uploaded to S3"
deactivate

echo "-> Deploying to Lambda"
aws lambda update-function-code \
  --function-name "history-learning-$SERVICE_NAME" \
  --s3-bucket $SOURCE_BUCKET \
  --s3-key "lambda-packages/$ZIP_FILE"
