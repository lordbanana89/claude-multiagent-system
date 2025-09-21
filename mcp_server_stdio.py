#!/usr/bin/env python3
"""
MCP Server with proper stdio handling for Claude Desktop
Based on FastMCP but with explicit stdio support
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging to stderr so it doesn't interfere with stdio
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

# Import the server
from mcp_server_fastmcp import mcp

if __name__ == "__main__":
    # Run with stdio mode
    import mcp.server.stdio

    # Run the server with stdio
    asyncio.run(mcp.server.stdio.stdio_server(
        mcp.app,
        mcp.name,
        "1.0.0"
    ))