#!/bin/bash

# Configuration
BACKUP_DIR="data/db/backups"
MAX_DAILY_BACKUPS=30
MAX_WEEKLY_BACKUPS=12
MAX_MONTHLY_BACKUPS=24

# Create backup directories if they don't exist
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/weekly"
mkdir -p "$BACKUP_DIR/monthly"
mkdir -p "logs"

# Log file
LOG_FILE="logs/db_backup_$(date +%Y-%m-%d).log"

# Log function
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting database backup process"

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

# Get current date info
DATE=$(date +%Y-%m-%d)
DAY_OF_WEEK=$(date +%u)
DAY_OF_MONTH=$(date +%d)
MONTH=$(date +%B | tr '[:upper:]' '[:lower:]')
YEAR=$(date +%Y)

# Create daily backup
DAILY_BACKUP_FILE="$BACKUP_DIR/daily/expense_app_backup_$DATE.sql.gz"
log "Creating daily backup: $DAILY_BACKUP_FILE"

if [ -f "/.dockerenv" ]; then
  # Inside Docker
  pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$DAILY_BACKUP_FILE"
else
  # On host
  $DOCKER_CMD pg_dump -U postgres expense_app | gzip > "$DAILY_BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
  log "Daily backup completed successfully"
else
  log "ERROR: Daily backup failed"
  exit 1
fi

# Create weekly backup on Sunday (day 7)
if [ "$DAY_OF_WEEK" = "7" ]; then
  WEEK_NUM=$(date +%V)
  WEEKLY_BACKUP_FILE="$BACKUP_DIR/weekly/expense_app_backup_week${WEEK_NUM}_$DATE.sql.gz"
  log "Creating weekly backup: $WEEKLY_BACKUP_FILE"
  
  # Just copy the daily backup to save resources
  cp "$DAILY_BACKUP_FILE" "$WEEKLY_BACKUP_FILE"
  
  if [ $? -eq 0 ]; then
    log "Weekly backup completed successfully"
  else
    log "ERROR: Weekly backup failed"
  fi
fi

# Create monthly backup on the 1st of the month
if [ "$DAY_OF_MONTH" = "01" ]; then
  MONTHLY_BACKUP_FILE="$BACKUP_DIR/monthly/expense_app_backup_${MONTH}_${YEAR}.sql.gz"
  log "Creating monthly backup: $MONTHLY_BACKUP_FILE"
  
  # Just copy the daily backup to save resources
  cp "$DAILY_BACKUP_FILE" "$MONTHLY_BACKUP_FILE"
  
  if [ $? -eq 0 ]; then
    log "Monthly backup completed successfully"
  else
    log "ERROR: Monthly backup failed"
  fi
fi

# Rotate old backups
log "Rotating old backups"

# Delete old daily backups
find "$BACKUP_DIR/daily" -name "*.sql.gz" -type f | sort -r | tail -n +$((MAX_DAILY_BACKUPS+1)) | xargs -r rm
log "Rotated daily backups, keeping last $MAX_DAILY_BACKUPS"

# Delete old weekly backups
find "$BACKUP_DIR/weekly" -name "*.sql.gz" -type f | sort -r | tail -n +$((MAX_WEEKLY_BACKUPS+1)) | xargs -r rm
log "Rotated weekly backups, keeping last $MAX_WEEKLY_BACKUPS"

# Delete old monthly backups
find "$BACKUP_DIR/monthly" -name "*.sql.gz" -type f | sort -r | tail -n +$((MAX_MONTHLY_BACKUPS+1)) | xargs -r rm
log "Rotated monthly backups, keeping last $MAX_MONTHLY_BACKUPS"

log "Backup process completed successfully" 