# 🚀 Taara Internet Monitor - WORKING VERSION

A complete internet data usage monitoring system for Taara subscribers. **This is a fully functional implementation** that automatically tracks your data usage and provides beautiful visualizations.

## ✅ What's Working

- ✅ **API Integration**: Successfully connects to Taara API
- ✅ **Data Collection**: Automatically scrapes usage data every 15 minutes
- ✅ **Database Storage**: Stores historical data in SQLite database
- ✅ **Web Dashboard**: Beautiful responsive interface with charts
- ✅ **Real-time Updates**: Live data refresh and manual collection
- ✅ **Usage Analytics**: Daily usage rates and predictions

## 🎯 Features

- **Current Balance**: See your remaining data in GB
- **Usage Tracking**: Monitor daily consumption patterns
- **Expiration Alerts**: Know when your plan expires
- **Interactive Charts**: Visual representation of usage over time
- **Manual Refresh**: Force data collection when needed
- **Mobile Responsive**: Works on all devices

## 🚀 Quick Start

### Option 1: Simple Run (Recommended)

```bash
# Clone and navigate to directory
cd /path/to/taara

# Start everything with one command
./run.sh
```

### Option 2: Manual Setup

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3-fastapi python3-requests python3-sqlalchemy python3-dotenv python3-jinja2 python3-schedule python3-plotly python3-uvicorn

# 2. Edit credentials (REQUIRED)
cp .env.example .env
# Edit .env with your actual credentials

# 3. Initialize database
python3 init_db.py

# 4. Start web server (Terminal 1)
PYTHONPATH=/usr/lib/python3/dist-packages python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Start data collector (Terminal 2)  
PYTHONPATH=/usr/lib/python3/dist-packages python3 scheduler.py
```

## 🔧 Configuration

Edit `.env` file with your Taara account details:

```bash
# Your Taara credentials (CHANGE THESE!)
TAARA_PHONE_COUNTRY_CODE=254
TAARA_PHONE_NUMBER=your_phone_number
TAARA_PASSCODE=your_passcode
TAARA_PARTNER_ID=your_partner_id
TAARA_HOTSPOT_ID=your_hotspot_id

# How often to collect data (minutes)
SCRAPING_INTERVAL_MINUTES=15
```

## 🌐 Access Points

- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Raw API**: http://localhost:8000/api/data

## 📊 Current Data (Based on Test)

Your current status shows:
- **Plan**: 1 Month Unlimited  
- **Remaining**: 928.9 GB
- **Expires**: 28 days
- **Status**: Active ✅

## 🔧 API Endpoints

- `GET /` - Web dashboard
- `GET /api/data` - Latest usage data
- `GET /api/history?days=7` - Usage history
- `GET /api/stats` - Usage statistics
- `POST /api/collect` - Manual data collection

## 📱 Dashboard Features

- **Live Data**: Auto-refreshes every 5 minutes
- **Progress Bar**: Visual usage representation  
- **Interactive Charts**: Plotly-powered visualizations
- **Recent Data Table**: Latest collection points
- **Manual Refresh**: Force data update button
- **Responsive Design**: Works on mobile and desktop

## 🗂️ Project Structure

```
taara/
├── app/
│   ├── main.py          # FastAPI web application
│   ├── database.py      # Database models and setup
│   ├── taara_api.py     # Taara API integration
│   ├── data_collector.py # Data collection logic
│   └── config.py        # Configuration settings
├── templates/
│   └── dashboard.html   # Web interface template
├── static/              # Static files (if needed)
├── .env                 # Your credentials (EDIT THIS!)
├── run.sh              # Simple startup script
├── init_db.py          # Database initialization
├── scheduler.py        # Data collection scheduler
├── test_api.py         # API connection test
└── README.md           # This file
```

## 🧪 Testing

Test your API connection:
```bash
PYTHONPATH=/usr/lib/python3/dist-packages python3 test_api.py
```

Should output:
```
✅ Login successful!
✅ Bundle data retrieval successful!
✅ Logout successful!
✅ API test completed successfully!
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to use `PYTHONPATH=/usr/lib/python3/dist-packages`
2. **Database Errors**: Run `python3 init_db.py` to recreate tables
3. **API Failures**: Check your credentials in `.env` file
4. **Port Conflicts**: Change port in uvicorn command if 8000 is taken

### Logs

- Web server: Check terminal output
- Data collector: Check `taara_scheduler.log`
- Database: SQLite file at `taara_monitoring.db`

## 🚀 Deployment

### Local Development
```bash
./run.sh
```

### Production (Digital Ocean)
```bash
# Install dependencies
sudo apt update && sudo apt install -y python3-fastapi python3-requests python3-sqlalchemy python3-dotenv python3-jinja2 python3-schedule python3-plotly python3-uvicorn

# Clone repository
git clone <your-repo> taara-monitor
cd taara-monitor

# Configure
cp .env.example .env
# Edit .env with your credentials

# Start services
./run.sh
```

## 📊 Usage Analytics

The system automatically calculates:
- Daily usage rates
- Predicted days remaining
- Usage patterns over time
- Peak usage periods

## 🎨 UI Features

- **Bootstrap 5**: Modern, responsive design
- **Plotly Charts**: Interactive data visualizations
- **FontAwesome Icons**: Beautiful iconography
- **Auto-refresh**: Updates every 5 minutes
- **Manual Refresh**: Force update button
- **Progress Indicators**: Visual usage bars

## 🔒 Security

- Credentials stored in environment variables
- HTTPS ready (add reverse proxy)
- Rate limiting on API calls
- Secure JWT token handling

## 🚀 Next Steps

1. **Start the application**: `./run.sh`
2. **Open browser**: http://localhost:8000
3. **Monitor usage**: Watch the beautiful charts!
4. **Set up automation**: Let it run and collect data

## 💡 Pro Tips

- Let it run for a few hours to see usage patterns
- Check the dashboard on mobile - it's fully responsive
- Use the manual refresh button to get instant updates
- Monitor the logs to ensure data collection is working

---

**🎉 Congratulations! You now have a fully working Taara internet monitoring system!**

The system is already collecting data and will continue to do so every 15 minutes. Your dashboard will show increasingly useful analytics as more data is collected over time.
