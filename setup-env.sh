#!/bin/bash
# Taara Internet Monitor - Environment Setup Script
# This script helps you set up your .env file securely

set -e

echo "🔧 Taara Internet Monitor - Environment Setup"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Function to generate secure random string
generate_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local variable="$3"
    
    if [ -n "$default" ]; then
        echo -n "$prompt [$default]: "
    else
        echo -n "$prompt: "
    fi
    
    read -r input
    if [ -z "$input" ] && [ -n "$default" ]; then
        input="$default"
    fi
    
    eval "$variable='$input'"
}

# Function to prompt for sensitive input (hidden)
prompt_sensitive() {
    local prompt="$1"
    local variable="$2"
    
    echo -n "$prompt: "
    read -s input
    echo ""
    eval "$variable='$input'"
}

# Check if .env already exists
if [ -f ".env" ]; then
    print_warning ".env file already exists!"
    echo -n "Do you want to overwrite it? [y/N]: "
    read -r confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Setup cancelled. Existing .env file preserved."
        exit 0
    fi
    echo ""
fi

# Check if .env.example exists
if [ ! -f ".env.example" ]; then
    print_error ".env.example not found! Please run this script from the project root."
    exit 1
fi

print_info "Setting up your environment configuration..."
echo ""

# =============================================================================
# TAARA API CREDENTIALS
# =============================================================================
echo "📡 Taara API Credentials"
echo "========================"
print_info "You can find these credentials in your Taara account dashboard."
echo ""

prompt_with_default "Phone country code" "254" "PHONE_COUNTRY_CODE"
prompt_with_default "Phone number (without country code)" "" "PHONE_NUMBER"
prompt_sensitive "Passcode/PIN" "PASSCODE"
prompt_with_default "Partner ID" "" "PARTNER_ID"
prompt_with_default "Hotspot ID" "" "HOTSPOT_ID"

echo ""

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
echo "⚙️  Application Settings"
echo "======================="

prompt_with_default "Environment (production/development)" "production" "ENVIRONMENT"
prompt_with_default "Debug mode (true/false)" "false" "DEBUG"
prompt_with_default "Log level (DEBUG/INFO/WARNING/ERROR)" "INFO" "LOG_LEVEL"

echo ""

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
echo "🔐 Security Settings"
echo "==================="
print_info "Generating secure random keys..."

SECRET_KEY=$(generate_secret)
JWT_SECRET_KEY=$(generate_secret)

print_success "Generated SECRET_KEY: ${SECRET_KEY:0:16}..."
print_success "Generated JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:16}..."

prompt_with_default "Allowed hosts (comma-separated)" "localhost,127.0.0.1" "ALLOWED_HOSTS"

echo ""

# =============================================================================
# DATA COLLECTION SETTINGS
# =============================================================================
echo "📊 Data Collection Settings"
echo "==========================="

prompt_with_default "Collection interval (seconds)" "900" "COLLECTION_INTERVAL"
prompt_with_default "Scraping interval (minutes)" "15" "SCRAPING_INTERVAL_MINUTES"
prompt_with_default "Max retries" "3" "MAX_RETRIES"
prompt_with_default "Timeout (seconds)" "30" "TIMEOUT_SECONDS"

echo ""

# =============================================================================
# OPTIONAL SERVICES
# =============================================================================
echo "📧 Optional Services"
echo "==================="
echo -n "Do you want to configure email notifications? [y/N]: "
read -r setup_email

EMAIL_SMTP_HOST=""
EMAIL_SMTP_PORT="587"
EMAIL_USERNAME=""
EMAIL_PASSWORD=""
EMAIL_FROM=""

if [[ $setup_email =~ ^[Yy]$ ]]; then
    prompt_with_default "SMTP host" "smtp.gmail.com" "EMAIL_SMTP_HOST"
    prompt_with_default "SMTP port" "587" "EMAIL_SMTP_PORT"
    prompt_with_default "Email username" "" "EMAIL_USERNAME"
    prompt_sensitive "Email password (app password)" "EMAIL_PASSWORD"
    prompt_with_default "From email address" "$EMAIL_USERNAME" "EMAIL_FROM"
fi

echo ""
echo -n "Do you want to configure webhook notifications? [y/N]: "
read -r setup_webhook

WEBHOOK_URL=""
WEBHOOK_SECRET=""

if [[ $setup_webhook =~ ^[Yy]$ ]]; then
    prompt_with_default "Webhook URL" "" "WEBHOOK_URL"
    if [ -n "$WEBHOOK_URL" ]; then
        WEBHOOK_SECRET=$(generate_secret)
        print_success "Generated webhook secret: ${WEBHOOK_SECRET:0:16}..."
    fi
fi

# =============================================================================
# CREATE .ENV FILE
# =============================================================================
echo ""
print_info "Creating .env file..."

cat > .env << EOF
# Taara Internet Monitor - Production Configuration
# DO NOT COMMIT THIS FILE TO PUBLIC REPOSITORY
# Generated on $(date)

# =============================================================================
# TAARA API CREDENTIALS (REQUIRED)
# =============================================================================
TAARA_PHONE_COUNTRY_CODE=$PHONE_COUNTRY_CODE
TAARA_PHONE_NUMBER=$PHONE_NUMBER
TAARA_PASSCODE=$PASSCODE
TAARA_PARTNER_ID=$PARTNER_ID
TAARA_HOTSPOT_ID=$HOTSPOT_ID

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL=sqlite:///./data/taara_monitoring.db

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
DEBUG=$DEBUG
LOG_LEVEL=$LOG_LEVEL
ENVIRONMENT=$ENVIRONMENT

# Application Security
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
ENCRYPTION_KEY=

# =============================================================================
# DATA COLLECTION SETTINGS
# =============================================================================
COLLECTION_INTERVAL=$COLLECTION_INTERVAL
SCRAPING_INTERVAL_MINUTES=$SCRAPING_INTERVAL_MINUTES
MAX_RETRIES=$MAX_RETRIES
TIMEOUT_SECONDS=$TIMEOUT_SECONDS

# API Rate Limiting
API_RATE_LIMIT=100
API_BURST_LIMIT=20

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
ALLOWED_HOSTS=$ALLOWED_HOSTS
CORS_ORIGINS=https://localhost,https://127.0.0.1

# SSL/TLS Configuration
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
SSL_VERIFY=True

# Security Headers
ENABLE_SECURITY_HEADERS=True
HSTS_MAX_AGE=31536000
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com cdn.plot.ly; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com;"

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================
WORKERS=1
MAX_CONNECTIONS=100
CONNECTION_TIMEOUT=30
KEEPALIVE_TIMEOUT=65

# Cache Settings
ENABLE_CACHE=True
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# =============================================================================
# MONITORING & LOGGING
# =============================================================================
ENABLE_HEALTH_CHECK=True
HEALTH_CHECK_INTERVAL=60
HEALTH_CHECK_TIMEOUT=10

# Logging Configuration
LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE_MAX_SIZE=10485760
LOG_FILE_BACKUP_COUNT=5

# Metrics & Analytics
ENABLE_METRICS=True
METRICS_ENDPOINT=/metrics
ENABLE_REQUEST_LOGGING=True

# =============================================================================
# EXTERNAL SERVICES
# =============================================================================
# Email Notifications
EMAIL_SMTP_HOST=$EMAIL_SMTP_HOST
EMAIL_SMTP_PORT=$EMAIL_SMTP_PORT
EMAIL_USERNAME=$EMAIL_USERNAME
EMAIL_PASSWORD=$EMAIL_PASSWORD
EMAIL_FROM=$EMAIL_FROM
EMAIL_TLS=True

# Webhook Notifications
WEBHOOK_URL=$WEBHOOK_URL
WEBHOOK_SECRET=$WEBHOOK_SECRET

# Third-party API Keys
SENTRY_DSN=
ANALYTICS_API_KEY=

# =============================================================================
# DOCKER & DEPLOYMENT
# =============================================================================
DOCKER_IMAGE_TAG=latest
CONTAINER_NAME=taara-monitor
DOCKER_NETWORK=taara-network

# Health Check URLs
HEALTH_CHECK_URL=http://localhost:8000/api/data
EXTERNAL_HEALTH_CHECK_URL=

# =============================================================================
# BACKUP & MAINTENANCE
# =============================================================================
BACKUP_ENABLED=True
BACKUP_INTERVAL=86400
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE_PATH=/app/backups

# Database Maintenance
AUTO_VACUUM_ENABLED=True
AUTO_VACUUM_INTERVAL=604800

# =============================================================================
# FEATURE FLAGS
# =============================================================================
ENABLE_API_DOCS=False
ENABLE_DEBUG_ROUTES=False
ENABLE_MAINTENANCE_MODE=False
ENABLE_RATE_LIMITING=True

# Experimental Features
ENABLE_REAL_TIME_UPDATES=False
ENABLE_ADVANCED_ANALYTICS=False
ENABLE_MOBILE_APP_API=False
EOF

# Set secure permissions
chmod 600 .env

print_success ".env file created successfully!"
echo ""

# =============================================================================
# VALIDATION
# =============================================================================
print_info "Validating configuration..."

# Check required fields
errors=0

if [ -z "$PHONE_NUMBER" ]; then
    print_error "TAARA_PHONE_NUMBER is required!"
    errors=$((errors + 1))
fi

if [ -z "$PASSCODE" ]; then
    print_error "TAARA_PASSCODE is required!"
    errors=$((errors + 1))
fi

if [ -z "$PARTNER_ID" ]; then
    print_error "TAARA_PARTNER_ID is required!"
    errors=$((errors + 1))
fi

if [ -z "$HOTSPOT_ID" ]; then
    print_error "TAARA_HOTSPOT_ID is required!"
    errors=$((errors + 1))
fi

if [ $errors -eq 0 ]; then
    print_success "Configuration validation passed!"
else
    print_warning "$errors validation error(s) found. Please edit .env to fix them."
fi

echo ""

# =============================================================================
# FINAL INSTRUCTIONS
# =============================================================================
echo "🎉 Setup Complete!"
echo "=================="
echo ""
print_info "Your .env file has been created with secure permissions (600)."
echo ""
echo "📋 Next Steps:"
echo "1. Review and edit .env if needed: nano .env"
echo "2. Start the application: docker-compose up -d"
echo "3. Check the logs: docker-compose logs -f"
echo "4. Access the dashboard: https://localhost"
echo ""
print_warning "Security Reminders:"
echo "• Never commit the .env file to version control"
echo "• Keep your credentials secure and private"
echo "• Regularly rotate your secrets in production"
echo "• Use different credentials for different environments"
echo ""
print_info "For help, see ENVIRONMENT_SETUP.md or create an issue."
echo ""

# Optional: Start the application
if command -v docker-compose >/dev/null 2>&1; then
    echo -n "Do you want to start the application now? [y/N]: "
    read -r start_app
    if [[ $start_app =~ ^[Yy]$ ]]; then
        print_info "Starting Taara Internet Monitor..."
        docker-compose up -d
        echo ""
        print_success "Application started! Access it at https://localhost"
        print_info "View logs with: docker-compose logs -f"
    fi
else
    print_warning "Docker Compose not found. Install it to run the application."
fi
