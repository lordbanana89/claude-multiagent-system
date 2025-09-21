# Claude Multi-Agent System Overview

## System Purpose

The Claude Multi-Agent System is a production-ready orchestration platform that coordinates 9 specialized Claude AI agents to collaboratively develop software projects. Each agent has specific expertise and runs in its own TMUX session, communicating through the MCP (Model Context Protocol) v2.

## Core Features

- **9 Specialized Agents**: Each focused on specific development domains
- **MCP v2 Protocol**: Industry-standard inter-agent communication
- **Real-time Dashboard**: React-based monitoring and control interface
- **Task Orchestration**: Automated task distribution and workflow management
- **Security Framework**: Enterprise-grade security with OAuth 2.1 and JWT
- **Persistent State**: SQLite databases for state, messaging, and authentication

## System Architecture

```
User Interface (React Dashboard)
        ↓
   API Gateway (FastAPI)
        ↓
  MCP Server (Port 9999)
        ↓
   Agent Orchestrator
        ↓
  9 Specialized Agents
  (TMUX Sessions)
```

## Agent Roster

1. **Supervisor Agent** - Strategic oversight and task coordination
2. **Master Agent** - Supreme command authority and crisis management
3. **Backend API Agent** - API development and server-side logic
4. **Database Agent** - Database design and data management
5. **Frontend UI Agent** - User interface and UX development
6. **Testing Agent** - Quality assurance and automated testing
7. **Queue Manager Agent** - Message queue and async task management
8. **Instagram Agent** - Social media integration specialist
9. **Deployment Agent** - DevOps and production deployment

## Technology Stack

### Backend
- Python 3.11+ with FastAPI
- SQLite for persistence
- Redis for message queuing
- Dramatiq for task processing

### Frontend
- React 19 with TypeScript
- Tailwind CSS for styling
- Zustand for state management
- TanStack Query for data fetching
- Vite for build tooling

### Infrastructure
- TMUX for agent session management
- Overmind for process orchestration
- MCP v2 for inter-agent communication
- OAuth 2.1 for authentication

## System Status

Current operational status: **85% functional**

- ✅ Core infrastructure operational
- ✅ All 9 agents active and responsive
- ✅ MCP v2 protocol implemented
- ✅ Dashboard monitoring functional
- ✅ Task lifecycle management complete
- ⚠️ Advanced workflows in development
- ⚠️ Some integration features pending

## Use Cases

- **Complex Software Development**: Coordinated multi-domain development
- **Automated Testing**: Comprehensive test suite generation
- **API Development**: Full-stack API design and implementation
- **Database Design**: Schema design and optimization
- **UI/UX Development**: Modern React applications
- **DevOps Automation**: CI/CD pipeline management

## Next Steps

- Review the [Quickstart Guide](./quickstart.md) to get the system running
- Explore [Agent Documentation](../agents/) to understand each agent's capabilities
- Check [Architecture Documentation](../architecture/system-design.md) for technical details