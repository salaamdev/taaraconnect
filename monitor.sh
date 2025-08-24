#!/bin/bash
# Production Monitoring Script for Taara Internet Monitor

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🔍 Taara Internet Monitor - Production Health Check"
echo "================================================="
echo ""

# System Information
print_info "System Information:"
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Disk Usage: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo "Memory Usage: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo ""

# Docker Status
print_info "Docker Status:"
if systemctl is-active --quiet docker; then
    print_success "Docker service is running"
else
    print_error "Docker service is not running"
    exit 1
fi

# Container Status
print_info "Container Status:"
containers=(taara-web-prod taara-scheduler-prod taara-nginx-prod taara-backup-prod)

for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not found")
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no health check")
        
        if [ "$status" = "running" ]; then
            if [ "$health" = "healthy" ] || [ "$health" = "no health check" ]; then
                print_success "$container: $status ($health)"
            else
                print_warning "$container: $status ($health)"
            fi
        else
            print_error "$container: $status"
        fi
    else
        print_error "$container: not found"
    fi
done
echo ""

# API Health Check
print_info "API Health Check:"
API_URL="http://localhost:8000/api/data"
if curl -sf "$API_URL" > /dev/null 2>&1; then
    response_time=$(curl -o /dev/null -s -w '%{time_total}' "$API_URL")
    print_success "API is responding (${response_time}s response time)"
    
    # Check if data is being collected
    data_count=$(curl -s "$API_URL" | jq length 2>/dev/null || echo "0")
    if [ "$data_count" -gt 0 ]; then
        print_success "Data collection is active ($data_count recent records)"
    else
        print_warning "No recent data found - check Taara credentials"
    fi
else
    print_error "API is not responding at $API_URL"
fi

# Web Interface Check
print_info "Web Interface Check:"
WEB_URL="http://localhost"
if curl -sf "$WEB_URL" > /dev/null 2>&1; then
    print_success "Web interface is accessible"
else
    print_warning "Web interface check failed"
fi

# HTTPS Check
HTTPS_URL="https://localhost"
if curl -sfk "$HTTPS_URL" > /dev/null 2>&1; then
    print_success "HTTPS interface is accessible"
else
    print_warning "HTTPS interface check failed"
fi
echo ""

# Database Status
print_info "Database Status:"
DB_PATH="./data/taara_monitoring.db"
if [ -f "$DB_PATH" ]; then
    db_size=$(ls -lh "$DB_PATH" | awk '{print $5}')
    print_success "Database file exists ($db_size)"
    
    # Check database accessibility
    if docker exec taara-web-prod python -c "
from app.database import SessionLocal, DataUsageRecord
from sqlalchemy import func
try:
    session = SessionLocal()
    count = session.query(func.count(DataUsageRecord.id)).scalar()
    print(f'Total records: {count}')
    session.close()
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
" 2>/dev/null; then
        print_success "Database is accessible"
    else
        print_error "Database connection failed"
    fi
else
    print_error "Database file not found at $DB_PATH"
fi
echo ""

# Log Analysis
print_info "Recent Log Analysis (last 50 lines):"
log_errors=$(docker-compose logs --tail=50 2>/dev/null | grep -i "error\|critical\|exception" | wc -l)
log_warnings=$(docker-compose logs --tail=50 2>/dev/null | grep -i "warning\|warn" | wc -l)

if [ "$log_errors" -eq 0 ]; then
    print_success "No recent errors in logs"
else
    print_warning "$log_errors recent errors found in logs"
fi

if [ "$log_warnings" -eq 0 ]; then
    print_success "No recent warnings in logs"
else
    print_info "$log_warnings recent warnings found in logs"
fi

# Resource Usage
print_info "Container Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -5
echo ""

# Backup Status
print_info "Backup Status:"
BACKUP_DIR="./backups"
if [ -d "$BACKUP_DIR" ]; then
    latest_backup=$(ls -t "$BACKUP_DIR" | head -1)
    if [ -n "$latest_backup" ]; then
        backup_age=$(stat -c %Y "$BACKUP_DIR/$latest_backup" 2>/dev/null || echo "0")
        current_time=$(date +%s)
        age_hours=$(( (current_time - backup_age) / 3600 ))
        
        if [ "$age_hours" -lt 25 ]; then
            print_success "Latest backup: $latest_backup (${age_hours}h ago)"
        else
            print_warning "Latest backup is ${age_hours}h old: $latest_backup"
        fi
    else
        print_warning "No backups found"
    fi
else
    print_warning "Backup directory not found"
fi
echo ""

# Security Check
print_info "Security Check:"
# Check if .env file has proper permissions
if [ -f ".env" ]; then
    env_perms=$(stat -c %a .env)
    if [ "$env_perms" = "600" ]; then
        print_success ".env file has secure permissions (600)"
    else
        print_warning ".env file permissions: $env_perms (should be 600)"
    fi
else
    print_error ".env file not found"
fi

# Network Security
if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        print_success "UFW firewall is active"
    else
        print_warning "UFW firewall is not active"
    fi
fi
echo ""

# Summary
print_info "Health Check Summary:"
echo "✅ Run this script regularly to monitor your Taara Monitor instance"
echo "⚠️  Address any warnings or errors found above"
echo "📊 Check logs with: docker-compose logs -f"
echo "🔄 Restart services with: docker-compose restart"
echo ""

# Optional: Send alert if critical issues found
# if [ "$log_errors" -gt 5 ]; then
#     echo "Critical: Multiple errors detected - sending alert"
#     # curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
#     #      -H 'Content-type: application/json' \
#     #      --data '{"text":"Taara Monitor: Multiple errors detected on production server"}'
# fi

echo "Health check completed at $(date)"
