#!/bin/bash

# Setup script for Taara Internet Monitor

echo "Setting up Taara Internet Monitor..."

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your actual credentials!"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create database (PostgreSQL)
echo "Setting up database..."
echo "Make sure PostgreSQL is running and create the database:"
echo "sudo -u postgres createdb taara_monitoring"
echo "sudo -u postgres psql -c \"CREATE USER taara_user WITH PASSWORD 'your_password';\""
echo "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE taara_monitoring TO taara_user;\""

# Create database tables
echo "Creating database tables..."
python -c "from app.database import create_tables; create_tables()"

# Test API connection
echo "Testing API connection..."
python -c "
from app.taara_api import TaaraAPI
import os
from dotenv import load_dotenv

load_dotenv()

api = TaaraAPI(
    phone_country_code=os.getenv('TAARA_PHONE_COUNTRY_CODE', '254'),
    phone_number=os.getenv('TAARA_PHONE_NUMBER', '718920243'),
    passcode=os.getenv('TAARA_PASSCODE', '888344'),
    partner_id=os.getenv('TAARA_PARTNER_ID', '313324693'),
    hotspot_id=os.getenv('TAARA_HOTSPOT_ID', '596370186')
)

result = api.login()
if result['success']:
    print('✅ API connection successful!')
    api.logout()
else:
    print('❌ API connection failed:', result.get('error'))
"

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. Start the web server: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "2. Start the data collector: python scheduler.py"
echo "3. Open http://localhost:8000 in your browser"
