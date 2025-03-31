#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR" || exit 1

# Log directory
LOG_DIR="$SCRIPT_DIR/logs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log file with date in name for rotation
LOG_DATE=$(date +"%Y-%m-%d")
LOG_FILE="$LOG_DIR/file-management-$LOG_DATE.log"

# Rotate logs - keep only the last 15 log files
find "$LOG_DIR" -name "file-management-*.log" -type f | sort -r | tail -n +11 | xargs -r rm

# Add timestamp to log
echo "=== File Management Run: $(date) ===" >> "$LOG_FILE"

# Run the management command
docker-compose exec -T web flask manage-files >> "$LOG_FILE" 2>&1

# Add completion message
echo "Completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE" 