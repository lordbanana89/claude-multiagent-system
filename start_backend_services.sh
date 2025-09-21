#!/bin/bash

# Start Backend Services for Claude Squad System

echo "🚀 Starting Claude Squad Backend Services..."

# Kill any existing processes
echo "Stopping existing services..."
pkill -f routes_api.py
pkill -f integration_orchestrator.py
sleep 2

# Start Routes API (Port 5001)
echo "Starting Routes API on port 5001..."
python3 routes_api.py > /tmp/routes_api.log 2>&1 &
ROUTES_PID=$!

# Start Integration Orchestrator (Port 5002)
echo "Starting Integration Orchestrator on port 5002..."
python3 integration_orchestrator.py > /tmp/integration_orchestrator.log 2>&1 &
INTEGRATION_PID=$!

# Wait for services to start
sleep 3

# Check if services are running
echo ""
echo "Checking service status..."

# Test Routes API
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health | grep -q "200"; then
    echo "✅ Routes API is running on port 5001 (PID: $ROUTES_PID)"
else
    echo "❌ Routes API failed to start"
fi

# Test Integration Orchestrator
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/api/integration/health | grep -q "200"; then
    echo "✅ Integration Orchestrator is running on port 5002 (PID: $INTEGRATION_PID)"
else
    echo "❌ Integration Orchestrator failed to start"
fi

# Test CORS headers
echo ""
echo "Testing CORS configuration..."

CORS_5001=$(curl -s -H "Origin: http://localhost:5173" -I http://localhost:5001/api/health 2>/dev/null | grep -i "access-control-allow-origin")
if [ ! -z "$CORS_5001" ]; then
    echo "✅ Routes API CORS: $CORS_5001"
else
    echo "❌ Routes API CORS not configured"
fi

CORS_5002=$(curl -s -H "Origin: http://localhost:5173" -I http://localhost:5002/api/integration/health 2>/dev/null | grep -i "access-control-allow-origin")
if [ ! -z "$CORS_5002" ]; then
    echo "✅ Integration CORS: $CORS_5002"
else
    echo "❌ Integration CORS not configured"
fi

echo ""
echo "📋 Service Summary:"
echo "  - Routes API: http://localhost:5001"
echo "  - Integration Orchestrator: http://localhost:5002"
echo "  - Frontend: http://localhost:5173"
echo ""
echo "Logs available at:"
echo "  - /tmp/routes_api.log"
echo "  - /tmp/integration_orchestrator.log"
echo ""
echo "✅ Backend services started successfully!"