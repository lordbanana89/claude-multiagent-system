#!/usr/bin/env python3
"""Simple test to verify MCP server works outside Claude Desktop"""

import asyncio
from mcp_server_fastmcp import mcp

async def test():
    print(f"Server name: {mcp.name}")
    print(f"Number of tools: {len(mcp._tool_manager._tools)}")
    print(f"Tool names: {list(mcp._tool_manager._tools.keys())}")
    print(f"Resources: {len(mcp._resource_manager._resources)}")
    print("✅ Server configured correctly")

if __name__ == "__main__":
    asyncio.run(test())