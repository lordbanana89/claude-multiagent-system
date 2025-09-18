#!/bin/bash
# Claude Multi-Agent System - TMUX Session Management via Overmind
# This Procfile manages TMUX sessions that Claude Code agents connect to
# Start with: overmind start -f Procfile.tmux

# Core Claude Agent TMUX Sessions
# These create detached TMUX sessions that Claude Code can connect to
supervisor: tmux new-session -d -s claude-supervisor 2>/dev/null || tmux send-keys -t claude-supervisor "echo 'Supervisor session ready'" Enter; tail -f /dev/null
master: tmux new-session -d -s claude-master 2>/dev/null || tmux send-keys -t claude-master "echo 'Master session ready'" Enter; tail -f /dev/null
backend-api: tmux new-session -d -s claude-backend-api 2>/dev/null || tmux send-keys -t claude-backend-api "echo 'Backend API session ready'" Enter; tail -f /dev/null
database: tmux new-session -d -s claude-database 2>/dev/null || tmux send-keys -t claude-database "echo 'Database session ready'" Enter; tail -f /dev/null
frontend-ui: tmux new-session -d -s claude-frontend-ui 2>/dev/null || tmux send-keys -t claude-frontend-ui "echo 'Frontend UI session ready'" Enter; tail -f /dev/null
instagram: tmux new-session -d -s claude-instagram 2>/dev/null || tmux send-keys -t claude-instagram "echo 'Instagram session ready'" Enter; tail -f /dev/null
testing: tmux new-session -d -s claude-testing 2>/dev/null || tmux send-keys -t claude-testing "echo 'Testing session ready'" Enter; tail -f /dev/null
queue-manager: tmux new-session -d -s claude-queue-manager 2>/dev/null || tmux send-keys -t claude-queue-manager "echo 'Queue Manager session ready'" Enter; tail -f /dev/null
deployment: tmux new-session -d -s claude-deployment 2>/dev/null || tmux send-keys -t claude-deployment "echo 'Deployment session ready'" Enter; tail -f /dev/null

# Support Services
web: streamlit run interfaces/web/complete_integration.py --server.port 8501
# redis: redis-server --port 6379 --loglevel warning  # Commentato - Redis già attivo

# Queue Worker - Processes messages from Redis
dramatiq: python3 -m dramatiq task_queue.worker --processes 2 --threads 4

# Session Monitor (checks TMUX sessions are alive)
monitor: while true; do tmux ls 2>/dev/null | grep -E "claude-" | wc -l | xargs -I {} echo "Active Claude sessions: {}"; sleep 30; done

# Notes:
# - Each agent process creates/maintains a TMUX session
# - Use 'tmux attach -t claude-supervisor' to attach directly to a session
# - Use 'overmind connect monitor' to see session status
# - Use 'overmind restart <name>' to recreate a session if needed
# - Sessions persist even if Overmind restarts