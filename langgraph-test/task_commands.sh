#!/bin/bash

# 🎯 Task Management Commands for Claude Agents
# Sourced in each tmux session for task lifecycle management

SHARED_STATE_FILE="/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_state.json"
AGENT_SESSION=$(tmux display-message -p '#S')

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current task ID for this agent
get_current_task() {
    if [ -f "$SHARED_STATE_FILE" ]; then
        python3 -c "
import json
import sys
try:
    with open('$SHARED_STATE_FILE', 'r') as f:
        state = json.load(f)

    agent_id = None
    for aid, agent in state['agents'].items():
        if agent['session_id'] == '$AGENT_SESSION':
            agent_id = aid
            break

    if agent_id and state['agents'][agent_id]['current_task']:
        print(state['agents'][agent_id]['current_task'])
    else:
        print('')
except:
    print('')
"
    fi
}

# Update task progress
task-progress() {
    local percentage=$1
    local task_id=$(get_current_task)

    if [ -z "$task_id" ]; then
        echo -e "${RED}❌ No active task found for this agent${NC}"
        return 1
    fi

    if [ -z "$percentage" ]; then
        echo -e "${YELLOW}Usage: task-progress <percentage>${NC}"
        echo -e "${BLUE}Example: task-progress 50${NC}"
        return 1
    fi

    # Validate percentage
    if ! [[ "$percentage" =~ ^[0-9]+$ ]] || [ "$percentage" -lt 0 ] || [ "$percentage" -gt 100 ]; then
        echo -e "${RED}❌ Invalid percentage. Must be between 0-100${NC}"
        return 1
    fi

    echo -e "${BLUE}📊 Updating task $task_id progress to $percentage%${NC}"

    # Call Python script to update SharedState
    python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('$SHARED_STATE_FILE', 'r') as f:
        state = json.load(f)

    # Find current task and update progress
    if state.get('current_task') and state['current_task']['task_id'] == '$task_id':
        state['current_task']['progress'] = float($percentage)
        state['last_updated'] = datetime.now().isoformat()

        with open('$SHARED_STATE_FILE', 'w') as f:
            json.dump(state, f, indent=2)

        print('✅ Progress updated successfully')
    else:
        print('❌ Task not found or not current')
        sys.exit(1)

except Exception as e:
    print(f'❌ Error updating progress: {e}')
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Task progress updated to $percentage%${NC}"
    else
        echo -e "${RED}❌ Failed to update progress${NC}"
    fi
}

# Complete task successfully
task-complete() {
    local message="$1"
    local task_id=$(get_current_task)

    if [ -z "$task_id" ]; then
        echo -e "${RED}❌ No active task found for this agent${NC}"
        return 1
    fi

    if [ -z "$message" ]; then
        message="Task completed successfully"
    fi

    echo -e "${GREEN}🎉 Completing task $task_id${NC}"
    echo -e "${BLUE}📝 Message: $message${NC}"

    # Call Python script to complete task
    python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('$SHARED_STATE_FILE', 'r') as f:
        state = json.load(f)

    # Find agent ID for this session
    agent_id = None
    for aid, agent in state['agents'].items():
        if agent['session_id'] == '$AGENT_SESSION':
            agent_id = aid
            break

    if not agent_id:
        print('❌ Agent not found')
        sys.exit(1)

    # Complete the task
    if state.get('current_task') and state['current_task']['task_id'] == '$task_id':
        # Move task to history
        completed_task = state['current_task'].copy()
        completed_task['status'] = 'completed'
        completed_task['progress'] = 100.0
        completed_task['completed_at'] = datetime.now().isoformat()
        completed_task['results'][agent_id] = '$message'

        state['task_history'].append(completed_task)

        # Clear current task if all agents completed
        all_completed = True
        for aid in completed_task['assigned_agents']:
            if aid not in completed_task['results']:
                all_completed = False
                break

        if all_completed:
            state['current_task'] = None
            state['system_status'] = 'idle'

        # Update agent status
        state['agents'][agent_id]['status'] = 'idle'
        state['agents'][agent_id]['current_task'] = None
        state['agents'][agent_id]['last_activity'] = datetime.now().isoformat()

        state['last_updated'] = datetime.now().isoformat()

        # Keep only last 50 tasks in history
        if len(state['task_history']) > 50:
            state['task_history'] = state['task_history'][-50:]

        with open('$SHARED_STATE_FILE', 'w') as f:
            json.dump(state, f, indent=2)

        print('✅ Task completed successfully')
    else:
        print('❌ Task not found or not current')
        sys.exit(1)

except Exception as e:
    print(f'❌ Error completing task: {e}')
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Task completed! Agent is now IDLE${NC}"
        echo -e "${BLUE}💡 Ready for new tasks${NC}"
    else
        echo -e "${RED}❌ Failed to complete task${NC}"
    fi
}

# Fail task with reason
task-fail() {
    local reason="$1"
    local task_id=$(get_current_task)

    if [ -z "$task_id" ]; then
        echo -e "${RED}❌ No active task found for this agent${NC}"
        return 1
    fi

    if [ -z "$reason" ]; then
        echo -e "${YELLOW}Usage: task-fail <reason>${NC}"
        echo -e "${BLUE}Example: task-fail \"Unable to access database\"${NC}"
        return 1
    fi

    echo -e "${RED}❌ Failing task $task_id${NC}"
    echo -e "${YELLOW}📝 Reason: $reason${NC}"

    # Call Python script to fail task
    python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('$SHARED_STATE_FILE', 'r') as f:
        state = json.load(f)

    # Find agent ID for this session
    agent_id = None
    for aid, agent in state['agents'].items():
        if agent['session_id'] == '$AGENT_SESSION':
            agent_id = aid
            break

    if not agent_id:
        print('❌ Agent not found')
        sys.exit(1)

    # Fail the task
    if state.get('current_task') and state['current_task']['task_id'] == '$task_id':
        # Update task status
        state['current_task']['status'] = 'failed'
        state['current_task']['error_message'] = '$reason'
        state['current_task']['completed_at'] = datetime.now().isoformat()

        # Move to history
        state['task_history'].append(state['current_task'].copy())
        state['current_task'] = None
        state['system_status'] = 'idle'

        # Update agent status
        state['agents'][agent_id]['status'] = 'error'
        state['agents'][agent_id]['current_task'] = None
        state['agents'][agent_id]['error_message'] = '$reason'
        state['agents'][agent_id]['last_activity'] = datetime.now().isoformat()

        state['last_updated'] = datetime.now().isoformat()

        with open('$SHARED_STATE_FILE', 'w') as f:
            json.dump(state, f, indent=2)

        print('✅ Task failed and logged')
    else:
        print('❌ Task not found or not current')
        sys.exit(1)

except Exception as e:
    print(f'❌ Error failing task: {e}')
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        echo -e "${RED}❌ Task failed and logged${NC}"
        echo -e "${BLUE}💡 Use 'task-status' to see current state${NC}"
    else
        echo -e "${RED}❌ Failed to log task failure${NC}"
    fi
}

# Show current task status
task-status() {
    local task_id=$(get_current_task)

    if [ -z "$task_id" ]; then
        echo -e "${BLUE}📋 No active task for this agent${NC}"
        echo -e "${GREEN}✅ Agent is IDLE and ready for new tasks${NC}"
        return 0
    fi

    echo -e "${BLUE}📋 Current Task Status${NC}"
    echo -e "${YELLOW}Task ID: $task_id${NC}"

    # Get detailed task info
    python3 -c "
import json
try:
    with open('$SHARED_STATE_FILE', 'r') as f:
        state = json.load(f)

    if state.get('current_task'):
        task = state['current_task']
        print(f\"Description: {task['description']}\")
        print(f\"Progress: {task['progress']}%\")
        print(f\"Status: {task['status']}\")
        print(f\"Created: {task['created_at']}\")
        print(f\"Started: {task['started_at']}\")
        print(f\"Assigned Agents: {', '.join(task['assigned_agents'])}\")
    else:
        print('No current task found')
except:
    print('Error reading task status')
"
}

# Show available commands
task-help() {
    echo -e "${BLUE}🎯 Task Management Commands${NC}"
    echo ""
    echo -e "${GREEN}task-status${NC}        - Show current task information"
    echo -e "${GREEN}task-progress <0-100>${NC} - Update task progress percentage"
    echo -e "${GREEN}task-complete [msg]${NC}  - Mark task as completed with optional message"
    echo -e "${GREEN}task-fail <reason>${NC}   - Mark task as failed with reason"
    echo -e "${GREEN}task-help${NC}           - Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "${BLUE}  task-progress 75${NC}"
    echo -e "${BLUE}  task-complete \"API endpoints implemented\"${NC}"
    echo -e "${BLUE}  task-fail \"Database connection failed\"${NC}"
}

# Auto-show current task when commands are loaded
echo -e "${BLUE}🎯 Task Management Commands Loaded${NC}"
echo -e "${YELLOW}Type 'task-help' for available commands${NC}"
task-status