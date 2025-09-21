#!/bin/bash
# MCP Server Launcher for Claude Desktop
# Workaround for connection issues

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Set Python path
export PYTHONPATH="/Users/erik/Desktop/claude-multiagent-system:$PYTHONPATH"

# Launch the server with explicit python path
exec /usr/local/bin/python3 mcp_server_fastmcp.py