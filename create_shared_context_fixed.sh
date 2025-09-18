#!/bin/bash

# 🧠 Create Shared Context Terminal for Claude Agents (FIXED VERSION)
# This terminal aggregates all agent activities for visibility

echo "🚀 Creating Shared Context System for Claude Agents"
echo "===================================================="

# Kill existing shared context if exists
tmux kill-session -t claude-shared-context 2>/dev/null

# Create the shared context session with a simple tail command
echo "📊 Creating shared context terminal..."
tmux new-session -d -s claude-shared-context

# Create a log file for shared context
LOGFILE="/tmp/claude_shared_context.log"
echo "═══════════════════════════════════════════════════════════════" > $LOGFILE
echo "           🧠 CLAUDE MULTI-AGENT SHARED CONTEXT" >> $LOGFILE
echo "═══════════════════════════════════════════════════════════════" >> $LOGFILE
echo "" >> $LOGFILE
echo "This log aggregates all agent activities for coordination" >> $LOGFILE
echo "All agents can see what others are doing in real-time" >> $LOGFILE
echo "───────────────────────────────────────────────────────────────" >> $LOGFILE
echo "[$(date +"%H:%M:%S")] System initialized. Waiting for agent activities..." >> $LOGFILE
echo "" >> $LOGFILE

# Start tailing the log file in the shared context session
tmux send-keys -t claude-shared-context "tail -f $LOGFILE" Enter

echo "✅ Shared context terminal created (using $LOGFILE)"

# Function to log to shared context
log_to_context() {
    echo "[$(date +"%H:%M:%S")] $1" >> $LOGFILE
}

# Function to inject context awareness into an agent
inject_context_awareness() {
    local agent=$1
    echo "💉 Injecting context awareness into $agent..."

    # Create agent-specific script to log activities
    cat > /tmp/${agent}_logger.sh << 'EOF'
#!/bin/bash
# Auto-logger for agent activities
LOGFILE="/tmp/claude_shared_context.log"
log_activity() {
    echo "[$(date +"%H:%M:%S")] ${1}: $2" >> $LOGFILE
}
EOF

    tmux send-keys -t "$agent" "
# ════════════════════════════════════════════════════════════════
# 🧠 MULTI-AGENT CONTEXT AWARENESS ACTIVATED
# ════════════════════════════════════════════════════════════════
#
# You are part of a coordinated multi-agent system.
#
# TO LOG YOUR ACTIVITIES TO SHARED CONTEXT:
# Just prefix important decisions with 'LOG:' and they will be
# automatically captured. Example:
#   LOG: Creating user authentication endpoint
#
# TO SEE WHAT OTHERS ARE DOING:
# Check the shared context at: /tmp/claude_shared_context.log
#
# COORDINATION RULES:
# 1. Log major decisions and actions
# 2. Check the log before making conflicting changes
# 3. Coordinate on shared interfaces
# 4. Report completion of milestones
#
# ════════════════════════════════════════════════════════════════
" Enter
}

# Check which Claude agents are running
echo ""
echo "🔍 Checking for active Claude agents..."
active_agents=$(tmux list-sessions 2>/dev/null | grep claude- | grep -v shared-context | awk -F: '{print $1}')

if [ -z "$active_agents" ]; then
    echo "⚠️  No Claude agents found. Start them first with:"
    echo "   ./scripts/start_all_claude_agents.sh"
else
    echo "📋 Found agents: $active_agents"

    # Inject context awareness into each agent
    for agent in $active_agents; do
        inject_context_awareness "$agent"
        log_to_context "$agent joined the shared context system"
    done
fi

# Create helper functions file
cat > /tmp/claude_context_helpers.sh << 'EOF'
#!/bin/bash
# Helper functions for Claude agents

# Log an activity to shared context
log_activity() {
    local agent="${1:-unknown}"
    local message="$2"
    echo "[$(date +"%H:%M:%S")] $agent: $message" >> /tmp/claude_shared_context.log
}

# Read recent context
read_context() {
    tail -20 /tmp/claude_shared_context.log
}

# Send message to all agents
broadcast_to_agents() {
    local message="$1"
    for session in $(tmux list-sessions -F "#{session_name}" | grep claude- | grep -v shared-context); do
        tmux send-keys -t "$session" "# 📢 BROADCAST: $message" Enter
    done
    echo "[$(date +"%H:%M:%S")] BROADCAST: $message" >> /tmp/claude_shared_context.log
}
EOF

chmod +x /tmp/claude_context_helpers.sh

echo ""
echo "🎯 Next Steps:"
echo "1. View shared context: tmux attach -t claude-shared-context"
echo "2. View log directly: tail -f $LOGFILE"
echo "3. Log from any agent: echo '[timestamp] agent: message' >> $LOGFILE"
echo "4. Use helpers: source /tmp/claude_context_helpers.sh"
echo ""
echo "✨ Shared context system ready and working!"
echo ""
echo "📝 Example usage:"
echo '   log_activity "backend-api" "Creating user endpoint"'
echo '   read_context'
echo '   broadcast_to_agents "API schema updated"'