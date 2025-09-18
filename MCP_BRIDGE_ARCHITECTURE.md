# 🌉 MCP Bridge Architecture for Claude CLI

## 🎯 Soluzione: Claude Code Hooks + MCP Integration

Basandoci sulla ricerca, possiamo usare il **sistema di hooks nativo di Claude Code** per intercettare comandi e connettere a MCP!

## 📐 Architettura del Bridge

```
┌─────────────────────────┐
│   Claude CLI Agent      │
│  (in TMUX session)      │
└───────────┬─────────────┘
            │
            ▼ Hooks intercept
┌─────────────────────────┐
│   Claude Code Hooks     │
│  ~/.claude/hooks/       │
│  • PreToolUse          │
│  • PostToolUse         │
│  • Notification        │
└───────────┬─────────────┘
            │
            ▼ Bridge Layer
┌─────────────────────────┐
│   MCP Bridge Service    │
│  (Python daemon)        │
│  • Parse hook data      │
│  • Call MCP tools       │
│  • Return results       │
└───────────┬─────────────┘
            │
            ▼ MCP Protocol
┌─────────────────────────┐
│   MCP Server            │
│  (Already running)      │
│  • SQLite DB           │
│  • Coordination tools   │
└─────────────────────────┘
```

## 🔧 Come Funziona

### 1. **Claude Code Hooks**
I hooks intercettano ogni azione di Claude:
- **PreToolUse**: Prima che Claude esegua un comando
- **PostToolUse**: Dopo l'esecuzione
- **Notification**: Quando Claude comunica
- **Stop**: Quando Claude finisce

### 2. **Pattern Detection**
Il hook rileva quando Claude vuole usare MCP:
```bash
# Se Claude dice "I'll use the log_activity tool..."
# Il hook intercetta e traduce in chiamata MCP
```

### 3. **Bridge Service**
Un servizio Python che:
- Riceve dati dal hook via stdin
- Chiama il tool MCP appropriato
- Restituisce risultato a Claude

## 🛠️ Implementazione Step-by-Step

### Step 1: Hook Configuration
```toml
# ~/.claude/hooks/settings.toml
[hooks.pre_tool_use]
command = "python3 /path/to/mcp_bridge.py pre"
enabled = true

[hooks.post_tool_use]
command = "python3 /path/to/mcp_bridge.py post"
enabled = true

[hooks.notification]
command = "python3 /path/to/mcp_bridge.py notify"
enabled = true
```

### Step 2: Bridge Service
```python
# mcp_bridge.py
import json
import sys
import re
from mcp_client import MCPClient

def detect_mcp_intent(text):
    """Detect if Claude wants to use MCP tool"""
    patterns = {
        'log_activity': r"use.*log_activity.*tool.*to\s+(.+)",
        'check_conflicts': r"check.*conflicts.*for\s+(.+)",
        'register_component': r"register.*component\s+(.+)",
        'heartbeat': r"heartbeat|keep.*alive",
    }

    for tool, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return tool, match.groups()
    return None, None

def handle_hook(event_type, data):
    # Parse Claude's intent
    tool, params = detect_mcp_intent(data.get('content', ''))

    if tool:
        # Call MCP server
        mcp = MCPClient()
        result = mcp.call_tool(tool, params)

        # Return formatted response
        return {
            "continue": True,
            "systemMessage": f"MCP Tool '{tool}' executed: {result}"
        }

    return {"continue": True}

if __name__ == "__main__":
    event_type = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    # Read hook data from stdin
    data = json.load(sys.stdin)

    # Process and respond
    result = handle_hook(event_type, data)

    # Output JSON response
    print(json.dumps(result))
    sys.exit(0)
```

### Step 3: MCP Client Library
```python
# mcp_client.py
import requests
import sqlite3
from datetime import datetime

class MCPClient:
    def __init__(self):
        self.db_path = "/tmp/mcp_state.db"
        self.server_url = "http://localhost:8000"  # If using HTTP

    def call_tool(self, tool_name, params):
        """Call MCP tool directly via database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if tool_name == "log_activity":
            cursor.execute("""
                INSERT INTO activities (id, agent, timestamp, activity, category, metadata, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"bridge_{datetime.now().timestamp()}",
                params.get('agent', 'unknown'),
                datetime.now().isoformat(),
                params.get('activity', ''),
                params.get('category', 'info'),
                '{}',
                'completed'
            ))
            conn.commit()
            return "Activity logged"

        elif tool_name == "check_conflicts":
            # Query for conflicts
            cursor.execute("""
                SELECT agent, activity FROM activities
                WHERE activity LIKE ?
                ORDER BY timestamp DESC LIMIT 5
            """, (f"%{params[0]}%",))

            conflicts = cursor.fetchall()
            return f"Found {len(conflicts)} potential conflicts"

        conn.close()
        return f"Tool {tool_name} executed"
```

## 🔌 Integration Points

### 1. **Project-Level Hooks**
```bash
# Create project hooks directory
mkdir -p /Users/erik/Desktop/claude-multiagent-system/.claude/hooks/

# Add hook scripts
cp mcp_bridge.py .claude/hooks/
```

### 2. **Environment Variables**
```bash
export CLAUDE_PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"
export MCP_SERVER_URL="http://localhost:8000"
export MCP_DB_PATH="/tmp/mcp_state.db"
```

### 3. **Named Pipes for Real-time**
```python
# Create named pipe for bidirectional communication
import os
import stat

PIPE_PATH = "/tmp/claude_mcp_pipe"

if not os.path.exists(PIPE_PATH):
    os.mkfifo(PIPE_PATH)
```

## 🚀 Advanced Features

### 1. **Intent Recognition with NLP**
```python
# Use simple NLP to understand Claude's intent better
from difflib import SequenceMatcher

MCP_TOOLS = [
    'log_activity',
    'check_conflicts',
    'register_component',
    'update_status',
    'request_collaboration'
]

def find_closest_tool(text):
    best_match = None
    best_score = 0

    for tool in MCP_TOOLS:
        score = SequenceMatcher(None, tool, text.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = tool

    return best_match if best_score > 0.5 else None
```

### 2. **Context Injection**
```python
# Inject MCP context back into Claude's conversation
def inject_context(agent_session, context):
    tmux_cmd = f"""
    tmux send-keys -t {agent_session} "
    # MCP Context Update:
    {context}
    " Enter
    """
    os.system(tmux_cmd)
```

### 3. **Bidirectional Sync**
```python
# Monitor MCP database for changes and notify agents
def monitor_mcp_changes():
    last_check = datetime.now()

    while True:
        # Check for new activities
        new_activities = query_new_activities(since=last_check)

        for activity in new_activities:
            # Notify relevant agents
            notify_agent(activity['agent'], activity)

        last_check = datetime.now()
        time.sleep(5)
```

## ✅ Benefits of This Approach

1. **Native Integration**: Uses Claude's own hook system
2. **No Polling**: Event-driven via hooks
3. **Bidirectional**: Can inject context back to Claude
4. **Transparent**: Claude doesn't know about the bridge
5. **Flexible**: Easy to add new MCP tools
6. **Debuggable**: All hook calls are logged

## 🎯 Implementation Priority

1. **Phase 1**: Basic hook → MCP bridge (log_activity)
2. **Phase 2**: Full tool mapping (all 10 tools)
3. **Phase 3**: Bidirectional context injection
4. **Phase 4**: Advanced NLP intent detection

This architecture provides a **complete bridge** between Claude CLI and MCP without modifying Claude itself!