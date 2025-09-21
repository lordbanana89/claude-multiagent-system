#!/bin/bash
# System Status Check Script

echo "📊 Claude Multi-Agent System - Status"
echo "======================================="
echo ""

# Check services
echo "🔍 Service Status:"
echo -n "  Redis: "
redis-cli ping > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped"

echo -n "  MCP Server: "
curl -s http://localhost:9999/health > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped"

echo -n "  API Gateway: "
curl -s http://localhost:5001/health > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped"

echo -n "  Frontend: "
curl -s http://localhost:5173 > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped"

echo ""
echo "🤖 Agent Sessions:"
tmux ls 2>/dev/null | grep claude- | while read line; do
    echo "  ✅ $line"
done

echo ""
echo "💾 Databases:"
for db in mcp_system.db shared_inbox.db auth.db; do
    if [ -f "$db" ]; then
        size=$(du -h "$db" | cut -f1)
        echo "  ✅ $db ($size)"
    else
        echo "  ❌ $db (missing)"
    fi
done

echo ""
echo "📁 Disk Usage:"
du -sh . 2>/dev/null | cut -f1 | xargs echo "  Total:"
du -sh archive/ 2>/dev/null | cut -f1 | xargs echo "  Archive:"