#!/bin/bash

echo "🔍 Testing MCP Inspector Compatibility"
echo "======================================"

# Test basic MCP server response
echo ""
echo "1. Testing MCP Server initialization..."

python3 -c "
import subprocess
import json
import sys

# Start MCP server
proc = subprocess.Popen(
    ['python3', 'mcp_server_fastmcp.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send initialize request
init_request = {
    'jsonrpc': '2.0',
    'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {
            'tools': {'listChanged': True}
        },
        'clientInfo': {
            'name': 'mcp-inspector',
            'version': '1.0.0'
        }
    },
    'id': 1
}

proc.stdin.write(json.dumps(init_request) + '\n')
proc.stdin.flush()

# Read response
import select
ready = select.select([proc.stdout], [], [], 2)
if ready[0]:
    response = proc.stdout.readline()
    if response:
        data = json.loads(response)
        if 'result' in data:
            print('✅ Initialize: SUCCESS')
            print(f'   Protocol: {data[\"result\"].get(\"protocolVersion\", \"unknown\")}')
            print(f'   Server: {data[\"result\"][\"serverInfo\"][\"name\"]}')
        else:
            print('❌ Initialize: FAILED')
    else:
        print('❌ No response from server')
else:
    print('❌ Server timeout')

# Send tools/list request
tools_request = {
    'jsonrpc': '2.0',
    'method': 'tools/list',
    'params': {},
    'id': 2
}

proc.stdin.write(json.dumps(tools_request) + '\n')
proc.stdin.flush()

ready = select.select([proc.stdout], [], [], 2)
if ready[0]:
    response = proc.stdout.readline()
    if response:
        data = json.loads(response)
        if 'result' in data and 'tools' in data['result']:
            tools = data['result']['tools']
            print(f'✅ Tools List: {len(tools)} tools found')
            for tool in tools[:3]:
                print(f'   - {tool[\"name\"]}: {tool.get(\"description\", \"No description\")[:50]}...')
        else:
            print('❌ Tools List: FAILED')

proc.terminate()
"

echo ""
echo "2. Testing with actual MCP Inspector..."
echo ""
echo "To test with the official MCP Inspector, run:"
echo "  npx @modelcontextprotocol/inspector python mcp_server_fastmcp.py"
echo ""
echo "Expected behavior:"
echo "  - Opens browser at http://localhost:5173"
echo "  - Shows 11 available tools"
echo "  - Allows testing each tool interactively"
echo ""
echo "======================================"