#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

cd "$(dirname "${BASH_SOURCE[0]}")"

ROOT_DIR=$(pwd)

SERVICES=("api" "paragraphs" "summaries" "vocabulary")

# Use find -print0 and while-read loop to handle spaces safely
for SERVICE in "${SERVICES[@]}"; do
  cd "services/$SERVICE"
  echo "🔧 Setting up: $SERVICE"

  hatch env create
  hatch run echo "Installed packages"
  echo "✅ Finished: $SERVICE"
  echo

  cd "$ROOT_DIR"
done

echo "🎉 All environments are set up!"
