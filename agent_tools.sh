#!/bin/bash
# Agent Tools - Funzioni per comunicazione tra agenti

MCP_URL="http://localhost:8099/jsonrpc"

# Heartbeat - Sono vivo
heartbeat() {
    local agent="${1:-$AGENT_NAME}"
    curl -s -X POST $MCP_URL \
        -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"heartbeat\",\"arguments\":{\"agent\":\"$agent\"}},\"id\":1}" \
        | python3 -c "import sys, json; r=json.load(sys.stdin); print(f'✅ Heartbeat: {r.get(\"result\", {}).get(\"status\", \"error\")}')"
}

# Status - Cambio il mio stato
status() {
    local agent="${1:-$AGENT_NAME}"
    local new_status="$2"
    local task="${3:-}"

    local args="{\"agent\":\"$agent\",\"status\":\"$new_status\""
    if [ -n "$task" ]; then
        args="${args},\"task\":\"$task\""
    fi
    args="${args}}"

    curl -s -X POST $MCP_URL \
        -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"update_status\",\"arguments\":$args},\"id\":1}" \
        | python3 -c "import sys, json; r=json.load(sys.stdin); print(f\"✅ Status updated to: $new_status\")"
}

# Log - Registro un'attività
log_activity() {
    local agent="${1:-$AGENT_NAME}"
    local category="$2"
    local activity="$3"
    local details="${4:-{}}"

    curl -s -X POST $MCP_URL \
        -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"log_activity\",\"arguments\":{\"agent\":\"$agent\",\"category\":\"$category\",\"activity\":\"$activity\",\"details\":$details}},\"id\":1}" \
        | python3 -c "import sys, json; r=json.load(sys.stdin); print(f'✅ Activity logged')"
}

# Send message to inbox
send_message() {
    local from="${1:-$AGENT_NAME}"
    local to="$2"
    local message="$3"

    python3 -c "
import sqlite3
import uuid
from datetime import datetime

db = sqlite3.connect('langgraph-test/shared_inbox.db')
cursor = db.cursor()
cursor.execute('''
    INSERT INTO messages (message_id, sender_id, recipient_id, message_type, subject, content, timestamp, status)
    VALUES (?, ?, ?, 'direct', ?, ?, ?, 'sent')
''', (str(uuid.uuid4()), '$from', '$to', '$message', '$message', datetime.now().isoformat(), ))
db.commit()
db.close()
print('✅ Message sent to $to')
"
}

# Read my inbox
read_inbox() {
    local agent="${1:-$AGENT_NAME}"

    echo "📬 INBOX for $agent:"
    sqlite3 -column -header langgraph-test/shared_inbox.db "
        SELECT
            sender_id as From,
            substr(subject, 1, 50) as Subject,
            datetime(timestamp) as Time
        FROM messages
        WHERE recipient_id = '$agent' OR recipient_id = 'all'
        ORDER BY timestamp DESC
        LIMIT 10
    "
}

# Check other agents status
check_agents() {
    echo "👥 AGENT STATUS:"
    sqlite3 -column -header mcp_system.db "
        SELECT
            id as Agent,
            status as Status,
            CASE
                WHEN last_heartbeat > datetime('now', '-60 seconds') THEN '✅ Active'
                ELSE '❌ Inactive'
            END as Health
        FROM agents
    "
}

# View recent activities
view_activities() {
    echo "📋 RECENT ACTIVITIES:"
    sqlite3 -column -header mcp_system.db "
        SELECT
            agent_id as Agent,
            category as Type,
            substr(activity, 1, 50) as Activity,
            datetime(timestamp) as Time
        FROM activity_logs
        ORDER BY timestamp DESC
        LIMIT 10
    "
}

# Initialize agent
init_agent() {
    local name="${1:-$AGENT_NAME}"
    export AGENT_NAME="$name"
    echo "🤖 Agent initialized: $AGENT_NAME"
    heartbeat
    status "$name" "idle"
}

# Help
agent_help() {
    echo "🛠️ AGENT TOOLS:"
    echo "  init_agent <name>     - Initialize agent"
    echo "  heartbeat            - Send heartbeat"
    echo "  status <status>      - Update status (idle/busy/error)"
    echo "  log_activity <cat> <msg> - Log activity"
    echo "  send_message <to> <msg>  - Send message to agent"
    echo "  read_inbox           - Read your messages"
    echo "  check_agents         - Check all agents status"
    echo "  view_activities      - View recent activities"
}

# Export functions
export -f heartbeat status log_activity send_message read_inbox check_agents view_activities init_agent agent_help