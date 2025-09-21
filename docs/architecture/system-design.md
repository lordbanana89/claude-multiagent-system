# System Architecture

## Overview

The Claude Multi-Agent System employs a microservices architecture with specialized AI agents coordinated through a central orchestration layer. The system uses TMUX for process isolation, MCP v2 for communication, and multiple persistence layers for state management.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    React Dashboard (5173)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Monitor   │  │   Control   │  │  Analytics  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway (5001-5004)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Health API │  │   Auth API  │  │  Routes API │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (9999)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   JSON-RPC  │  │  WebSocket  │  │   Security  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent Orchestration Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Coordinator│  │   Router    │  │ Message Bus │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    TMUX Agent Sessions                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Supervisor│ │  Master  │ │ Backend  │ │ Database │ ...   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Persistence Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │mcp_system.db│  │shared_inbox │  │   auth.db   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Process Management Layer

**Technology**: Overmind + TMUX
- **Overmind**: Process orchestrator using Procfile.tmux
- **TMUX**: Isolated sessions for each agent
- **TTY**: Terminal access for direct agent interaction

### 2. Communication Layer

**MCP v2 Protocol Implementation**
- JSON-RPC 2.0 for method invocation
- WebSocket support for real-time communication
- OAuth 2.1 for secure authentication
- Request/Response and Push notification patterns

### 3. Agent Layer

**9 Specialized Claude Agents**:

| Agent | Responsibility | Port | Session |
|-------|---------------|------|---------|
| Supervisor | Task coordination | 8089 | claude-supervisor |
| Master | Supreme command | 8088 | claude-master |
| Backend API | API development | 8090 | claude-backend-api |
| Database | Data management | 8091 | claude-database |
| Frontend UI | UI development | 8092 | claude-frontend-ui |
| Testing | Quality assurance | 8094 | claude-testing |
| Queue Manager | Task queuing | 8095 | claude-queue-manager |
| Instagram | Social integration | 8093 | claude-instagram |
| Deployment | DevOps operations | 8096 | claude-deployment |

### 4. API Gateway

**FastAPI Services**:
- **Port 5001**: Health monitoring and system status
- **Port 5002**: Authentication and authorization
- **Port 5003**: Main routing and API endpoints
- **Port 5004**: Complete authentication service

### 5. Data Persistence

**SQLite Databases**:

#### mcp_system.db
- Agent registration and status
- Task management
- Activity logs
- System configuration

#### shared_inbox.db
- Inter-agent messages
- Broadcast notifications
- Message priority queuing

#### auth.db
- User authentication
- JWT token management
- Session tracking
- Access control

### 6. Message Queue

**Redis + Dramatiq**:
- Asynchronous task processing
- Message broker for agent communication
- Task retry and failure handling
- Priority queue management

## Security Architecture

### Authentication Flow

1. **User Authentication**: OAuth 2.1 with JWT tokens
2. **Agent Authorization**: Request approval system
3. **Inter-Agent Security**: Signed messages with timestamps
4. **Audit Trail**: Complete logging of all operations

### Request Management System

```python
RequestType:
  - BASH_COMMAND: Shell command execution
  - FILE_OPERATION: File system operations
  - API_CALL: External API requests
  - DATABASE_QUERY: Database operations
  - DEPLOYMENT: Production deployments

Risk Assessment:
  - LOW: Auto-approved (echo, status checks)
  - MEDIUM: Requires confirmation
  - HIGH: Manual approval required
  - CRITICAL: Multi-agent consensus
```

## Communication Patterns

### 1. Direct Messaging
Agent-to-agent direct communication via MCP protocol

### 2. Broadcast
System-wide notifications to all agents

### 3. Task Distribution
Supervisor delegates tasks to specialized agents

### 4. Consensus
Multiple agents vote on critical decisions

## Scalability Features

- **Dynamic Agent Creation**: Spawn new agents as needed
- **Load Balancing**: Distribute tasks across agents
- **Horizontal Scaling**: Add more agent instances
- **Connection Pooling**: Efficient resource utilization
- **Caching Layer**: Redis for frequently accessed data

## Monitoring and Observability

- **Real-time Dashboard**: Live agent status
- **Activity Logs**: Comprehensive audit trail
- **Performance Metrics**: Response times, success rates
- **Health Checks**: Automatic service monitoring
- **Alert System**: Notification of critical events

## Deployment Architecture

### Development Environment
- Local TMUX sessions
- SQLite databases
- Single Redis instance

### Production Environment
- Containerized agents (Docker/Kubernetes)
- PostgreSQL for persistence
- Redis cluster for high availability
- Load balancer for API gateway
- SSL/TLS encryption

## Recovery Mechanisms

- **Circuit Breakers**: Prevent cascade failures
- **Retry Logic**: Automatic retry with exponential backoff
- **State Recovery**: Persistent state across restarts
- **Rollback Support**: Version-controlled deployments
- **Backup Strategy**: Regular database snapshots