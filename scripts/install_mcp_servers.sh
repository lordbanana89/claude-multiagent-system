#!/bin/bash
#
# Install MCP Servers - Complete Integration Script
# This script installs all essential MCP servers for the multi-agent system
#

set -e

echo "🚀 Installing MCP Servers for Multi-Agent System"
echo "================================================"

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 18+ required. Current version: $(node -v)"
    exit 1
fi

# Base directory
BASE_DIR="/Users/erik/Desktop/claude-multiagent-system"
cd "$BASE_DIR"

# Phase 1: Core MCP Servers (Official)
echo ""
echo "📦 Phase 1: Installing Official MCP Servers..."
echo "----------------------------------------------"

npm install --save \
    @modelcontextprotocol/sdk \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-git \
    @modelcontextprotocol/server-memory \
    @modelcontextprotocol/server-fetch \
    @modelcontextprotocol/server-sequentialthinking \
    @modelcontextprotocol/server-time \
    @modelcontextprotocol/server-everything

echo "✅ Official servers installed"

# Phase 2: Community Essential Servers
echo ""
echo "📦 Phase 2: Installing Community Essential Servers..."
echo "-----------------------------------------------------"

# Playwright MCP for browser automation
echo "Installing Playwright MCP..."
npm install --save @executeautomation/mcp-playwright || \
    npx @michaellatman/mcp-get@latest install mcp-playwright

# SQLite for local database
echo "Installing SQLite MCP..."
npm install --save @modelcontextprotocol/server-sqlite || echo "⚠️ SQLite server may need manual setup"

# Phase 3: Create server configurations
echo ""
echo "⚙️ Phase 3: Creating Server Configurations..."
echo "----------------------------------------------"

# Create config directory
mkdir -p "$BASE_DIR/config/mcp-servers"

# Generate individual server configs
cat > "$BASE_DIR/config/mcp-servers/filesystem.json" << 'EOF'
{
  "name": "filesystem",
  "command": "node",
  "args": ["node_modules/@modelcontextprotocol/server-filesystem/dist/index.js"],
  "env": {
    "ALLOWED_DIRECTORIES": "/Users/erik/Desktop/claude-multiagent-system"
  }
}
EOF

cat > "$BASE_DIR/config/mcp-servers/git.json" << 'EOF'
{
  "name": "git",
  "command": "node",
  "args": ["node_modules/@modelcontextprotocol/server-git/dist/index.js"],
  "env": {
    "REPO_PATH": "/Users/erik/Desktop/claude-multiagent-system"
  }
}
EOF

cat > "$BASE_DIR/config/mcp-servers/memory.json" << 'EOF'
{
  "name": "memory",
  "command": "node",
  "args": ["node_modules/@modelcontextprotocol/server-memory/dist/index.js"],
  "env": {
    "DB_PATH": "/Users/erik/Desktop/claude-multiagent-system/data/memory.db"
  }
}
EOF

cat > "$BASE_DIR/config/mcp-servers/fetch.json" << 'EOF'
{
  "name": "fetch",
  "command": "node",
  "args": ["node_modules/@modelcontextprotocol/server-fetch/dist/index.js"],
  "env": {}
}
EOF

cat > "$BASE_DIR/config/mcp-servers/sequential-thinking.json" << 'EOF'
{
  "name": "sequential-thinking",
  "command": "node",
  "args": ["node_modules/@modelcontextprotocol/server-sequentialthinking/dist/index.js"],
  "env": {}
}
EOF

echo "✅ Server configurations created"

# Phase 4: Verify installations
echo ""
echo "🔍 Phase 4: Verifying Installations..."
echo "---------------------------------------"

# Check if main servers are accessible
for server in filesystem git memory fetch; do
    if [ -f "node_modules/@modelcontextprotocol/server-$server/dist/index.js" ]; then
        echo "✅ $server server: OK"
    else
        echo "❌ $server server: NOT FOUND"
    fi
done

# Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p "$BASE_DIR/data/state"
mkdir -p "$BASE_DIR/data/memory"
mkdir -p "$BASE_DIR/data/cache"

# Final summary
echo ""
echo "========================================="
echo "✨ MCP Server Installation Complete!"
echo "========================================="
echo ""
echo "Installed servers:"
echo "  • Filesystem - Secure file operations"
echo "  • Git - Version control integration"
echo "  • Memory - Knowledge graph persistence"
echo "  • Fetch - Web content retrieval"
echo "  • Sequential Thinking - Advanced reasoning"
echo "  • Time - Scheduling and timezone"
echo "  • Everything - Reference implementation"
echo ""
echo "Next steps:"
echo "1. Run: npm run start-mcp"
echo "2. Test: npm run test-mcp"
echo "3. Configure agents in claude_mcp_config.json"
echo ""