#!/bin/bash
# Setup Claude Code hooks for MCP bridge integration

echo "🔧 Setting up Claude Code hooks for MCP bridge..."

# Create hooks directory structure
PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"

echo "📁 Creating hooks directory at: $HOOKS_DIR"
mkdir -p "$HOOKS_DIR"

# Create the hook configuration
echo "📝 Creating hooks configuration..."
cat > "$HOOKS_DIR/settings.toml" << 'EOF'
# Claude Code Hooks Configuration for MCP Bridge

[hooks.pre_tool_use]
command = "python3 /Users/erik/Desktop/claude-multiagent-system/mcp_bridge.py pre_tool_use"
enabled = true
description = "Intercept before tool execution for MCP coordination"

[hooks.post_tool_use]
command = "python3 /Users/erik/Desktop/claude-multiagent-system/mcp_bridge.py post_tool_use"
enabled = true
description = "Process tool results for MCP logging"

[hooks.notification]
command = "python3 /Users/erik/Desktop/claude-multiagent-system/mcp_bridge.py notification"
enabled = true
description = "Capture Claude notifications for MCP"

[hooks.stop]
command = "python3 /Users/erik/Desktop/claude-multiagent-system/mcp_bridge.py stop"
enabled = true
description = "Handle session end for MCP cleanup"
EOF

# Make bridge executable
chmod +x "$PROJECT_DIR/mcp_bridge.py"

# Create test script
echo "🧪 Creating test script..."
cat > "$PROJECT_DIR/test_mcp_bridge.py" << 'EOF'
#!/usr/bin/env python3
"""Test MCP Bridge functionality"""

import json
import sys
import subprocess

def test_bridge():
    """Test the MCP bridge with sample data"""

    test_cases = [
        {
            "event": "notification",
            "data": {
                "content": "I'll use the log_activity tool to record starting the backend API implementation"
            }
        },
        {
            "event": "notification",
            "data": {
                "content": "Checking for conflicts with /api/users endpoint"
            }
        },
        {
            "event": "notification",
            "data": {
                "content": "Registering component: api:/api/users"
            }
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test['event']}")
        print(f"   Input: {test['data']['content'][:50]}...")

        # Run bridge with test data
        result = subprocess.run(
            ["python3", "/Users/erik/Desktop/claude-multiagent-system/mcp_bridge.py", test["event"]],
            input=json.dumps(test["data"]),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            response = json.loads(result.stdout)
            if response.get("systemMessage"):
                print(f"   ✅ Result: {response['systemMessage']}")
            else:
                print(f"   ✅ Passed through (no MCP tool detected)")
        else:
            print(f"   ❌ Error: {result.stderr}")

if __name__ == "__main__":
    print("🌉 Testing MCP Bridge...")
    test_bridge()
EOF

chmod +x "$PROJECT_DIR/test_mcp_bridge.py"

echo ""
echo "✅ Claude hooks setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test the bridge: python3 $PROJECT_DIR/test_mcp_bridge.py"
echo "2. Start Claude agents with environment variable:"
echo "   export CLAUDE_AGENT_NAME=backend-api"
echo "   claude"
echo ""
echo "🔍 Monitor bridge activity:"
echo "   tail -f /tmp/mcp_bridge.log"
echo ""
echo "📊 Check MCP database:"
echo "   sqlite3 /tmp/mcp_state.db 'SELECT * FROM activities ORDER BY timestamp DESC LIMIT 5;'"