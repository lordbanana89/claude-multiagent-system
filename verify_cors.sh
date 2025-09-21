#!/bin/bash

echo "🔍 Verifying CORS Configuration for Claude Squad System"
echo "======================================================="
echo ""

# Test Routes API (Port 5001)
echo "📡 Testing Routes API (Port 5001)..."
RESULT=$(curl -s -H "Origin: http://localhost:5173" -I http://localhost:5001/api/health 2>&1 | grep -i "access-control-allow-origin")
if [ ! -z "$RESULT" ]; then
    echo "✅ Routes API CORS for localhost:5173: $RESULT"
else
    echo "❌ Routes API CORS for localhost:5173 NOT working"
fi

RESULT=$(curl -s -H "Origin: http://localhost:8080" -I http://localhost:5001/api/health 2>&1 | grep -i "access-control-allow-origin")
if [ ! -z "$RESULT" ]; then
    echo "✅ Routes API CORS for localhost:8080: $RESULT"
else
    echo "❌ Routes API CORS for localhost:8080 NOT working"
fi

echo ""

# Test Integration Orchestrator (Port 5002)
echo "📡 Testing Integration Orchestrator (Port 5002)..."
RESULT=$(curl -s -H "Origin: http://localhost:5173" -I http://localhost:5002/api/integration/health 2>&1 | grep -i "access-control-allow-origin")
if [ ! -z "$RESULT" ]; then
    echo "✅ Integration CORS for localhost:5173: $RESULT"
else
    echo "❌ Integration CORS for localhost:5173 NOT working"
fi

RESULT=$(curl -s -H "Origin: http://localhost:8080" -I http://localhost:5002/api/integration/health 2>&1 | grep -i "access-control-allow-origin")
if [ ! -z "$RESULT" ]; then
    echo "✅ Integration CORS for localhost:8080: $RESULT"
else
    echo "❌ Integration CORS for localhost:8080 NOT working"
fi

echo ""

# Test actual data fetch
echo "📊 Testing actual data fetch..."
echo ""

echo "Routes API Health Check:"
curl -s http://localhost:5001/api/health | python3 -m json.tool | head -5
echo ""

echo "Integration Health Check:"
curl -s http://localhost:5002/api/integration/health | python3 -m json.tool | head -10
echo ""

echo "======================================================="
echo "✨ CORS Verification Complete!"
echo ""
echo "📝 Summary:"
echo "  - Routes API: http://localhost:5001"
echo "  - Integration: http://localhost:5002"
echo "  - Frontend: http://localhost:5173"
echo "  - Test Page: http://localhost:8080/test_cors_complete.html"
echo ""
echo "All services should now be accessible from the frontend!"