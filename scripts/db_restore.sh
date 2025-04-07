#!/bin/bash

# Configuration
BACKUP_DIR="data/db/backups"
LOG_FILE="logs/db_restore_$(date +%Y-%m-%d).log"

# Create logs directory if it doesn't exist
mkdir -p "logs"

# Log function
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to list available backups
list_backups() {
  echo "Available backups:"
  echo "Daily backups:"
  ls -1 "$BACKUP_DIR/daily" | cat -n
  echo ""
  echo "Weekly backups:"
  ls -1 "$BACKUP_DIR/weekly" | cat -n
  echo ""
  echo "Monthly backups:"
  ls -1 "$BACKUP_DIR/monthly" | cat -n
}

# Determine if we're running in Docker
if [ -f "/.dockerenv" ]; then
  # We're inside Docker
  DB_HOST="db"
  DB_USER="postgres"
  DB_NAME="expense_app"
  PGPASSWORD="postgres"
  export PGPASSWORD
else
  # We're on the host - use docker-compose
  DOCKER_CMD="docker-compose exec -T db"
fi

# Check if we should list backups
if [ "$1" = "--list" ]; then
  list_backups
  exit 0
fi

# Check if a backup file was specified
if [ "$1" = "--file" ] && [ -n "$2" ]; then
  BACKUP_FILE="$2"
  
  if [ ! -f "$BACKUP_FILE" ]; then
    log "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
  fi
elif [ "$1" = "--latest" ] && [ -n "$2" ]; then
  # Get the latest backup of the specified type
  TYPE="$2"
  
  if [ "$TYPE" != "daily" ] && [ "$TYPE" != "weekly" ] && [ "$TYPE" != "monthly" ]; then
    log "ERROR: Invalid backup type. Must be daily, weekly, or monthly."
    exit 1
  fi
  
  BACKUP_FILE=$(ls -t "$BACKUP_DIR/$TYPE"/*.sql.gz | head -1)
  
  if [ -z "$BACKUP_FILE" ]; then
    log "ERROR: No $TYPE backups found."
    exit 1
  fi
  
  log "Using latest $TYPE backup: $BACKUP_FILE"
else
  # Interactive mode
  list_backups
  
  echo ""
  echo "Enter backup type (daily, weekly, monthly):"
  read -r TYPE
  
  if [ "$TYPE" != "daily" ] && [ "$TYPE" != "weekly" ] && [ "$TYPE" != "monthly" ]; then
    log "ERROR: Invalid backup type. Must be daily, weekly, or monthly."
    exit 1
  fi
  
  echo "Enter backup number:"
  read -r NUM
  
  BACKUP_NAME=$(ls -1 "$BACKUP_DIR/$TYPE" | sed -n "${NUM}p")
  
  if [ -z "$BACKUP_NAME" ]; then
    log "ERROR: Invalid backup number."
    exit 1
  fi
  
  BACKUP_FILE="$BACKUP_DIR/$TYPE/$BACKUP_NAME"
fi

# Confirm restore
echo "WARNING: This will DESTROY the current database and replace it with the backup."
echo "Are you sure you want to restore from $BACKUP_FILE? (yes/no):"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  log "Restore cancelled."
  exit 0
fi

log "Starting database restore from $BACKUP_FILE"

# Create a temporary file for the uncompressed backup
TEMP_FILE="/tmp/expense_app_restore_$(date +%s).sql"
gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"

if [ $? -ne 0 ]; then
  log "ERROR: Failed to uncompress backup file."
  rm -f "$TEMP_FILE"
  exit 1
fi

# Restore the database
if [ -f "/.dockerenv" ]; then
  # Inside Docker
  # Drop connections to the database
  psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"
  
  # Drop and recreate the database
  dropdb -h "$DB_HOST" -U "$DB_USER" --if-exists "$DB_NAME"
  createdb -h "$DB_HOST" -U "$DB_USER" "$DB_NAME"
  
  # Restore from backup
  psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$TEMP_FILE"
else
  # On host
  # Drop connections to the database
  $DOCKER_CMD psql -U postgres -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'expense_app' AND pid <> pg_backend_pid();"
  
  # Drop and recreate the database
  $DOCKER_CMD dropdb -U postgres --if-exists expense_app
  $DOCKER_CMD createdb -U postgres expense_app
  
  # Restore from backup
  cat "$TEMP_FILE" | $DOCKER_CMD psql -U postgres -d expense_app
fi

if [ $? -eq 0 ]; then
  log "Database restore completed successfully"
else
  log "ERROR: Database restore failed"
  rm -f "$TEMP_FILE"
  exit 1
fi

# Clean up
rm -f "$TEMP_FILE"
log "Temporary files cleaned up"
log "Restore process completed" 