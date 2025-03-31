#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Make the management script executable
chmod +x "$SCRIPT_DIR/file-management.sh"

# Create crontab file with the correct absolute path
echo "# Expense App scheduled tasks" > "$SCRIPT_DIR/crontab"
echo "0 2 * * 3 $SCRIPT_DIR/file-management.sh" >> "$SCRIPT_DIR/crontab"

# Install the crontab
crontab "$SCRIPT_DIR/crontab"

echo "Crontab installed successfully!" 