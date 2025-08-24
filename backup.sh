#!/bin/bash
# Backup Script for Taara Internet Monitor Production Data

set -e

# Configuration
BACKUP_DIR="/app/backups"
DATA_DIR="/app/data"
RETENTION_DAYS=30
DATE=$(date +%Y-%m-%d_%H-%M-%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${GREEN}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

print_info "Starting Taara Monitor backup - $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup database
if [ -f "$DATA_DIR/taara_monitoring.db" ]; then
    print_info "Backing up database..."
    cp "$DATA_DIR/taara_monitoring.db" "$BACKUP_DIR/$DATE/taara_monitoring.db"
    
    # Compress the backup
    gzip "$BACKUP_DIR/$DATE/taara_monitoring.db"
    
    print_info "Database backup completed: $BACKUP_DIR/$DATE/taara_monitoring.db.gz"
else
    print_warning "Database file not found at $DATA_DIR/taara_monitoring.db"
fi

# Backup logs
if [ -d "/app/logs" ]; then
    print_info "Backing up logs..."
    tar -czf "$BACKUP_DIR/$DATE/logs_$DATE.tar.gz" -C /app logs/
    print_info "Logs backup completed: $BACKUP_DIR/$DATE/logs_$DATE.tar.gz"
fi

# Backup configuration (without secrets)
print_info "Backing up configuration..."
cat > "$BACKUP_DIR/$DATE/config_info.txt" << EOF
# Taara Monitor Configuration Backup - $DATE
# This file contains non-sensitive configuration information

BACKUP_DATE=$DATE
DOCKER_VERSION=$(docker --version 2>/dev/null || echo "Unknown")
COMPOSE_VERSION=$(docker-compose --version 2>/dev/null || echo "Unknown")
SYSTEM_INFO=$(uname -a)

# Container Status
$(docker-compose ps 2>/dev/null || echo "Docker Compose not available")

# Disk Usage
$(df -h /app 2>/dev/null || echo "Disk usage not available")
EOF

# Create backup manifest
cat > "$BACKUP_DIR/$DATE/manifest.txt" << EOF
# Backup Manifest - $DATE

Files in this backup:
$(ls -la "$BACKUP_DIR/$DATE/")

Backup size:
$(du -sh "$BACKUP_DIR/$DATE/")
EOF

# Clean old backups
print_info "Cleaning old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true

# Display backup summary
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$DATE/" | cut -f1)
print_info "Backup completed successfully!"
print_info "Backup location: $BACKUP_DIR/$DATE/"
print_info "Backup size: $BACKUP_SIZE"

# Optional: Upload to remote storage (uncomment and configure as needed)
# print_info "Uploading to remote storage..."
# rsync -avz "$BACKUP_DIR/$DATE/" user@backup-server:/backups/taara-monitor/
# aws s3 cp "$BACKUP_DIR/$DATE/" s3://your-backup-bucket/taara-monitor/ --recursive

print_info "Backup process completed!"
