#!/bin/bash
# System Test Script - Verifica completa del sistema

echo "==========================================="
echo "   CLAUDE MULTI-AGENT SYSTEM TEST SUITE   "
echo "==========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Testing $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)

    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $response)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC} (Expected $expected, got $response)"
        ((TESTS_FAILED++))
    fi
}

# Test JSON response
test_json() {
    local name=$1
    local url=$2
    local field=$3

    echo -n "Testing $name... "
    response=$(curl -s $url | jq -r "$field" 2>/dev/null)

    if [ ! -z "$response" ] && [ "$response" != "null" ]; then
        echo -e "${GREEN}✅ PASSED${NC} (Value: $response)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC} (No valid response)"
        ((TESTS_FAILED++))
    fi
}

echo "1️⃣  BACKEND SERVICES"
echo "===================="
test_endpoint "Main API Gateway" "http://localhost:8888/" "200"
test_endpoint "API Health Check" "http://localhost:8888/api/system/health" "200"
test_endpoint "API Documentation" "http://localhost:8888/docs" "200"
test_endpoint "Agents Endpoint" "http://localhost:8888/api/agents" "200"

echo ""
echo "2️⃣  FRONTEND SERVICE"
echo "===================="
test_endpoint "React Dashboard" "http://localhost:5173" "200"
test_endpoint "Frontend Proxy to API" "http://localhost:5173/api/agents" "200"

echo ""
echo "3️⃣  API RESPONSES"
echo "================="
test_json "Agent Count" "http://localhost:8888/api/agents" ". | length"
test_json "First Agent ID" "http://localhost:8888/api/agents" ".[0].id"
test_json "System Health Status" "http://localhost:8888/api/system/health" ".status"

echo ""
echo "4️⃣  TMUX SESSIONS"
echo "================="
agent_count=$(tmux ls 2>/dev/null | grep -c claude-)
echo -n "Testing TMUX agent sessions... "
if [ $agent_count -eq 9 ]; then
    echo -e "${GREEN}✅ PASSED${NC} ($agent_count/9 agents active)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} ($agent_count/9 agents active)"
fi

echo ""
echo "5️⃣  DATABASE"
echo "============"
echo -n "Testing MCP database... "
if [ -f "mcp_system.db" ]; then
    tables=$(sqlite3 mcp_system.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null)
    if [ "$tables" -gt "0" ]; then
        echo -e "${GREEN}✅ PASSED${NC} ($tables tables)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC} (No tables)"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}❌ FAILED${NC} (Database not found)"
    ((TESTS_FAILED++))
fi

echo ""
echo "6️⃣  REDIS"
echo "========="
echo -n "Testing Redis connection... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "==========================================="
echo "              TEST SUMMARY                 "
echo "==========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! System is fully operational.${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Review the results above.${NC}"
    exit 1
fi