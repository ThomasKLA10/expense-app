#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the project root directory
cd "$SCRIPT_DIR/.." || exit 1

# Log directory
LOG_DIR="logs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log file with date in name for rotation
LOG_DATE=$(date +"%Y-%m-%d")
LOG_FILE="$LOG_DIR/file-management-$LOG_DATE.log"

# Rotate logs - keep only the last 10 log files
find "$LOG_DIR" -name "file-management-*.log" -type f | sort -r | tail -n +11 | xargs -r rm

# Add timestamp to log
echo "=== File Management Run: $(date) ===" >> "$LOG_FILE"

# Check if we're in a Docker environment
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    # Run the management command in Docker
    docker-compose run --rm web flask manage-files >> "$LOG_FILE" 2>&1
else
    # Run the management command directly (for BBDeployor)
    export FLASK_APP=run.py
    flask manage-files >> "$LOG_FILE" 2>&1
fi

# Add completion message
echo "Completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE" 