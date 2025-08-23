#!/bin/bash
# Production Verification Script for Taara Internet Monitor

set -e

echo "🔍 Taara Internet Monitor - Production Verification"
echo "=================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if containers are running
echo "📦 Checking container status..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Containers are not running. Run 'docker-compose up -d' first."
    exit 1
fi

# Test API endpoint
echo "🔌 Testing API endpoint..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/data || echo "000")
if [ "$API_STATUS" == "200" ]; then
    echo "✅ API endpoint is working"
else
    echo "❌ API endpoint failed (Status: $API_STATUS)"
fi

# Test HTTPS endpoint
echo "🔐 Testing HTTPS endpoint..."
HTTPS_STATUS=$(curl -s -k -o /dev/null -w "%{http_code}" https://localhost/ || echo "000")
if [ "$HTTPS_STATUS" == "200" ]; then
    echo "✅ HTTPS endpoint is working"
else
    echo "❌ HTTPS endpoint failed (Status: $HTTPS_STATUS)"
fi

# Check database records
echo "📊 Checking database..."
RECORD_COUNT=$(docker-compose exec -T app python -c "
from app.database import SessionLocal, DataUsageRecord
from sqlalchemy import func
try:
    session = SessionLocal()
    count = session.query(func.count(DataUsageRecord.id)).scalar()
    print(count)
    session.close()
except Exception as e:
    print('0')
" 2>/dev/null)

if [ "$RECORD_COUNT" -gt "0" ]; then
    echo "✅ Database has $RECORD_COUNT records"
else
    echo "⚠️  No data records found. Check if credentials are configured in .env"
fi

echo ""
echo "🌐 Access Points:"
echo "   HTTPS: https://localhost"
echo "   HTTP:  http://localhost"
echo "   API:   http://localhost:8000"
echo ""
echo "📋 Management Commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Restart:      docker-compose restart"
echo "   Stop:         docker-compose down"
echo "   Status:       docker-compose ps"
echo ""

if [ "$RECORD_COUNT" -eq "0" ]; then
    echo "⚙️  Next Steps:"
    echo "   1. Edit .env with your Taara credentials"
    echo "   2. Restart scheduler: docker-compose restart scheduler"
    echo ""
fi

echo "✅ Production verification complete!"
