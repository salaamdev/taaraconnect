# Taara Internet Monitor

Production-ready internet data usage monitoring system for Taara internet subscribers.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Valid Taara internet subscription

### 1. Configure Environment

**Option A: Interactive Setup (Recommended)**
```bash
./setup-env.sh
```

**Option B: Manual Setup**
```bash
cp .env.example .env
# Edit .env with your Taara credentials
```

### 2. Deploy
```bash
docker-compose up -d
```

### 3. Access
- **HTTPS**: https://localhost
- **HTTP**: http://localhost

## 🔧 Configuration

Edit `.env` with your credentials:
```bash
TAARA_PHONE_COUNTRY_CODE=254
TAARA_PHONE_NUMBER=your_phone_number
TAARA_PASSCODE=your_passcode
TAARA_PARTNER_ID=your_partner_id
TAARA_HOTSPOT_ID=your_hotspot_id
```

## 📊 Features

- Automated data collection (15-min intervals)
- Real-time web dashboard
- Responsive design
- Docker containerized
- HTTPS with Nginx
- Persistent SQLite database

## 📋 Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Check status
docker-compose ps
```
