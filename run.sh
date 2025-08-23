#!/bin/bash

# Simple startup script for Taara Internet Monitor
# Run this to start the complete system

echo "🚀 Starting Taara Internet Monitor..."

# Set Python path for system packages
export PYTHONPATH=/usr/lib/python3/dist-packages

# Kill any existing processes
pkill -f "uvicorn app.main:app"
pkill -f "python3 scheduler.py"

# Initialize database
echo "📊 Initializing database..."
python3 init_db.py

# Start web server in background
echo "🌐 Starting web server on http://localhost:8000"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
WEB_PID=$!

# Start scheduler in background
echo "⏰ Starting data collection scheduler..."
python3 scheduler.py &
SCHEDULER_PID=$!

echo "✅ Taara Internet Monitor is running!"
echo ""
echo "🌐 Web Dashboard: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $WEB_PID 2>/dev/null
    kill $SCHEDULER_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Setup trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
