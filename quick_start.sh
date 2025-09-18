#!/bin/bash
# Quick Start Script for Claude Multi-Agent System

echo "🤖 CLAUDE MULTI-AGENT SYSTEM - QUICK START"
echo "=========================================="
echo ""

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "📁 Project Directory: $PROJECT_DIR"
echo ""

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found!"
    echo "Expected: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "1️⃣ Installing Dependencies..."
python3 core/install_enhanced_dependencies.py

echo ""
echo "2️⃣ Creating Claude Session..."
chmod +x scripts/start_claude.sh
./scripts/start_claude.sh

echo ""
echo "3️⃣ Starting Web Interface..."
echo "🌐 Launching working prototype on http://localhost:8506"
python3 -m streamlit run interfaces/web/working_prototype.py --server.port=8506 &

echo ""
echo "✅ SETUP COMPLETE!"
echo ""
echo "🔧 Next Steps:"
echo "1. Attach to Claude session: tmux attach -t claude-test"
echo "2. Verify Claude is running and responsive"
echo "3. Detach: Ctrl+B then D"
echo "4. Access web interface: http://localhost:8506"
echo ""
echo "📚 Documentation: docs/MULTI_AGENT_DOCUMENTATION.md"
echo "🗺️ Project Map: docs/PROJECT_MAPPING.md"