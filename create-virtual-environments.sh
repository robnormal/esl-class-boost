#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

cd "$(dirname "${BASH_SOURCE[0]}")"

ROOT_DIR=$(pwd)
ROOT_DEV_IN="$ROOT_DIR/requirements-dev.in"

# Check root requirements-dev.in
if [[ ! -f "$ROOT_DEV_IN" ]]; then
  echo "❌ Root requirements-dev.in not found at $ROOT_DEV_IN"
  exit 1
fi

# Use find -print0 and while-read loop to handle spaces safely
find backend -type f -name "requirements.in" -print0 | while IFS= read -r -d '' SERVICE_REQ_IN; do
  SERVICE_DIR=$(dirname "$SERVICE_REQ_IN")
  echo "🔧 Setting up: $SERVICE_DIR"

  VENV_DIR="$SERVICE_DIR/.venv"

  # Create virtual environment if not present
  if [[ ! -d "$VENV_DIR" ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
  fi

  # Activate virtual environment
  source "$VENV_DIR/bin/activate"

  # Upgrade pip and install pip-tools
  echo "⬆️  Installing/upgrading pip-tools..."
  pip install --upgrade pip
  pip install pip-tools

  # Compile service requirements
  echo "📄 Compiling $SERVICE_DIR/requirements.txt"
  pip-compile "$SERVICE_REQ_IN" --output-file "$SERVICE_DIR/requirements.txt"

  # Compile dev requirements (into same service folder)
  echo "🛠️  Compiling $SERVICE_DIR/requirements-dev.txt"
  pip-compile "$ROOT_DEV_IN" "$SERVICE_REQ_IN" --output-file "$SERVICE_DIR/requirements-dev.txt"

  # Install dev requirements locally
  echo "> Installing dependencies in $SERVICE_DIR/requirements-dev.txt"
  pip-sync "$SERVICE_DIR/requirements-dev.txt"

  # Deactivate
  deactivate

  echo "✅ Finished: $SERVICE_DIR"
  echo
done

echo "🎉 All environments are set up!"
