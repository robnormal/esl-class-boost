#!/bin/bash
poetry env info -e

set -euo pipefail
IFS=$'\n\t'

# Handy color codes
RED='\033[0;31m'
RESET='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
service_name=$1

# Function to start a service
start_service() {
    if [[ ! "$service_name" =~ ^(api|paragraphs|vocabulary|summaries)$ ]]; then
        echo -e "${RED}❌ Error: '$service_name' is not a valid service.${RESET}"
        echo "Valid services are: api, paragraphs, vocabulary"
        exit 1
    fi
    cd "$SCRIPT_DIR/$service_name"

    echo "🚀 Starting $service_name service..."

    # Activate virtual environment and start the service
    (
        echo "📂 Working directory: $(pwd)"
        echo "🐍 Python version: $(python --version)"


        # Start the service (adjust the command based on how each service should be started)
        # All services currently call their entrypoint the same way:
        poetry run python src/main.py
    )
}

start_service "$service_name"

# # Wait for all background processes
# echo "⏳ Services are running. Press Ctrl+C to stop all services."
# wait
