#!/bin/bash

# Startup script for Taara Internet Monitor

echo "Starting Taara Internet Monitor..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Check if database is ready
echo "Waiting for database to be ready..."
until pg_isready -h localhost -p 5432 -U ${DATABASE_USER:-taara_user} 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database ready!"

# Create tables if they don't exist
echo "Creating database tables..."
python -c "
from app.database import create_tables
try:
    create_tables()
    print('Database tables created/verified successfully')
except Exception as e:
    print(f'Error creating tables: {e}')
"

# Start data collection immediately
echo "Running initial data collection..."
python -c "
from app.data_collector import DataCollector
try:
    collector = DataCollector()
    success = collector.collect_data()
    if success:
        print('Initial data collection successful')
    else:
        print('Initial data collection failed')
except Exception as e:
    print(f'Error in initial collection: {e}')
"

echo "Taara Internet Monitor is ready!"
echo "Web dashboard: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
