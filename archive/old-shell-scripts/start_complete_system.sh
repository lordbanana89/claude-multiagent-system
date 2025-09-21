#!/bin/bash

# 🚀 Claude Multi-Agent System - Complete Integration Starter
# Script per avviare tutto il sistema completo

echo "🤖 Starting Claude Multi-Agent System - Complete Integration"
echo "=============================================================="
echo "⚠️  Legacy script detected. The recommended runtime is 'overmind start' (Procfile.tmux)."
echo "   Use this script only for manual troubleshooting." 

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command -v ttyd &> /dev/null; then
    echo "❌ ttyd not found. Installing..."
    brew install ttyd
fi

if ! command -v tmux &> /dev/null; then
    echo "❌ tmux not found. Installing..."
    brew install tmux
fi

echo "✅ Dependencies OK"

# Kill existing processes if any
echo "🧹 Cleaning up existing processes..."
pkill -f "langgraph dev" 2>/dev/null || true
pkill -f "streamlit run.*complete_integration" 2>/dev/null || true
pkill -f "ttyd -p 80" 2>/dev/null || true

# Start LangGraph dev server
echo "🔧 Starting LangGraph dev server..."
cd langgraph-test
langgraph dev --port 8080 --no-browser > /dev/null 2>&1 &
LANGGRAPH_PID=$!
echo "✅ LangGraph dev server started (PID: $LANGGRAPH_PID)"

# Wait for LangGraph to be ready
echo "⏳ Waiting for LangGraph to be ready..."
sleep 5

# Create test Claude sessions
echo "🎭 Creating test Claude sessions..."
tmux kill-session -t claude-backend-api 2>/dev/null || true
tmux kill-session -t claude-database 2>/dev/null || true
tmux kill-session -t claude-frontend-ui 2>/dev/null || true

tmux new-session -d -s claude-backend-api
tmux send-keys -t claude-backend-api "echo '🔧 Claude Backend API Agent Ready - Type: claude'" Enter
sleep 0.2
tmux send-keys -t claude-backend-api "source /Users/erik/Desktop/claude-multiagent-system/langgraph-test/task_commands.sh" Enter

tmux new-session -d -s claude-database
tmux send-keys -t claude-database "echo '💾 Claude Database Agent Ready - Type: claude'" Enter
sleep 0.2
tmux send-keys -t claude-database "source /Users/erik/Desktop/claude-multiagent-system/langgraph-test/task_commands.sh" Enter

tmux new-session -d -s claude-frontend-ui
tmux send-keys -t claude-frontend-ui "echo '🎨 Claude Frontend UI Agent Ready - Type: claude'" Enter
sleep 0.2
tmux send-keys -t claude-frontend-ui "source /Users/erik/Desktop/claude-multiagent-system/langgraph-test/task_commands.sh" Enter

echo "✅ Test sessions created"

# Start ttyd terminals
echo "🖥️ Starting web terminals..."
ttyd -p 8090 --writable -t "titleFixed=Backend API Agent" tmux attach -t claude-backend-api > /dev/null 2>&1 &
TTYD1_PID=$!

ttyd -p 8091 --writable -t "titleFixed=Database Agent" tmux attach -t claude-database > /dev/null 2>&1 &
TTYD2_PID=$!

ttyd -p 8092 --writable -t "titleFixed=Frontend UI Agent" tmux attach -t claude-frontend-ui > /dev/null 2>&1 &
TTYD3_PID=$!

ttyd -p 8093 --writable -t "titleFixed=Testing Agent" tmux attach -t claude-testing > /dev/null 2>&1 &
TTYD4_PID=$!

ttyd -p 8094 --writable -t "titleFixed=Instagram Agent" tmux attach -t claude-instagram > /dev/null 2>&1 &
TTYD5_PID=$!

echo "✅ Web terminals started (PIDs: $TTYD1_PID, $TTYD2_PID, $TTYD3_PID, $TTYD4_PID, $TTYD5_PID)"

# Wait for terminals to be ready
echo "⏳ Waiting for terminals to be ready..."
sleep 3

# Start Streamlit interface
echo "🌐 Starting Complete Integration Web Interface..."
cd ..
python3 -m streamlit run interfaces/web/complete_integration.py --server.port=8501 > /dev/null 2>&1 &
STREAMLIT_PID=$!

echo "✅ Streamlit interface started (PID: $STREAMLIT_PID)"

# Wait for Streamlit to be ready
echo "⏳ Waiting for web interface to be ready..."
sleep 5

# Display summary
echo ""
echo "🎉 SISTEMA COMPLETAMENTE ATTIVO!"
echo "================================="
echo ""
echo "🌐 Web Interface:     http://localhost:8501"
echo "🔧 LangGraph API:     http://localhost:8080"
echo "🎨 LangGraph Studio:  https://smith.langchain.com/studio/?baseUrl=http://localhost:8080"
echo ""
echo "🖥️ Web Terminals:"
echo "   Backend API:       http://localhost:8090"
echo "   Database:          http://localhost:8091"
echo "   Frontend UI:       http://localhost:8092"
echo ""
echo "📊 API Endpoints:"
echo "   API Docs:          http://localhost:8080/docs"
echo "   Health Check:      http://localhost:8080/health"
echo ""
echo "🎭 tmux Sessions:"
echo "   claude-backend-api"
echo "   claude-database"
echo "   claude-frontend-ui"
echo ""
echo "📋 Process IDs:"
echo "   LangGraph:   $LANGGRAPH_PID"
echo "   Streamlit:   $STREAMLIT_PID"
echo "   ttyd (8090): $TTYD1_PID"
echo "   ttyd (8091): $TTYD2_PID"
echo "   ttyd (8092): $TTYD3_PID"
echo ""
echo "🛑 To stop all services:"
echo "   kill $LANGGRAPH_PID $STREAMLIT_PID $TTYD1_PID $TTYD2_PID $TTYD3_PID"
echo ""
echo "🚀 Opening web interface in 3 seconds..."
sleep 3

# Try to open browser (macOS)
if command -v open &> /dev/null; then
    open http://localhost:8501
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501
fi

echo ""
echo "✨ Setup completo! Il sistema è pronto all'uso."
echo "💡 Usa la web interface per coordinare tutti gli agenti Claude."
