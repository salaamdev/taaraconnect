# 🌐 Taara Internet Monitor

Production-grade internet usage monitoring system with Taara API integration.

## 🚀 Quick Deploy

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Taara credentials

# 2. Deploy to production
make deploy

# 3. Access dashboard
# http://your-server-ip
```

## 📋 Available Commands

```bash
make help      # Show all commands
make install   # Setup system (first time only)
make deploy    # Deploy application
make start     # Start services
make stop      # Stop services
make restart   # Restart services
make logs      # View logs
make backup    # Backup data
make verify    # Check system health
make clean     # Clean up
```

## 🔧 Requirements

- **Taara API Account** (phone number + passcode)
- **Linux VPS** (Ubuntu 20.04+ recommended)
- **Docker** (auto-installed with `make install`)

## 📊 Features

- ✅ Real-time usage monitoring
- ✅ Web dashboard
- ✅ Historical data tracking
- ✅ Automated backups
- ✅ Production-ready Docker setup
- ✅ SSL/HTTPS ready
- ✅ Health monitoring

## 🔒 Security

- Environment variables properly secured
- Docker containers run as non-root
- Firewall configured automatically
- SSL/TLS encryption ready
- Rate limiting enabled

## 📱 API Endpoints

- `GET /` - Dashboard
- `GET /api/usage` - Current usage
- `GET /api/history` - Historical data
- `GET /health` - Health check

## 🛠️ Manual Setup

If you prefer manual setup instead of `make install`:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Deploy
docker-compose up -d
```

## 📈 Monitoring

The system includes built-in monitoring:

- Application health checks
- Database backup automation
- Log rotation
- Performance metrics

Built with ❤️ for production environments.
