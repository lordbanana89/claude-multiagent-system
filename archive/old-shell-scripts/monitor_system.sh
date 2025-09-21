#!/bin/bash

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "📊 Claude Multi-Agent System Monitor"
echo "===================================="

while true; do
    clear
    echo "📊 SYSTEM STATUS - $(date)"
    echo "===================================="

    # Check MCP server
    echo ""
    echo "🔧 MCP Server:"
    if pgrep -f "mcp_server_complete.py" > /dev/null; then
        echo "  ✅ Running"
    else
        echo "  ❌ Not running"
    fi

    # Check agents
    echo ""
    echo "🤖 Active Agents:"
    for session in $(tmux list-sessions 2>/dev/null | grep claude- | cut -d: -f1); do
        echo "  ✅ $session"
    done

    # Show recent activities
    echo ""
    echo "📝 Recent Activities:"
    if [ -f "/tmp/mcp_shared_context.log" ]; then
        tail -5 /tmp/mcp_shared_context.log | while read line; do
            echo "  $line"
        done
    fi

    # Database stats
    echo ""
    echo "💾 Database Stats:"
    if [ -f "/tmp/mcp_state.db" ]; then
        activities=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM activities" 2>/dev/null || echo 0)
        components=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM components" 2>/dev/null || echo 0)
        echo "  Activities: $activities"
        echo "  Components: $components"
    fi

    echo ""
    echo "Press Ctrl+C to exit"
    sleep 5
done
