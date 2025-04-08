#!/bin/bash

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
    local service_dir="$SCRIPT_DIR/$service_name"
    local venv_dir

    cd "$service_dir"

    # Virtual environment is any directory starting with ".venv"
    venv_dir=$(find . -maxdepth 1 -name ".venv*" -print -quit)

    echo "🚀 Starting $service_name service..."

    if [[ ! -d "$venv_dir" ]]; then
        echo "❌ Virtual environment not found for $service_name. Please run create-virtual-environments.sh first."
        exit 1
    fi

    # Activate virtual environment and start the service
    (
        source "$venv_dir/bin/activate"
        echo "📂 Working directory: $(pwd)"
        echo "🐍 Python version: $(python --version)"

        # Start the service (adjust the command based on how each service should be started)
        case $service_name in
            "api")
                python app.py
                ;;
            "paragraphs")
                python main.py
                ;;
            "vocabulary")
                python main.py
                ;;
            "summaries")
                python main.py
                ;;
        esac
    )
}

start_service "$service_name"

# # Wait for all background processes
# echo "⏳ Services are running. Press Ctrl+C to stop all services."
# wait
