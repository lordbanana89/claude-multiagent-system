#!/bin/bash

# 🧠 Create Shared Context Terminal for Claude Agents
# This terminal aggregates all agent activities for visibility

echo "🚀 Creating Shared Context System for Claude Agents"
echo "===================================================="

# Kill existing shared context if exists
tmux kill-session -t claude-shared-context 2>/dev/null

# Create the shared context session
echo "📊 Creating shared context terminal..."
tmux new-session -d -s claude-shared-context

# Initialize with header
tmux send-keys -t claude-shared-context "clear" Enter
tmux send-keys -t claude-shared-context "echo '═══════════════════════════════════════════════════════════════'" Enter
tmux send-keys -t claude-shared-context "echo '           🧠 CLAUDE MULTI-AGENT SHARED CONTEXT'" Enter
tmux send-keys -t claude-shared-context "echo '═══════════════════════════════════════════════════════════════'" Enter
tmux send-keys -t claude-shared-context "echo ''" Enter
tmux send-keys -t claude-shared-context "echo 'This terminal aggregates all agent activities for coordination'" Enter
tmux send-keys -t claude-shared-context "echo 'All agents can see what others are doing in real-time'" Enter
tmux send-keys -t claude-shared-context "echo ''" Enter
tmux send-keys -t claude-shared-context "echo '─────────────────────────────────────────────────────────────────'" Enter
tmux send-keys -t claude-shared-context "echo '[$(date +\"%H:%M:%S\")] System initialized. Waiting for agent activities...'" Enter
tmux send-keys -t claude-shared-context "echo ''" Enter

echo "✅ Shared context terminal created"

# Function to inject context awareness into an agent
inject_context_awareness() {
    local agent=$1
    echo "💉 Injecting context awareness into $agent..."

    tmux send-keys -t "$agent" "
# ════════════════════════════════════════════════════════════════
# 🧠 MULTI-AGENT CONTEXT AWARENESS ACTIVATED
# ════════════════════════════════════════════════════════════════
#
# You are part of a coordinated multi-agent system with:
# - claude-backend-api: Handles backend logic and APIs
# - claude-database: Manages database schema and queries
# - claude-frontend-ui: Develops user interface
# - claude-testing: Writes and runs tests
# - claude-supervisor: Coordinates overall tasks
#
# IMPORTANT COORDINATION RULES:
# 1. Before making changes, announce your intentions
# 2. Check what other agents are doing
# 3. Coordinate on shared interfaces (APIs, schemas, etc)
# 4. Report completion of major milestones
# 5. Ask for clarification if dependencies are unclear
#
# The shared context terminal shows all agent activities.
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
    done
fi

echo ""
echo "🎯 Next Steps:"
echo "1. View shared context: tmux attach -t claude-shared-context"
echo "2. Start context synchronizer: python3 context_synchronizer.py"
echo "3. Monitor with ttyd: ttyd -p 8099 tmux attach -t claude-shared-context"
echo ""
echo "✨ Shared context system ready!"