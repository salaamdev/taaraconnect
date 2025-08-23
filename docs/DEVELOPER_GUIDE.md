# Taara Internet Monitor - Developer Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Development Environment](#development-environment)
5. [Code Structure](#code-structure)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Monitoring & Logging](#monitoring--logging)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)

---

## System Overview

The Taara Internet Monitor is a comprehensive monitoring system that automatically tracks internet data usage for Taara ISP subscribers. It provides real-time data collection, storage, analysis, and visualization through a web-based dashboard.

### Key Features

- **Automated Data Collection**: Polls Taara API every 10-15 minutes
- **Real-time Dashboard**: Web interface with live charts and statistics
- **RESTful API**: Endpoints for data access and integration
- **SQLite Database**: Local data storage with historical tracking
- **Responsive Design**: Mobile-friendly web interface
- **Background Scheduler**: Automated data collection service

### Technology Stack

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy
- **Frontend**: HTML, JavaScript, Bootstrap, Plotly.js
- **Database**: SQLite (production-ready, can migrate to PostgreSQL)
- **Server**: Uvicorn ASGI server
- **Scheduling**: Python schedule library
- **Containerization**: Docker and Docker Compose

---

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │────│   FastAPI App   │────│   SQLite DB     │
│   (Dashboard)   │    │   (Web Server)  │    │   (Data Store)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Data Collector│────│   Taara API     │
                       │   (Scheduler)   │    │   (External)    │
                       └─────────────────┘    └─────────────────┘
```

### Component Interaction

1. **Data Collector** polls Taara API at regular intervals
2. **API Client** handles authentication and data retrieval from Taara
3. **Database Layer** stores usage data and API logs
4. **Web Server** serves dashboard and provides REST API
5. **Frontend** displays real-time charts and statistics

### Data Flow

```
Taara API → Data Collector → Database → Web API → Dashboard
    ↑                                       ↓
    └────── Authentication & Session ──────┘
```

---

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional but recommended)

### Quick Start with Docker

```bash
# Clone the repository
git clone <repository-url>
cd taara

# Copy environment template
cp .env.example .env

# Edit .env with your Taara credentials
nano .env

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Manual Installation

```bash
# Clone and navigate
git clone <repository-url>
cd taara

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python init_db.py

# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start the scheduler
python scheduler.py
```

### Environment Configuration

Create a `.env` file with the following variables:

```env
# Taara API Credentials
TAARA_PHONE_COUNTRY_CODE=254
TAARA_PHONE_NUMBER=your_phone_number
TAARA_PASSCODE=your_passcode
TAARA_PARTNER_ID=your_partner_id
TAARA_HOTSPOT_ID=your_hotspot_id

# Database
DATABASE_URL=sqlite:///./taara_monitoring.db

# Application
DEBUG=False
LOG_LEVEL=INFO
```

---

## Development Environment

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Run in development mode
python -m uvicorn app.main:app --reload --port 8000

# Run tests
python tests/test_comprehensive.py

# Check code style (if installed)
flake8 app/
black app/
```

### Development Workflow

1. **Feature Development**
   ```bash
   git checkout -b feature/new-feature
   # Develop and test
   python tests/test_comprehensive.py
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

2. **Testing Changes**
   ```bash
   # Test API directly
   python test_api.py
   
   # Test data collection
   python -c "from app.data_collector import DataCollector; DataCollector().collect_data()"
   
   # Run comprehensive tests
   python tests/test_comprehensive.py
   ```

3. **Database Changes**
   ```bash
   # Backup database
   cp taara_monitoring.db taara_monitoring.db.backup
   
   # Modify models in app/database.py
   # Run migration script if needed
   python scripts/migrate_database.py
   ```

### Code Style Guidelines

- Follow PEP 8 for Python code
- Use type hints where possible
- Document functions and classes
- Keep functions small and focused
- Use meaningful variable names

---

## Code Structure

```
taara/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # FastAPI application and routes
│   ├── database.py        # Database models and connection
│   ├── taara_api.py       # Taara API client
│   ├── data_collector.py  # Data collection logic
│   └── config.py          # Application configuration
├── templates/             # HTML templates
│   └── dashboard.html     # Main dashboard template
├── static/               # Static files (CSS, JS, images)
├── tests/                # Test files
│   └── test_comprehensive.py
├── scripts/              # Utility scripts
│   ├── setup_database.py
│   └── mock_isp_api.py
├── docs/                 # Documentation
├── deployment/           # Deployment configurations
│   └── ansible/
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker image definition
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
└── README.md           # Basic project info
```

### Key Files Explained

#### `app/main.py`
- FastAPI application instance
- Route definitions for web dashboard and API
- Template rendering and static file serving
- Chart generation for dashboard

#### `app/taara_api.py`
- Taara API client implementation
- Authentication handling (login/logout)
- Data retrieval and parsing
- Error handling and retry logic

#### `app/database.py`
- SQLAlchemy models
- Database connection setup
- Table definitions
- Database utility functions

#### `app/data_collector.py`
- Main data collection logic
- Scheduled data retrieval
- Database storage
- Error handling and logging

---

## API Reference

### Dashboard Routes

#### `GET /`
**Main Dashboard**
- Returns the HTML dashboard with charts and statistics
- Includes latest usage data and historical trends

### REST API Endpoints

#### `GET /api/data`
**Get Latest Usage Data**

Returns the 5 most recent usage records.

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2025-08-23T11:59:17",
    "plan_name": "1 Month Unlimited",
    "remaining_balance_gb": 928.8,
    "expires_in_days": 28,
    "is_active": true
  }
]
```

#### `GET /api/history?days=7`
**Get Usage History**

Returns usage data for the specified number of days.

**Parameters:**
- `days` (optional): Number of days to retrieve (default: 7)

**Response:**
```json
[
  {
    "timestamp": "2025-08-23T11:44:46",
    "remaining_balance_gb": 928.9,
    "plan_name": "1 Month Unlimited"
  }
]
```

#### `GET /api/stats`
**Get Usage Statistics**

Returns calculated statistics including predictions.

**Response:**
```json
{
  "current_balance_gb": 928.8,
  "expires_in_days": 28,
  "avg_daily_usage_gb": 0.1,
  "predicted_days_remaining": 28,
  "plan_name": "1 Month Unlimited",
  "last_updated": "2025-08-23T11:59:17"
}
```

#### `POST /api/collect`
**Trigger Manual Data Collection**

Manually triggers data collection from Taara API.

**Response:**
```json
{
  "status": "success",
  "message": "Data collection completed"
}
```

### Error Responses

All API endpoints return error responses in this format:

```json
{
  "detail": "Error description"
}
```

Common HTTP status codes:
- `200`: Success
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

## Database Schema

### Tables

#### `data_usage_records`
Stores internet usage data collected from Taara API.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `timestamp` | DATETIME | When the record was created |
| `subscriber_id` | STRING | Taara subscriber ID |
| `plan_name` | STRING | Name of the internet plan |
| `plan_id` | STRING | Unique plan identifier |
| `remaining_balance_gb` | FLOAT | Remaining data in GB |
| `remaining_balance_bytes` | BIGINT | Remaining data in bytes |
| `total_data_usage_bytes` | BIGINT | Total data used in bytes |
| `expires_in_days` | INTEGER | Days until plan expires |
| `is_active` | BOOLEAN | Whether the plan is active |
| `is_home_plan` | BOOLEAN | Whether this is the home plan |
| `raw_response` | TEXT | Raw API response for debugging |
| `created_at` | DATETIME | Record creation timestamp |

#### `api_logs`
Stores API interaction logs for debugging and monitoring.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `timestamp` | DATETIME | When the API call was made |
| `operation` | STRING | Type of operation (login, data, logout) |
| `success` | BOOLEAN | Whether the operation succeeded |
| `response_time_ms` | FLOAT | Response time in milliseconds |
| `error_message` | TEXT | Error details if failed |
| `request_data` | TEXT | Request parameters (sanitized) |
| `response_data` | TEXT | Response data |

### Database Operations

#### Creating Tables
```python
from app.database import create_tables
create_tables()
```

#### Querying Data
```python
from app.database import SessionLocal, DataUsageRecord
from sqlalchemy import desc

session = SessionLocal()
latest_record = session.query(DataUsageRecord)\
    .filter(DataUsageRecord.is_active == True)\
    .order_by(desc(DataUsageRecord.timestamp))\
    .first()
session.close()
```

#### Adding Records
```python
from app.database import SessionLocal, DataUsageRecord

session = SessionLocal()
record = DataUsageRecord(
    subscriber_id="example-id",
    plan_name="Test Plan",
    # ... other fields
)
session.add(record)
session.commit()
session.close()
```

---

## Testing

### Test Suite Structure

The comprehensive test suite (`tests/test_comprehensive.py`) includes:

1. **Environment and Configuration Tests**
   - Environment variable validation
   - Database file checks
   - Dependency verification

2. **Database Operations Tests**
   - Table creation
   - Connection testing
   - CRUD operations

3. **Taara API Integration Tests**
   - Authentication testing
   - Data retrieval
   - Error handling

4. **Data Collection Tests**
   - Collector initialization
   - Data collection process
   - Database storage verification

5. **Web API Endpoint Tests**
   - All REST API endpoints
   - Response validation
   - Performance measurement

6. **Dashboard Interface Tests**
   - HTML content validation
   - Responsive design checks
   - Element presence verification

7. **Performance and Stress Tests**
   - Concurrent request handling
   - Database query performance
   - Load testing

8. **Error Handling Tests**
   - Invalid endpoint handling
   - Authentication failures
   - Edge case validation

### Running Tests

```bash
# Run all tests
python tests/test_comprehensive.py

# Test specific components
python test_api.py  # API only
python -c "from app.data_collector import DataCollector; print(DataCollector().collect_data())"  # Data collection
```

### Test Results Interpretation

- **PASS**: Test succeeded completely
- **FAIL**: Test failed and requires attention
- **WARNING**: Test passed but with minor issues

Success rates:
- 90%+: Excellent system health
- 75-89%: Good, minor issues
- 50-74%: Fair, needs attention
- <50%: Poor, immediate action required

---

## Deployment

### Production Deployment with Docker

```bash
# Build and deploy
docker-compose up -d --build

# View status
docker-compose ps

# View logs
docker-compose logs -f app
docker-compose logs -f scheduler

# Update deployment
git pull
docker-compose down
docker-compose up -d --build
```

### Manual Production Deployment

```bash
# Setup production environment
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# Clone and setup
git clone <repo> /opt/taara
cd /opt/taara
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values

# Setup systemd services
sudo cp deployment/systemd/taara-web.service /etc/systemd/system/
sudo cp deployment/systemd/taara-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable taara-web taara-scheduler
sudo systemctl start taara-web taara-scheduler

# Configure nginx
sudo cp deployment/nginx/taara.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/taara.conf /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

### Environment Variables for Production

```env
# Production settings
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./taara_monitoring.db

# Security
SECRET_KEY=your-secret-key-here

# Performance
WORKERS=4
```

### Health Checks

```bash
# Check application health
curl http://localhost:8000/api/data

# Check database
python -c "from app.database import SessionLocal; SessionLocal().execute('SELECT 1')"

# Check scheduler
ps aux | grep scheduler
```

---

## Monitoring & Logging

### Application Logs

Logs are written to:
- Console output (development)
- `taara_scheduler.log` (scheduler logs)
- System logs via systemd (production)

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical errors

### Monitoring Commands

```bash
# View recent logs
tail -f taara_scheduler.log

# Monitor database size
du -h taara_monitoring.db

# Check disk space
df -h

# Monitor system resources
htop
```

### Performance Monitoring

Key metrics to monitor:
- API response times
- Database query performance
- Memory usage
- Disk space
- Network connectivity

### Setting Up Alerts

```bash
# Basic disk space monitoring
echo "if [ \$(df / | tail -1 | awk '{print \$5}' | sed 's/%//') -gt 80 ]; then echo 'Disk space warning'; fi" > /etc/cron.hourly/disk-check

# Database size monitoring
echo "if [ \$(du taara_monitoring.db | awk '{print \$1}') -gt 100000 ]; then echo 'Database size warning'; fi" > /etc/cron.daily/db-check
```

---

## Troubleshooting

### Common Issues

#### 1. API Authentication Fails

**Symptoms:**
- Login errors in logs
- No new data being collected
- 404 or 401 API responses

**Solutions:**
```bash
# Verify credentials
python test_api.py

# Check environment variables
cat .env | grep TAARA

# Test manual login
python -c "from app.taara_api import TaaraAPI; api = TaaraAPI(...); print(api.login())"
```

#### 2. Database Issues

**Symptoms:**
- Database locked errors
- Query timeouts
- Data not saving

**Solutions:**
```bash
# Check database file permissions
ls -la taara_monitoring.db

# Test database connection
python -c "from app.database import SessionLocal; SessionLocal().execute('SELECT 1')"

# Backup and recreate if corrupted
cp taara_monitoring.db backup.db
python init_db.py
```

#### 3. Web Interface Not Loading

**Symptoms:**
- 500 errors
- Missing charts
- Template errors

**Solutions:**
```bash
# Check if server is running
curl http://localhost:8000/api/data

# Verify template files
ls -la templates/dashboard.html

# Check static files
ls -la static/

# Restart web server
docker-compose restart app
```

#### 4. Scheduler Not Running

**Symptoms:**
- No new data being collected
- Stale timestamps in database
- Missing scheduler logs

**Solutions:**
```bash
# Check scheduler process
ps aux | grep scheduler

# Restart scheduler
docker-compose restart scheduler

# Check scheduler logs
docker-compose logs scheduler
```

#### 5. Performance Issues

**Symptoms:**
- Slow page loads
- High CPU usage
- Memory errors

**Solutions:**
```bash
# Check system resources
htop
free -h
df -h

# Optimize database
VACUUM database in SQLite browser

# Check for memory leaks
monitor application over time
```

### Debug Mode

Enable debug logging:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### Getting Help

1. Check application logs
2. Run comprehensive tests
3. Verify environment configuration
4. Test individual components
5. Check system resources

---

## Contributing

### Development Guidelines

1. **Code Style**
   - Follow PEP 8
   - Use type hints
   - Document functions
   - Write tests for new features

2. **Git Workflow**
   ```bash
   git checkout -b feature/description
   # Make changes
   python tests/test_comprehensive.py
   git commit -m "feat: description"
   git push origin feature/description
   # Create pull request
   ```

3. **Testing Requirements**
   - All new features must have tests
   - Maintain >80% test success rate
   - Test both success and failure cases

4. **Documentation**
   - Update this documentation for new features
   - Include API documentation for new endpoints
   - Update README for setup changes

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No hardcoded credentials
- [ ] Error handling implemented
- [ ] Logging added where appropriate

### Feature Request Process

1. Create issue describing the feature
2. Discuss implementation approach
3. Create feature branch
4. Implement with tests
5. Update documentation
6. Submit pull request

---

This developer documentation provides comprehensive information for setting up, developing, testing, and maintaining the Taara Internet Monitor system. For additional help, refer to the inline code comments and the end-user documentation.
