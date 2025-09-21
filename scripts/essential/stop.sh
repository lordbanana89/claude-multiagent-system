#!/bin/bash
# Unified Stop Script for Claude Multi-Agent System

echo "🛑 Stopping Claude Multi-Agent System"
echo "======================================"

# Kill Python processes
echo "Stopping Python services..."
pkill -f "mcp_server" 2>/dev/null || true
pkill -f "routes_api" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true

# Kill Node processes
echo "Stopping Frontend..."
pkill -f "vite" 2>/dev/null || true

# Kill TMUX sessions
echo "Stopping agent sessions..."
tmux kill-server 2>/dev/null || true

# Stop Redis
echo "Stopping Redis..."
redis-cli shutdown 2>/dev/null || true

echo "✅ All services stopped!"