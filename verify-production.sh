#!/bin/bash
# Production Readiness Verification for Taara Internet Monitor

set -e

echo "🔍 Production Readiness Verification"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

errors=0
warnings=0

# Check .env file
echo "🔐 Environment Configuration:"
if [ -f ".env" ]; then
    if [ "$(stat -c %a .env)" = "600" ]; then
        print_success ".env file exists with secure permissions"
    else
        print_warning ".env file permissions should be 600"
        warnings=$((warnings + 1))
    fi
    
    # Check for real credentials
    if grep -q "718920243" .env && grep -q "888344" .env; then
        print_success "Real Taara credentials configured"
    else
        print_error "Taara credentials not properly configured"
        errors=$((errors + 1))
    fi
    
    # Check for secure secrets
    if grep -q "S9oVNylB8G1QM2q4Au7HRWicE1QG0EXBtd-YQB82q4I" .env; then
        print_success "Production secrets configured"
    else
        print_warning "Production secrets may not be configured"
        warnings=$((warnings + 1))
    fi
else
    print_error ".env file not found"
    errors=$((errors + 1))
fi

echo ""

# Check Docker files
echo "🐳 Docker Configuration:"
if [ -f "Dockerfile" ]; then
    if grep -q "gunicorn" Dockerfile; then
        print_success "Production Dockerfile with Gunicorn"
    else
        print_warning "Dockerfile may not be production-optimized"
        warnings=$((warnings + 1))
    fi
else
    print_error "Dockerfile not found"
    errors=$((errors + 1))
fi

if [ -f "docker-compose.yml" ]; then
    if grep -q "production" docker-compose.yml; then
        print_success "Production docker-compose.yml configured"
    else
        print_warning "docker-compose.yml may not be production-ready"
        warnings=$((warnings + 1))
    fi
else
    print_error "docker-compose.yml not found"
    errors=$((errors + 1))
fi

echo ""

# Check Nginx configuration
echo "⚡ Nginx Configuration:"
if [ -f "nginx/nginx.conf" ]; then
    if grep -q "gzip on" nginx/nginx.conf && grep -q "ssl_protocols" nginx/nginx.conf; then
        print_success "Production Nginx configuration"
    else
        print_warning "Nginx configuration may need optimization"
        warnings=$((warnings + 1))
    fi
else
    print_error "Nginx configuration not found"
    errors=$((errors + 1))
fi

echo ""

# Check deployment scripts
echo "🚀 Deployment Scripts:"
scripts=("deploy-vps.sh" "backup.sh" "monitor.sh")
for script in "${scripts[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        print_success "$script is ready"
    else
        print_error "$script not found or not executable"
        errors=$((errors + 1))
    fi
done

echo ""

# Check gitignore
echo "🔒 Security Files:"
if [ -f ".gitignore" ]; then
    if grep -q ".env" .gitignore; then
        print_success ".gitignore properly configured"
    else
        print_error ".gitignore doesn't exclude .env files"
        errors=$((errors + 1))
    fi
else
    print_error ".gitignore not found"
    errors=$((errors + 1))
fi

echo ""

# Check SSL certificates
echo "🔐 SSL Certificates:"
if [ -f "nginx/ssl/cert.pem" ] && [ -f "nginx/ssl/key.pem" ]; then
    print_success "SSL certificates present"
    print_warning "Replace with real certificates for production"
    warnings=$((warnings + 1))
else
    print_error "SSL certificates not found"
    errors=$((errors + 1))
fi

echo ""

# Check directories
echo "📁 Directory Structure:"
dirs=("data" "logs" "backups")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_success "$dir directory exists"
    else
        print_warning "$dir directory missing (will be created)"
        warnings=$((warnings + 1))
    fi
done

echo ""

# Final assessment
echo "📊 Production Readiness Assessment:"
echo "=================================="

if [ $errors -eq 0 ] && [ $warnings -le 2 ]; then
    print_success "🎉 PRODUCTION READY!"
    echo ""
    echo "Your Taara Internet Monitor is ready for VPS deployment."
    echo ""
    echo "Next steps:"
    echo "1. Upload files to VPS: scp -r . user@vps-ip:/opt/taara/"
    echo "2. Run deployment: sudo ./deploy-vps.sh"
    echo "3. Configure domain name in .env"
    echo "4. Set up SSL certificates"
    echo ""
elif [ $errors -eq 0 ]; then
    print_warning "MOSTLY READY with $warnings warnings"
    echo ""
    echo "Address warnings above before production deployment."
    echo ""
else
    print_error "NOT READY - $errors errors, $warnings warnings"
    echo ""
    echo "Fix errors above before deployment."
    echo ""
    exit 1
fi

echo "🔧 Production secrets summary:"
echo "• SECRET_KEY: S9oVNylB8G1QM2q4Au7HRWicE1QG0EXBtd-YQB82q4I"
echo "• JWT_SECRET_KEY: GfvmYFZV1eLHfJaOYEQKW3mjK-vrG4b18aCh-OcsM8A"
echo "• ENCRYPTION_KEY: z0B0HUosRfFg1F0jMIpIy/vLgIqzYSoZfd0bCAJWQMQ="
echo "• API_TOKEN: LD7P74qevZvFtnrkzFK_JP2MCh1P4bvxRnCAsV5Y0qfw-Z0BK0xtPiWQxNQwp29Z"
echo ""
echo "💾 Save these secrets securely - they're already in your .env file!"
echo ""

if [ $errors -eq 0 ]; then
    echo "🚀 Ready to deploy to VPS!"
fi
