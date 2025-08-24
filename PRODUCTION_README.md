# 🚀 Taara Internet Monitor - Production Deployment Guide

Production-ready internet data usage monitoring system for Taara internet subscribers.

## 📦 What's Included

This production setup includes:
- ✅ **Secure environment configuration** with encrypted secrets
- ✅ **Production-optimized Docker images** with multi-stage builds
- ✅ **High-performance Nginx** with caching and security headers
- ✅ **Automated backup system** with retention policies
- ✅ **Health monitoring scripts** for production oversight
- ✅ **VPS deployment automation** with one-command setup

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   FastAPI App   │    │   Scheduler     │
│   (Port 80/443) │───▶│   (Port 8000)   │    │  (Background)   │
│   Load Balancer │    │   Web Dashboard │    │ Data Collection │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   SQLite DB     │◀─────────────┘
         │              │ (Persistent)    │
         │              └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Static Files   │    │ Automated       │
│   (Cached)      │    │ Backup Service  │
└─────────────────┘    └─────────────────┘
```

## 🚀 Quick VPS Deployment

### 1. **Upload Files to VPS**
```bash
# On your local machine, upload the project
scp -r . user@your-vps-ip:/opt/taara/
```

### 2. **Run Production Deployment**
```bash
# On your VPS
cd /opt/taara
chmod +x deploy-vps.sh
sudo ./deploy-vps.sh
```

### 3. **Access Your Application**
- **HTTPS**: `https://your-vps-ip`
- **HTTP**: `http://your-vps-ip` (redirects to HTTPS)

## 🔧 Manual Setup (Alternative)

### Prerequisites
- Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Docker & Docker Compose
- 2GB+ RAM, 20GB+ disk space
- Valid Taara internet subscription

### Installation Steps

1. **Clone and setup:**
```bash
git clone https://github.com/salaamdev/taaraconnect.git
cd taaraconnect
```

2. **Configure environment:**
```bash
# The .env file is already configured with production secrets
# Update domain name if needed:
sed -i 's/your-vps-domain.com/yourdomain.com/g' .env
```

3. **Deploy:**
```bash
docker-compose up -d --build
```

4. **Verify deployment:**
```bash
./monitor.sh
```

## 🔐 Security Features

### Pre-configured Secrets
- ✅ **Cryptographically secure keys** generated using Python's `secrets` module
- ✅ **Real Taara credentials** already configured
- ✅ **File permissions** properly secured (600)
- ✅ **Git exclusion** prevents secret leakage

### Security Hardening
- 🛡️ **Rate limiting** on all endpoints
- 🛡️ **Security headers** (HSTS, CSP, XSS protection)
- 🛡️ **Non-root containers** for minimal attack surface
- 🛡️ **Input validation** and sanitization
- 🛡️ **SSL/TLS encryption** with modern ciphers

## 📊 Production Configuration

### Performance Optimizations
```yaml
# Already configured in .env
WORKERS=2                    # Multi-process handling
MAX_CONNECTIONS=200          # Concurrent connection limit
CACHE_TTL=300               # 5-minute cache for API responses
ENABLE_CACHE=True           # Response caching enabled
```

### Data Collection
```yaml
COLLECTION_INTERVAL=900      # 15-minute collection intervals
MAX_RETRIES=3               # API failure resilience
TIMEOUT_SECONDS=30          # Request timeout protection
```

### Monitoring
```yaml
ENABLE_HEALTH_CHECK=True    # Container health monitoring
ENABLE_METRICS=True         # Performance metrics
LOG_LEVEL=INFO              # Production logging
```

## 📋 Management Commands

### Daily Operations
```bash
# Check system health
./monitor.sh

# View live logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update application
git pull && docker-compose up -d --build
```

### Backup & Recovery
```bash
# Create manual backup
./backup.sh

# Restore from backup
docker-compose down
cp /app/backups/YYYY-MM-DD/taara_monitoring.db.gz ./data/
gunzip ./data/taara_monitoring.db.gz
docker-compose up -d
```

### Troubleshooting
```bash
# Check container status
docker-compose ps

# View container resource usage
docker stats

# Access container shell
docker exec -it taara-web-prod bash

# Reset and rebuild
docker-compose down --volumes
docker-compose up -d --build
```

## 🌐 Domain Configuration

### DNS Setup
1. **Point your domain to VPS IP:**
```bash
# A Record
yourdomain.com    →    YOUR_VPS_IP
www.yourdomain.com →   YOUR_VPS_IP
```

2. **Update configuration:**
```bash
# Edit .env file
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

3. **Restart services:**
```bash
docker-compose restart
```

### SSL Certificate Setup (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Restart nginx
docker-compose start nginx
```

## 📈 Monitoring & Alerts

### Health Monitoring
The production setup includes automated health monitoring:
- **Container health checks** every 30 seconds
- **API endpoint monitoring** with response time tracking
- **Database connectivity verification**
- **Log analysis** for errors and warnings

### Setting Up Alerts
1. **Email alerts** (configure SMTP in .env):
```bash
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_USERNAME=alerts@yourdomain.com
EMAIL_PASSWORD=your-app-password
```

2. **Webhook alerts** (Slack/Discord):
```bash
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Log Management
```bash
# View recent errors
docker-compose logs | grep ERROR

# Monitor in real-time
docker-compose logs -f --tail=100

# Export logs
docker-compose logs > taara-logs-$(date +%Y%m%d).log
```

## 🔧 Advanced Configuration

### Database Scaling
For high-traffic deployments, consider PostgreSQL:
```bash
# Update .env
DATABASE_URL=postgresql://taara:secure_password@postgres:5432/taara_db

# Add PostgreSQL service to docker-compose.yml
```

### Load Balancing
For multiple servers:
```bash
# Use external load balancer (nginx/HAProxy)
# Configure health checks: /health endpoint
# Enable session stickiness if needed
```

### Backup Automation
```bash
# Add to crontab for daily backups
0 2 * * * /opt/taara/backup.sh

# Weekly health checks
0 6 * * 1 /opt/taara/monitor.sh | mail -s "Taara Monitor Health" admin@yourdomain.com
```

## 🆘 Support & Troubleshooting

### Common Issues

1. **"API authentication failed"**
   - Verify Taara credentials in .env
   - Check internet connectivity
   - Confirm account is active

2. **"Container health check failed"**
   - Check logs: `docker-compose logs app`
   - Verify database connectivity
   - Restart services: `docker-compose restart`

3. **"High memory usage"**
   - Monitor with: `docker stats`
   - Adjust WORKERS in .env
   - Enable log rotation

### Performance Tuning
```bash
# For high-traffic sites
WORKERS=4
MAX_CONNECTIONS=500
CACHE_TTL=900

# For low-resource VPS
WORKERS=1
MAX_CONNECTIONS=100
CACHE_TTL=300
```

### Security Hardening
```bash
# Enable fail2ban
sudo apt install fail2ban

# Configure firewall
sudo ufw enable
sudo ufw allow 22,80,443/tcp

# Regular security updates
sudo apt update && sudo apt upgrade -y
```

## 📞 Production Support

- 📧 **Email**: Create an issue in the GitHub repository
- 📊 **Monitoring**: Use the included health check scripts
- 🔄 **Updates**: `git pull && docker-compose up -d --build`
- 🔒 **Security**: Regular updates and monitoring

---

**🎉 Your Taara Internet Monitor is production-ready!**

For additional support, create an issue with:
- System information (`uname -a`)
- Docker version (`docker --version`)
- Container logs (`docker-compose logs`)
- Health check results (`./monitor.sh`)
