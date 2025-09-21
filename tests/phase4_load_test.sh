#!/bin/bash
# Phase 4: Load Testing Script

echo "=================================================="
echo "PHASE 4: LOAD TESTING"
echo "=================================================="

# Configuration
MCP_URL="http://localhost:9999/jsonrpc"
AUTH_URL="http://localhost:5002/api/auth/login"
CONCURRENT_REQUESTS=50
TOTAL_REQUESTS=200

echo -e "\nTest Configuration:"
echo "  Concurrent requests: $CONCURRENT_REQUESTS"
echo "  Total requests: $TOTAL_REQUESTS"

# 1. MCP Server Load Test
echo -e "\n[LOAD] Testing MCP Server..."
echo "Starting at: $(date)"

# Create payload file
cat > /tmp/mcp_payload.json << EOF
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"heartbeat","arguments":{"agent":"load_test"}},"id":1}
EOF

# Run load test using parallel requests
start_time=$(date +%s)
seq 1 $TOTAL_REQUESTS | xargs -P $CONCURRENT_REQUESTS -I {} \
    curl -s -X POST $MCP_URL \
    -H "Content-Type: application/json" \
    -d @/tmp/mcp_payload.json \
    -o /dev/null 2>&1

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "  Duration: ${duration}s"
echo "  Requests/sec: $((TOTAL_REQUESTS / duration))"

if [ $duration -lt 30 ]; then
    echo "  ✅ MCP Load Test PASSED (Good performance)"
else
    echo "  ⚠️ MCP Load Test WARNING (Slow performance)"
fi

# 2. Auth API Load Test
echo -e "\n[LOAD] Testing Auth API..."
echo "Starting at: $(date)"

# Create auth payload
cat > /tmp/auth_payload.json << EOF
{"username":"loadtest","password":"test123"}
EOF

# Run auth load test
start_time=$(date +%s)
seq 1 $((TOTAL_REQUESTS/2)) | xargs -P $((CONCURRENT_REQUESTS/2)) -I {} \
    curl -s -X POST $AUTH_URL \
    -H "Content-Type: application/json" \
    -d @/tmp/auth_payload.json \
    -o /dev/null 2>&1

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "  Duration: ${duration}s"
echo "  Requests/sec: $((TOTAL_REQUESTS/2 / duration))"

if [ $duration -lt 20 ]; then
    echo "  ✅ Auth Load Test PASSED (Good performance)"
else
    echo "  ⚠️ Auth Load Test WARNING (Slow performance)"
fi

# 3. Database Load Test
echo -e "\n[LOAD] Testing Database Operations..."
start_time=$(date +%s)

for i in $(seq 1 50); do
    sqlite3 mcp_system.db "SELECT COUNT(*) FROM agents;" > /dev/null 2>&1 &
done
wait

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "  50 concurrent queries in ${duration}s"
if [ $duration -lt 5 ]; then
    echo "  ✅ Database Load Test PASSED"
else
    echo "  ⚠️ Database Load Test WARNING"
fi

# 4. Check system stability after load
echo -e "\n[LOAD] Checking System Stability..."
sleep 2

# Test if services still responding
curl -s -X POST $MCP_URL \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"heartbeat","arguments":{"agent":"stability_check"}},"id":1}' \
    -o /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "  ✅ System stable after load test"
else
    echo "  ❌ System unstable after load test"
fi

# Clean up
rm -f /tmp/mcp_payload.json /tmp/auth_payload.json

echo -e "\n✅ Load Testing Complete"