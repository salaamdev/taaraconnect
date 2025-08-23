# Taara Internet Monitor - System Administration Guide

## Overview

This guide provides comprehensive instructions for system administrators to deploy, configure, monitor, and maintain the Taara Internet Monitor system.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Configuration Management](#configuration-management)
4. [Service Management](#service-management)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Backup and Recovery](#backup-and-recovery)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Automated Management](#automated-management)

---

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+)
- **RAM**: 512MB
- **Storage**: 2GB available space
- **Network**: Stable internet connection
- **Python**: 3.8 or higher

### Recommended Requirements
- **OS**: Ubuntu 20.04 LTS or Debian 11
- **RAM**: 1GB
- **Storage**: 5GB available space
- **CPU**: 2 cores
- **Network**: High-speed broadband connection

### Software Dependencies
```bash
# Core dependencies
python3 (>= 3.8)
python3-pip
python3-venv
sqlite3

# Optional (for enhanced deployment)
docker
docker-compose
nginx
systemd
```

---

## Installation Methods

### Method 1: Docker Deployment (Recommended)

#### Quick Setup
```bash
# Clone repository
git clone <repository-url> /opt/taara-monitor
cd /opt/taara-monitor

# Configure environment
cp .env.example .env
nano .env  # Edit with actual credentials

# Deploy with Docker Compose
docker-compose up -d

# Verify deployment
docker-compose ps
curl http://localhost:8000/api/data
```

#### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/taara_monitoring.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - scheduler

  scheduler:
    build: .
    command: python scheduler.py
    environment:
      - DATABASE_URL=sqlite:///./data/taara_monitoring.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

### Method 2: Manual Installation

#### System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv sqlite3 nginx

# Create application user
sudo useradd -r -m -s /bin/bash taara
sudo usermod -a -G www-data taara
```

#### Application Setup
```bash
# Switch to application user
sudo su - taara

# Clone repository
git clone <repository-url> /home/taara/app
cd /home/taara/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with proper values

# Initialize database
python init_db.py

# Test installation
python test_api.py
```

#### Systemd Service Setup
```bash
# Create web service
sudo tee /etc/systemd/system/taara-web.service << EOF
[Unit]
Description=Taara Monitor Web Service
After=network.target

[Service]
Type=exec
User=taara
Group=taara
WorkingDirectory=/home/taara/app
Environment=PATH=/home/taara/app/venv/bin
ExecStart=/home/taara/app/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create scheduler service
sudo tee /etc/systemd/system/taara-scheduler.service << EOF
[Unit]
Description=Taara Monitor Data Collector
After=network.target

[Service]
Type=exec
User=taara
Group=taara
WorkingDirectory=/home/taara/app
Environment=PATH=/home/taara/app/venv/bin
ExecStart=/home/taara/app/venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable taara-web taara-scheduler
sudo systemctl start taara-web taara-scheduler
```

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/taara
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /home/taara/app/static/;
        expires 1d;
    }
}
```

---

## Configuration Management

### Environment Variables

#### Required Configuration
```bash
# Taara API Credentials
TAARA_PHONE_COUNTRY_CODE=254
TAARA_PHONE_NUMBER=718920243
TAARA_PASSCODE=888344
TAARA_PARTNER_ID=313324693
TAARA_HOTSPOT_ID=596370186

# Database Configuration
DATABASE_URL=sqlite:///./taara_monitoring.db

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
```

#### Advanced Configuration
```bash
# Performance Settings
COLLECTION_INTERVAL=900  # 15 minutes in seconds
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# Security Settings
SECRET_KEY=your-secure-random-key
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database Settings (for PostgreSQL migration)
DATABASE_URL=postgresql://user:password@localhost/taara_monitor

# Monitoring Settings
ENABLE_METRICS=True
METRICS_PORT=9090
```

### Configuration Files

#### Application Configuration
```python
# app/config.py
import os
from typing import Optional

class Settings:
    # Taara API Settings
    TAARA_PHONE_COUNTRY_CODE: str = os.getenv("TAARA_PHONE_COUNTRY_CODE", "254")
    TAARA_PHONE_NUMBER: str = os.getenv("TAARA_PHONE_NUMBER", "")
    TAARA_PASSCODE: str = os.getenv("TAARA_PASSCODE", "")
    TAARA_PARTNER_ID: str = os.getenv("TAARA_PARTNER_ID", "")
    TAARA_HOTSPOT_ID: str = os.getenv("TAARA_HOTSPOT_ID", "")
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./taara_monitoring.db")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Collection Settings
    COLLECTION_INTERVAL: int = int(os.getenv("COLLECTION_INTERVAL", "900"))
    
settings = Settings()
```

---

## Service Management

### Docker Operations

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f app
docker-compose logs -f scheduler

# Update deployment
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Scale services (if needed)
docker-compose up -d --scale app=2
```

### Systemd Operations

```bash
# Service status
sudo systemctl status taara-web
sudo systemctl status taara-scheduler

# Start/Stop services
sudo systemctl start taara-web
sudo systemctl stop taara-web
sudo systemctl restart taara-web

# Enable/Disable services
sudo systemctl enable taara-web
sudo systemctl disable taara-web

# View service logs
sudo journalctl -u taara-web -f
sudo journalctl -u taara-scheduler -f
```

### Health Checks

#### Automated Health Check Script
```bash
#!/bin/bash
# /opt/scripts/taara-health-check.sh

echo "=== Taara Monitor Health Check ==="
echo "Time: $(date)"
echo

# Check web service
echo "1. Web Service Status:"
if curl -s http://localhost:8000/api/data > /dev/null; then
    echo "   ✅ Web service is responding"
else
    echo "   ❌ Web service is not responding"
fi

# Check database
echo "2. Database Status:"
if [ -f "/home/taara/app/taara_monitoring.db" ]; then
    echo "   ✅ Database file exists"
    record_count=$(sqlite3 /home/taara/app/taara_monitoring.db "SELECT COUNT(*) FROM data_usage_records;")
    echo "   📊 Records in database: $record_count"
else
    echo "   ❌ Database file not found"
fi

# Check recent data collection
echo "3. Data Collection Status:"
last_record=$(sqlite3 /home/taara/app/taara_monitoring.db "SELECT timestamp FROM data_usage_records ORDER BY timestamp DESC LIMIT 1;")
if [ ! -z "$last_record" ]; then
    echo "   ✅ Last data collection: $last_record"
else
    echo "   ❌ No data records found"
fi

# Check disk space
echo "4. Disk Space:"
disk_usage=$(df -h / | awk 'NR==2{print $5}')
echo "   💾 Disk usage: $disk_usage"

# Check memory usage
echo "5. Memory Usage:"
memory_usage=$(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
echo "   🧠 Memory usage: $memory_usage"

echo
echo "=== Health Check Complete ==="
```

---

## Monitoring and Maintenance

### System Monitoring

#### Log File Monitoring
```bash
# Monitor application logs
tail -f /home/taara/app/taara_scheduler.log

# Monitor system logs
sudo journalctl -u taara-web -f
sudo journalctl -u taara-scheduler -f

# Check for errors
grep -i error /home/taara/app/taara_scheduler.log
grep -i error /var/log/nginx/error.log
```

#### Performance Monitoring
```bash
# Monitor system resources
htop
iotop
netstat -tuln

# Monitor disk usage
df -h
du -sh /home/taara/app/

# Monitor database size
ls -lh /home/taara/app/taara_monitoring.db
sqlite3 /home/taara/app/taara_monitoring.db "SELECT COUNT(*) FROM data_usage_records;"
```

### Automated Monitoring Scripts

#### Daily Health Check
```bash
#!/bin/bash
# /etc/cron.daily/taara-health-check

LOGFILE="/var/log/taara-health.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting daily health check" >> $LOGFILE

# Check services
if ! systemctl is-active --quiet taara-web; then
    echo "[$DATE] WARNING: Web service is not running" >> $LOGFILE
    systemctl start taara-web
fi

if ! systemctl is-active --quiet taara-scheduler; then
    echo "[$DATE] WARNING: Scheduler service is not running" >> $LOGFILE
    systemctl start taara-scheduler
fi

# Check database size
DB_SIZE=$(du -m /home/taara/app/taara_monitoring.db | cut -f1)
if [ $DB_SIZE -gt 100 ]; then
    echo "[$DATE] WARNING: Database size is ${DB_SIZE}MB" >> $LOGFILE
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$DATE] WARNING: Disk usage is ${DISK_USAGE}%" >> $LOGFILE
fi

echo "[$DATE] Health check completed" >> $LOGFILE
```

#### Database Maintenance
```bash
#!/bin/bash
# /etc/cron.weekly/taara-db-maintenance

cd /home/taara/app

# Backup database
cp taara_monitoring.db "backups/taara_monitoring_$(date +%Y%m%d).db"

# Vacuum database to optimize
sqlite3 taara_monitoring.db "VACUUM;"

# Remove old backups (keep 4 weeks)
find backups/ -name "taara_monitoring_*.db" -mtime +28 -delete

# Log maintenance
echo "$(date): Database maintenance completed" >> /var/log/taara-maintenance.log
```

---

## Backup and Recovery

### Backup Strategy

#### Automated Backup Script
```bash
#!/bin/bash
# /opt/scripts/taara-backup.sh

BACKUP_DIR="/opt/backups/taara"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/home/taara/app"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp $APP_DIR/taara_monitoring.db $BACKUP_DIR/database_$DATE.db

# Backup configuration
cp $APP_DIR/.env $BACKUP_DIR/config_$DATE.env

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz $APP_DIR/*.log

# Create full backup
tar -czf $BACKUP_DIR/full_backup_$DATE.tar.gz \
    --exclude=$APP_DIR/venv \
    --exclude=$APP_DIR/__pycache__ \
    $APP_DIR

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "$(date): Backup completed to $BACKUP_DIR" >> /var/log/taara-backup.log
```

#### Schedule Backups
```bash
# Add to crontab
sudo crontab -e

# Backup every 6 hours
0 */6 * * * /opt/scripts/taara-backup.sh

# Daily backup at 2 AM
0 2 * * * /opt/scripts/taara-backup.sh
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop services
sudo systemctl stop taara-web taara-scheduler

# Restore database from backup
cp /opt/backups/taara/database_YYYYMMDD_HHMMSS.db /home/taara/app/taara_monitoring.db

# Fix permissions
sudo chown taara:taara /home/taara/app/taara_monitoring.db

# Start services
sudo systemctl start taara-web taara-scheduler

# Verify recovery
curl http://localhost:8000/api/data
```

#### Full System Recovery
```bash
# Prepare new system
sudo useradd -r -m -s /bin/bash taara
sudo apt install -y python3 python3-pip python3-venv

# Extract full backup
cd /home/taara
sudo tar -xzf /opt/backups/taara/full_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore virtual environment
cd /home/taara/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Restore services
sudo cp /path/to/service/files/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable taara-web taara-scheduler
sudo systemctl start taara-web taara-scheduler
```

---

## Security Considerations

### Network Security

#### Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to app port
```

#### SSL/TLS Configuration
```nginx
# Nginx SSL configuration
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/taara.crt;
    ssl_certificate_key /etc/ssl/private/taara.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Application Security

#### Environment Security
```bash
# Secure .env file
sudo chmod 600 /home/taara/app/.env
sudo chown taara:taara /home/taara/app/.env

# Secure database file
sudo chmod 600 /home/taara/app/taara_monitoring.db
sudo chown taara:taara /home/taara/app/taara_monitoring.db
```

#### Access Control
```bash
# Restrict application directory
sudo chmod 750 /home/taara/app
sudo chown -R taara:taara /home/taara/app

# Create log directory with proper permissions
sudo mkdir -p /var/log/taara
sudo chown taara:taara /var/log/taara
sudo chmod 755 /var/log/taara
```

---

## Performance Optimization

### Database Optimization

#### SQLite Optimization
```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

-- Optimize cache size
PRAGMA cache_size=10000;

-- Enable memory mapping
PRAGMA mmap_size=268435456;

-- Analyze tables for query optimization
ANALYZE;
```

#### Database Maintenance
```bash
# Regular vacuum to optimize database
sqlite3 /home/taara/app/taara_monitoring.db "VACUUM;"

# Analyze for query optimization
sqlite3 /home/taara/app/taara_monitoring.db "ANALYZE;"

# Check database integrity
sqlite3 /home/taara/app/taara_monitoring.db "PRAGMA integrity_check;"
```

### Application Optimization

#### Python Optimizations
```python
# Use connection pooling for database
from sqlalchemy.pool import StaticPool

engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300
)
```

#### Caching Strategy
```python
# Implement caching for frequent queries
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_latest_stats():
    # Cache stats for 5 minutes
    return calculate_usage_stats()
```

### System Optimization

#### Memory Management
```bash
# Monitor memory usage
free -h
ps aux --sort=-%mem | head

# Optimize swap usage
echo "vm.swappiness=10" >> /etc/sysctl.conf
```

#### Disk I/O Optimization
```bash
# Monitor disk I/O
iotop

# Optimize SQLite for SSD
echo "PRAGMA journal_mode=WAL;" | sqlite3 /home/taara/app/taara_monitoring.db
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Service Won't Start
```bash
# Check service status
sudo systemctl status taara-web

# Check logs for errors
sudo journalctl -u taara-web -n 50

# Common fixes:
# 1. Check if port is already in use
sudo netstat -tulpn | grep :8000

# 2. Verify Python environment
cd /home/taara/app
source venv/bin/activate
python -c "import app.main"

# 3. Check permissions
ls -la /home/taara/app/
```

#### Issue 2: Database Connection Errors
```bash
# Check database file
ls -la /home/taara/app/taara_monitoring.db

# Test database connection
sqlite3 /home/taara/app/taara_monitoring.db "SELECT COUNT(*) FROM data_usage_records;"

# Fix common issues:
# 1. File permissions
sudo chown taara:taara /home/taara/app/taara_monitoring.db
sudo chmod 644 /home/taara/app/taara_monitoring.db

# 2. Database corruption
cp /home/taara/app/taara_monitoring.db /home/taara/app/taara_monitoring.db.backup
sqlite3 /home/taara/app/taara_monitoring.db ".dump" | sqlite3 /home/taara/app/taara_monitoring_new.db
mv /home/taara/app/taara_monitoring_new.db /home/taara/app/taara_monitoring.db
```

#### Issue 3: API Connection Problems
```bash
# Test API connectivity
cd /home/taara/app
source venv/bin/activate
python test_api.py

# Check environment variables
cat .env | grep TAARA

# Test network connectivity
ping api.taara.co.ke
curl -v https://api.taara.co.ke/

# Common fixes:
# 1. Update credentials
nano .env

# 2. Check firewall rules
sudo ufw status

# 3. Verify DNS resolution
nslookup api.taara.co.ke
```

### Diagnostic Commands

#### System Information
```bash
# System status overview
/opt/scripts/taara-health-check.sh

# Resource usage
top -p $(pgrep -f "taara")
df -h
free -h

# Network status
ss -tulpn | grep :8000
ping -c 3 api.taara.co.ke

# Service logs
sudo journalctl -u taara-web --since "1 hour ago"
sudo journalctl -u taara-scheduler --since "1 hour ago"
```

#### Application Diagnostics
```bash
# Test individual components
cd /home/taara/app
source venv/bin/activate

# Test API client
python -c "from app.taara_api import TaaraAPI; print('API module OK')"

# Test database
python -c "from app.database import SessionLocal; SessionLocal().execute('SELECT 1'); print('Database OK')"

# Test data collector
python -c "from app.data_collector import DataCollector; print('Collector OK')"

# Test web application
python -c "from app.main import app; print('Web app OK')"
```

---

## Automated Management

### Monitoring Scripts

#### System Monitor
```bash
#!/bin/bash
# /opt/scripts/taara-monitor.sh

# Configuration
ALERT_EMAIL="admin@example.com"
LOG_FILE="/var/log/taara-monitor.log"
THRESHOLD_DISK=80
THRESHOLD_MEMORY=90

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> $LOG_FILE
}

check_services() {
    for service in taara-web taara-scheduler; do
        if ! systemctl is-active --quiet $service; then
            log_message "ERROR: $service is not running"
            systemctl start $service
            log_message "INFO: Attempted to restart $service"
        fi
    done
}

check_resources() {
    # Check disk usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt $THRESHOLD_DISK ]; then
        log_message "WARNING: Disk usage is ${DISK_USAGE}%"
    fi
    
    # Check memory usage
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $MEMORY_USAGE -gt $THRESHOLD_MEMORY ]; then
        log_message "WARNING: Memory usage is ${MEMORY_USAGE}%"
    fi
}

check_api_connectivity() {
    if ! curl -s http://localhost:8000/api/data > /dev/null; then
        log_message "ERROR: API endpoint not responding"
    fi
}

# Run checks
check_services
check_resources
check_api_connectivity

log_message "INFO: Monitoring check completed"
```

#### Auto-Update Script
```bash
#!/bin/bash
# /opt/scripts/taara-update.sh

APP_DIR="/home/taara/app"
BACKUP_DIR="/opt/backups/taara"
DATE=$(date +%Y%m%d_%H%M%S)

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a /var/log/taara-update.log
}

# Backup before update
log_message "Starting backup before update"
/opt/scripts/taara-backup.sh

# Stop services
log_message "Stopping services"
sudo systemctl stop taara-web taara-scheduler

# Update code
log_message "Updating application code"
cd $APP_DIR
git fetch origin
git checkout main
git pull origin main

# Update dependencies
log_message "Updating dependencies"
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations if needed
if [ -f "migrations.py" ]; then
    log_message "Running database migrations"
    python migrations.py
fi

# Start services
log_message "Starting services"
sudo systemctl start taara-web taara-scheduler

# Verify deployment
sleep 10
if curl -s http://localhost:8000/api/data > /dev/null; then
    log_message "Update completed successfully"
else
    log_message "ERROR: Update failed, service not responding"
    # Rollback logic here if needed
fi
```

### Cron Jobs Setup

```bash
# Edit crontab for automated tasks
sudo crontab -e

# Add these entries:

# Health check every 15 minutes
*/15 * * * * /opt/scripts/taara-monitor.sh

# Backup every 6 hours
0 */6 * * * /opt/scripts/taara-backup.sh

# Database maintenance weekly
0 2 * * 0 /opt/scripts/taara-db-maintenance.sh

# Log rotation daily
0 1 * * * /usr/sbin/logrotate /etc/logrotate.d/taara

# Health report daily at 8 AM
0 8 * * * /opt/scripts/taara-health-check.sh | mail -s "Taara Monitor Daily Report" admin@example.com
```

---

This comprehensive system administration guide covers all aspects of deploying, configuring, and maintaining the Taara Internet Monitor system. Regular reference to this guide will ensure smooth operation and optimal performance of the monitoring system.
