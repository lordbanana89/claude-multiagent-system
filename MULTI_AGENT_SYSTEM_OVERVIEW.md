# Multi-Agent Coordination System

## Overview
A lightweight task coordination system for managing multiple specialized agents with small, focused tasks (max 5 words each).

## System Components

### 1. Core Scripts

#### `/supervisor_coordinator.py`
- Basic coordination with 30-second cycles
- Sends heartbeat checks
- Assigns micro-tasks
- Monitors agent responses

#### `/supervisor_daemon.py`
- Advanced background coordinator
- Multi-phase task execution
- State persistence
- Priority-based task queue
- Automatic phase progression
- Coordination event logging

#### `/agent_responder.py`
- Simulates agent responses
- Processes pending tasks
- Updates heartbeat status
- Returns task completions

### 2. Management Tools

#### `/control_agents.sh`
Main control script with commands:
- `start` - Start all agents and supervisor
- `stop` - Stop all processes
- `restart` - Restart the system
- `status` - Show current status
- `monitor` - Launch interactive dashboard
- `logs` - Show recent logs
- `clean` - Clean database and logs

#### `/monitor_dashboard.py`
- Real-time system monitoring
- Agent status tracking
- Task statistics
- Recent activity log
- Coordination events

#### `/check_status.py`
- Quick status snapshot
- Process verification
- Task counts per agent
- Recent activity summary

### 3. Helper Scripts

#### `/start_all_responders.sh`
- Starts all 8 agent responders
- Runs them in background
- Logs to `/tmp/<agent>.log`

## Database Schema

Located at: `/langgraph-test/shared_inbox.db`

### Tables:

1. **inbox**
   - `id` - Task identifier
   - `agent` - Target agent name
   - `task` - Task description (max 5 words)
   - `status` - pending/completed
   - `priority` - Task priority (1-10)
   - `response` - Agent response
   - `created_at` - Task creation time
   - `completed_at` - Task completion time

2. **heartbeat**
   - `agent` - Agent name
   - `last_seen` - Last heartbeat time
   - `status` - Agent status
   - `tasks_completed` - Completion count

3. **coordination_log**
   - `id` - Event identifier
   - `timestamp` - Event time
   - `event` - Event type
   - `details` - Event details

## Available Agents

1. **master** - System core coordination
2. **backend-api** - REST APIs and server logic
3. **database** - Schema and data management
4. **frontend-ui** - React/UI components
5. **testing** - Test suite management
6. **instagram** - Social media integration
7. **queue-manager** - Job queue handling
8. **deployment** - Docker and CI/CD

## Task Phases

### Phase 1 - System Setup
- Initialize core systems
- Create basic infrastructure
- Setup development environment

### Phase 2 - Implementation
- Build features
- Add integrations
- Implement business logic

## Key Features

1. **Small Task Focus**
   - All tasks limited to 5 words
   - Promotes clarity and precision
   - Prevents agent overload

2. **Automatic Coordination**
   - 10-second coordination cycles
   - Heartbeat monitoring
   - Automatic task assignment

3. **State Persistence**
   - Saves progress to JSON
   - Survives restarts
   - Tracks statistics

4. **Real-time Monitoring**
   - Interactive dashboard
   - Process status tracking
   - Task completion metrics

## Usage

### Start System
```bash
./control_agents.sh start
```

### Check Status
```bash
./control_agents.sh status
```

### Monitor Dashboard
```bash
./control_agents.sh monitor
```

### Stop System
```bash
./control_agents.sh stop
```

## File Locations

- Main Scripts: `/Users/erik/Desktop/claude-multiagent-system/`
- Database: `/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_inbox.db`
- State File: `/Users/erik/Desktop/claude-multiagent-system/supervisor_state.json`
- Agent Logs: `/tmp/<agent-name>.log`
- Supervisor Log: `/tmp/supervisor.log`

## Architecture Principles

1. **Simplicity** - Keep tasks small and focused
2. **Coherence** - Maintain agent state consistency
3. **Visibility** - Clear monitoring and logging
4. **Resilience** - Handle failures gracefully
5. **Scalability** - Easy to add new agents/tasks