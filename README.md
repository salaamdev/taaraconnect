# Taara Internet Monitor

A comprehensive internet data usage monitoring system for Taara internet subscribers. This application automatically scrapes your data usage from the Taara API and provides beautiful visualizations and analytics.

## Features

- **Real-time Data Monitoring**: Automatically collects data usage every 15 minutes
- **Beautiful Dashboard**: Clean, responsive web interface with charts and statistics
- **Usage Analytics**: Track daily usage patterns and predict when you'll run out of data
- **Historical Data**: Store and view usage history over time
- **API Endpoints**: RESTful API for integration with other systems
- **Configurable**: Easy to configure collection intervals and credentials

## Screenshots

The dashboard provides:
- Current data balance and remaining days
- Daily usage rate calculations
- Progress bar showing total usage
- Interactive charts for balance over time
- Recent data points table
- Auto-refresh functionality

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <your-repo-url>
cd taara
```

2. Copy and edit environment variables:
```bash
cp .env.example .env
# Edit .env with your Taara credentials
```

3. Start the application:
```bash
docker-compose up -d
```

4. Open http://localhost:8000 in your browser

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Setup PostgreSQL database:
```bash
sudo -u postgres createdb taara_monitoring
sudo -u postgres psql -c "CREATE USER taara_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE taara_monitoring TO taara_user;"
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the application:
```bash
# Start web server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start data collector (in another terminal)
python scheduler.py
```

## Configuration

Edit the `.env` file with your Taara account details:

```env
DATABASE_URL=postgresql://taara_user:password@localhost:5432/taara_monitoring
TAARA_PHONE_COUNTRY_CODE=254
TAARA_PHONE_NUMBER=718920243
TAARA_PASSCODE=888344
TAARA_PARTNER_ID=313324693
TAARA_HOTSPOT_ID=596370186
SCRAPING_INTERVAL_MINUTES=15
```

## API Endpoints

- `GET /` - Dashboard web interface
- `GET /api/data` - Get latest data usage records
- `GET /api/history?days=7` - Get usage history for specified days
- `GET /api/stats` - Get usage statistics and predictions
- `POST /api/collect` - Manually trigger data collection

## Data Collection

The system collects the following data points:
- Remaining data balance (GB)
- Plan name and ID
- Days until expiration
- Total data usage
- Active/inactive status
- Timestamp of collection

Data is collected every 15 minutes by default (configurable).

## Deployment

### Digital Ocean Droplet

1. Create a new droplet with Ubuntu 22.04
2. Install Docker and Docker Compose
3. Clone your repository
4. Configure environment variables
5. Run `docker-compose up -d`
6. Configure nginx reverse proxy (optional)

### Environment Variables for Production

```env
DATABASE_URL=postgresql://taara_user:secure_password@localhost:5432/taara_monitoring
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
SCRAPING_INTERVAL_MINUTES=15
```

## Development

To run in development mode:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

- **FastAPI**: Web framework for the API and dashboard
- **PostgreSQL**: Database for storing usage data
- **SQLAlchemy**: ORM for database operations
- **Plotly**: Interactive charts and visualizations
- **Bootstrap**: Responsive UI framework
- **Requests**: HTTP client for Taara API
- **Schedule**: Task scheduling for data collection

## Security Considerations

- Store credentials securely in environment variables
- Use HTTPS in production
- Regularly rotate API credentials
- Limit database access
- Monitor for unusual API usage patterns

## Troubleshooting

### Common Issues

1. **API Login Fails**: Check your phone number, passcode, and partner ID
2. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
3. **No Data Collected**: Check the scheduler logs for errors
4. **Charts Not Loading**: Ensure JavaScript is enabled and Plotly is accessible

### Logs

- Web server logs: Check uvicorn output
- Scheduler logs: Check `taara_scheduler.log`
- Database logs: Check PostgreSQL logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for personal use. Make sure to comply with Taara's terms of service when using their API.

## Disclaimer

This tool is for personal monitoring of your own Taara internet usage. Please respect Taara's API rate limits and terms of service. The authors are not responsible for any issues arising from the use of this tool.
