# Claude Multi-Agent System - Project Context

## Project Overview
Production-ready multi-agent orchestration system with 9 specialized Claude agents managed via TMUX sessions and MCP v2 protocol.

## Quick Commands
```bash
# Start system
overmind start              # Uses Procfile.tmux to launch all agents

# Check agent status
tmux ls                      # List all TMUX sessions
sqlite3 mcp_system.db "SELECT * FROM agents;"  # Check agent database

# Access UI
open http://localhost:5173   # React dashboard
```

## Architecture
- **9 Specialized Agents**: supervisor, master, backend-api, database, frontend-ui, testing, queue-manager, instagram, deployment
- **MCP v2 Protocol**: Full implementation with OAuth 2.1 security
- **Frontend**: React 19 + TypeScript + Tailwind CSS
- **Backend**: Python FastAPI on ports 5001-5004, MCP on 9999
- **Databases**: mcp_system.db, shared_inbox.db, auth.db (SQLite)

## Development Workflow
1. Research and understand before implementing
2. Test changes locally before committing
3. Run type checking: `npm run typecheck` (frontend)
4. Never commit without explicit user request

## Code Style
- Python: Use type hints, follow PEP 8
- TypeScript: Strict mode enabled, use interfaces
- SQL: Use parameterized queries, never raw concatenation
- Comments: Only when explicitly requested

## Important Notes
- Agent instructions are in `/langgraph-test/*_INSTRUCTIONS.md`
- MCP server must be running for agent communication
- Each agent runs in isolated TMUX session
- Use Redis for async task queue (Dramatiq)

## Testing
```bash
# Frontend
cd claude-ui && npm test

# Backend
pytest tests/

# Integration
python tests/run_full_suite.py
```

## Security
- OAuth 2.1 for MCP authentication
- JWT tokens for API access
- Never expose secrets in logs or commits
- Use environment variables for sensitive data