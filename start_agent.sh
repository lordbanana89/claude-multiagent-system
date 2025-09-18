#!/bin/bash

# Agent startup script with MCP integration
AGENT_NAME="${1:-backend-api}"
PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "🚀 Starting agent: $AGENT_NAME"

# Kill existing session
tmux kill-session -t "claude-$AGENT_NAME" 2>/dev/null

# Create new session
tmux new-session -d -s "claude-$AGENT_NAME"

# Navigate to project directory
tmux send-keys -t "claude-$AGENT_NAME" "cd $PROJECT_DIR" Enter

# Start Claude CLI
tmux send-keys -t "claude-$AGENT_NAME" "claude" Enter

# Wait for Claude to initialize
sleep 3

# Send initial context
tmux send-keys -t "claude-$AGENT_NAME" "
I am the $AGENT_NAME agent in a multi-agent system.

Available MCP tools for coordination:
- log_activity: Log activities to shared context
- check_conflicts: Check for conflicts before actions
- register_component: Register components I create
- update_status: Update my current status
- request_collaboration: Request help from other agents
- propose_decision: Propose decisions requiring consensus
- heartbeat: Keep my status active

To use a tool, say: 'I'll use the [tool_name] tool to [action]'

My responsibilities based on my role:
$(case $AGENT_NAME in
    backend-api) echo '- Create and manage API endpoints
- Implement business logic
- Handle authentication and authorization
- Data validation and processing';;
    database) echo '- Design and maintain database schema
- Create migrations and indexes
- Optimize queries
- Ensure data integrity';;
    frontend-ui) echo '- Build user interfaces
- Implement client-side logic
- Handle user interactions
- Styling and UX';;
    testing) echo '- Write unit and integration tests
- Create end-to-end tests
- Ensure code coverage
- Validate functionality';;
    supervisor) echo '- Coordinate between agents
- Assign and track tasks
- Resolve conflicts
- Monitor progress';;
    *) echo '- Perform assigned tasks
- Coordinate with other agents';;
esac)

I'll start by sending a heartbeat and checking current system status.
" Enter

# Send initial heartbeat
sleep 2
tmux send-keys -t "claude-$AGENT_NAME" "I'll use the heartbeat tool to indicate I'm active." Enter

echo "✅ Agent $AGENT_NAME started in session claude-$AGENT_NAME"
echo "   Connect with: tmux attach -t claude-$AGENT_NAME"
