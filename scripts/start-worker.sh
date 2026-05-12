#!/bin/bash
# Start the message processor worker
# This script ensures the correct environment is loaded

set -e

# Project root directory
PROJECT_ROOT="/home/saadahmed/hk-5"
cd "$PROJECT_ROOT"

# Activate virtual environment
source .venv/bin/activate

# Clear any existing DATABASE_URL from environment
unset DATABASE_URL

# Start the worker
echo "Starting message processor worker..."
python -m backend.worker.message_processor
