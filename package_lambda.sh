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

# Validate service and requirements
if [[ ! -d "$SERVICE_DIR" ]]; then
  echo "❌ Error: Service directory '$SERVICE_DIR' does not exist."
  exit 1
fi

if [[ ! -f "$REQS_FILE" ]]; then
  echo "❌ Error: No requirements.txt found at $REQS_FILE"
  echo "➡️  You may need to run pip-compile or ./setup_envs.sh"
  exit 1
fi

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

# Create ZIP file
echo "🗜️  Creating ZIP file: $ZIP_FILE"
cd "$STAGING_DIR"
zip -r9 "$ROOT_DIR/$ZIP_FILE" . > /dev/null
cd "$ROOT_DIR"

# Cleanup
rm -rf "$STAGING_DIR"

echo "✅ Lambda ZIP ready: $ZIP_FILE"
