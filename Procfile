# Claude Multi-Agent System - Process Management with Overmind
# Each process will run in its own tmux pane managed by Overmind
# Access any agent with: overmind connect <process_name>

# Core Claude Agents (will start Claude CLI in interactive mode)
supervisor: echo "Starting Claude Supervisor..." && claude
master: echo "Starting Claude Master..." && claude
backend: echo "Starting Claude Backend API..." && claude
database: echo "Starting Claude Database..." && claude
frontend: echo "Starting Claude Frontend UI..." && claude
instagram: echo "Starting Claude Instagram..." && claude
testing: echo "Starting Claude Testing..." && claude
queue: echo "Starting Claude Queue Manager..." && claude
deployment: echo "Starting Claude Deployment..." && claude

# Support Services
web: streamlit run interfaces/web/complete_integration.py --server.port 8501
redis: redis-server --port 6379

# Queue Worker - Processes messages from Redis
dramatiq: python -m dramatiq task_queue.worker --processes 2 --threads 4

# Notes:
# - Each Claude agent starts with an echo to show initialization
# - Use 'overmind connect <name>' to attach to any agent (e.g., 'overmind connect supervisor')
# - Use 'overmind restart <name>' to restart individual agents
# - Use 'overmind ps' to see all process statuses
# - Use 'overmind kill' to stop everything