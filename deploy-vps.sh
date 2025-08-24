#!/bin/bash
# Production Deployment Script for Taara Internet Monitor VPS
# Run this script on your VPS to deploy the application

set -e

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

echo "🚀 Taara Internet Monitor - Production VPS Deployment"
echo "====================================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. Consider creating a dedicated user for the application."
fi

# Check system requirements
print_info "Checking system requirements..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    print_success "Docker installed successfully"
else
    print_success "Docker is already installed"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_info "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose is already installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found! Please ensure you have uploaded the .env file to this directory."
    exit 1
fi

# Verify .env permissions
chmod 600 .env
print_success ".env file permissions secured"

# Create required directories
print_info "Creating required directories..."
mkdir -p data logs backups
chmod 755 data logs backups
print_success "Directories created"

# Set up log rotation
print_info "Setting up log rotation..."
cat > /etc/logrotate.d/taara-monitor << 'EOF'
/opt/taara/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
print_success "Log rotation configured"

# Firewall configuration
if command -v ufw &> /dev/null; then
    print_info "Configuring firewall..."
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 22/tcp
    print_success "Firewall configured (ports 80, 443, 22 open)"
else
    print_warning "UFW not found. Please manually configure firewall to allow ports 80, 443"
fi

# Stop existing containers if running
print_info "Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Pull latest images and build
print_info "Building production images..."
docker-compose build --no-cache

# Start services
print_info "Starting production services..."
docker-compose up -d

# Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 30

# Health check
print_info "Performing health checks..."
for i in {1..5}; do
    if curl -sf http://localhost:8000/api/data > /dev/null 2>&1; then
        print_success "API health check passed"
        break
    else
        if [ $i -eq 5 ]; then
            print_error "API health check failed after 5 attempts"
            docker-compose logs app
            exit 1
        fi
        print_warning "API not ready, waiting... (attempt $i/5)"
        sleep 10
    fi
done

# Test NGINX
if curl -sf http://localhost > /dev/null 2>&1; then
    print_success "NGINX health check passed"
else
    print_warning "NGINX health check failed - check SSL configuration"
fi

# Display status
print_info "Checking container status..."
docker-compose ps

# Display logs from the last few minutes
print_info "Recent logs:"
docker-compose logs --tail=20

echo ""
print_success "🎉 Production deployment completed successfully!"
echo ""

# Instructions
echo "📋 Post-deployment steps:"
echo "1. Update your domain DNS to point to this VPS IP address"
echo "2. Configure SSL certificates (replace self-signed certificates in nginx/ssl/)"
echo "3. Update ALLOWED_HOSTS in .env with your domain name"
echo "4. Set up monitoring and alerting"
echo ""

echo "🌐 Access points:"
echo "• HTTP:  http://$(curl -s ifconfig.me || echo 'YOUR_VPS_IP')"
echo "• HTTPS: https://$(curl -s ifconfig.me || echo 'YOUR_VPS_IP')"
echo "• API:   http://$(curl -s ifconfig.me || echo 'YOUR_VPS_IP'):8000"
echo ""

echo "📊 Management commands:"
echo "• View logs:        docker-compose logs -f"
echo "• Restart:          docker-compose restart"
echo "• Stop:             docker-compose down"
echo "• Update:           git pull && docker-compose up -d --build"
echo "• Backup:           ./backup.sh"
echo ""

echo "🔐 Security recommendations:"
echo "1. Set up fail2ban: apt install fail2ban"
echo "2. Configure automatic security updates"
echo "3. Set up SSL certificates with Let's Encrypt"
echo "4. Enable log monitoring"
echo "5. Set up regular database backups"
echo ""

print_warning "Remember to:"
print_warning "• Keep your .env file secure and backed up"
print_warning "• Monitor logs for any issues"
print_warning "• Set up SSL certificates for production use"
print_warning "• Configure your domain name in the .env file"
