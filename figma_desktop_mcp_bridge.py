#!/usr/bin/env python3
"""
Figma Desktop MCP Bridge
Connette Claude Desktop con Figma Desktop App
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional
import subprocess
import os
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class FigmaDesktopMCPBridge:
    def __init__(self):
        self.figma_token = "YOUR_FIGMA_TOKEN_HERE"
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": self.figma_token}

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})

        # Log per debug
        logger.info(f"Request: {method}")

        handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_list_tools,
            "tools/call": self.handle_tool_call,
            "resources/list": self.handle_list_resources,
            "resources/read": self.handle_read_resource,
            "prompts/list": self.handle_list_prompts,
            "prompts/get": self.handle_get_prompt,
        }

        handler = handlers.get(method, self.handle_unknown)
        return await handler(params)

    async def handle_initialize(self, params: Dict) -> Dict:
        """Initialize the MCP server"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {"subscribe": True},
                "prompts": {}
            },
            "serverInfo": {
                "name": "figma-desktop-bridge",
                "version": "1.0.0"
            }
        }

    async def handle_list_tools(self, params: Dict) -> Dict:
        """List available Figma tools"""
        return {
            "tools": [
                {
                    "name": "figma_list_files",
                    "description": "List all Figma files in your account",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "team_id": {
                                "type": "string",
                                "description": "Optional team ID to filter files"
                            }
                        }
                    }
                },
                {
                    "name": "figma_get_file",
                    "description": "Get details of a specific Figma file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "The file key from Figma URL"
                            }
                        },
                        "required": ["file_key"]
                    }
                },
                {
                    "name": "figma_get_components",
                    "description": "Get all components from a Figma file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "The file key from Figma URL"
                            }
                        },
                        "required": ["file_key"]
                    }
                },
                {
                    "name": "figma_get_styles",
                    "description": "Get all styles (colors, fonts, etc.) from a Figma file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "The file key from Figma URL"
                            }
                        },
                        "required": ["file_key"]
                    }
                },
                {
                    "name": "figma_export_node",
                    "description": "Export a specific node/frame as code",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "The file key"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "The node ID to export"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["react", "html", "vue", "css"],
                                "description": "Output format"
                            }
                        },
                        "required": ["file_key", "node_id"]
                    }
                },
                {
                    "name": "figma_open_in_desktop",
                    "description": "Open a Figma file in Desktop app",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_url": {
                                "type": "string",
                                "description": "Figma file URL"
                            }
                        },
                        "required": ["file_url"]
                    }
                }
            ]
        }

    async def handle_tool_call(self, params: Dict) -> Dict:
        """Execute a tool call"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        tools = {
            "figma_list_files": self.list_files,
            "figma_get_file": self.get_file,
            "figma_get_components": self.get_components,
            "figma_get_styles": self.get_styles,
            "figma_export_node": self.export_node,
            "figma_open_in_desktop": self.open_in_desktop,
        }

        if tool_name in tools:
            try:
                result = await tools[tool_name](arguments)
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            except Exception as e:
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

    async def list_files(self, args: Dict) -> Dict:
        """List Figma files"""
        team_id = args.get("team_id")

        if team_id:
            url = f"{self.base_url}/teams/{team_id}/projects"
        else:
            # Get user's files
            url = f"{self.base_url}/me/files"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_file(self, args: Dict) -> Dict:
        """Get Figma file details"""
        file_key = args.get("file_key")

        if not file_key:
            return {"error": "file_key required"}

        url = f"{self.base_url}/files/{file_key}"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                # Simplify response
                return {
                    "name": data.get("name"),
                    "lastModified": data.get("lastModified"),
                    "version": data.get("version"),
                    "components": len(data.get("components", {})),
                    "styles": len(data.get("styles", {})),
                    "document": self.simplify_node(data.get("document", {}))
                }
            else:
                return {"error": f"API returned {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_components(self, args: Dict) -> Dict:
        """Get components from file"""
        file_key = args.get("file_key")

        if not file_key:
            return {"error": "file_key required"}

        url = f"{self.base_url}/files/{file_key}/components"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_styles(self, args: Dict) -> Dict:
        """Get styles from file"""
        file_key = args.get("file_key")

        if not file_key:
            return {"error": "file_key required"}

        url = f"{self.base_url}/files/{file_key}/styles"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def export_node(self, args: Dict) -> Dict:
        """Export node as code"""
        file_key = args.get("file_key")
        node_id = args.get("node_id")
        format_type = args.get("format", "react")

        if not file_key or not node_id:
            return {"error": "file_key and node_id required"}

        # Get node data
        url = f"{self.base_url}/files/{file_key}/nodes?ids={node_id}"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                node_data = response.json()

                # Generate code based on format
                if format_type == "react":
                    code = self.generate_react_code(node_data)
                elif format_type == "html":
                    code = self.generate_html_code(node_data)
                else:
                    code = "// Format not yet implemented"

                return {"code": code, "format": format_type}
            else:
                return {"error": f"API returned {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def open_in_desktop(self, args: Dict) -> Dict:
        """Open file in Figma Desktop"""
        file_url = args.get("file_url")

        if not file_url:
            return {"error": "file_url required"}

        try:
            # Try to open with Figma Desktop
            subprocess.run(["open", "-a", "Figma", file_url])
            return {"success": True, "message": f"Opening {file_url} in Figma Desktop"}
        except Exception as e:
            return {"error": str(e)}

    def simplify_node(self, node: Dict, depth: int = 0) -> Dict:
        """Simplify node structure for readability"""
        if depth > 2:
            return {"type": node.get("type", "Unknown")}

        simplified = {
            "type": node.get("type"),
            "name": node.get("name"),
        }

        if "children" in node and depth < 2:
            simplified["children"] = [
                self.simplify_node(child, depth + 1)
                for child in node.get("children", [])[:3]
            ]

        return simplified

    def generate_react_code(self, node_data: Dict) -> str:
        """Generate React code from node data"""
        nodes = node_data.get("nodes", {})
        if not nodes:
            return "// No node data found"

        # Get first node
        node = list(nodes.values())[0] if nodes else {}
        document = node.get("document", {})

        component_name = document.get("name", "Component").replace(" ", "")

        code = f"""import React from 'react';

const {component_name} = () => {{
  return (
    <div className="{self.get_tailwind_classes(document)}">
      {self.generate_jsx(document)}
    </div>
  );
}};

export default {component_name};"""

        return code

    def generate_html_code(self, node_data: Dict) -> str:
        """Generate HTML code from node data"""
        nodes = node_data.get("nodes", {})
        if not nodes:
            return "<!-- No node data found -->"

        node = list(nodes.values())[0] if nodes else {}
        document = node.get("document", {})

        return f"""<!DOCTYPE html>
<html>
<head>
  <style>
    {self.generate_css(document)}
  </style>
</head>
<body>
  {self.generate_html_element(document)}
</body>
</html>"""

    def get_tailwind_classes(self, node: Dict) -> str:
        """Generate Tailwind classes from node properties"""
        classes = []

        # Layout
        if node.get("layoutMode") == "HORIZONTAL":
            classes.append("flex flex-row")
        elif node.get("layoutMode") == "VERTICAL":
            classes.append("flex flex-col")

        # Spacing
        if "paddingLeft" in node:
            classes.append(f"p-{int(node['paddingLeft'] / 4)}")

        # Colors
        if "backgroundColor" in node:
            classes.append("bg-white")

        return " ".join(classes)

    def generate_jsx(self, node: Dict) -> str:
        """Generate JSX from node"""
        if node.get("type") == "TEXT":
            return f'{{"{node.get("characters", "")}"}}'

        children = node.get("children", [])
        if children:
            child_jsx = "\n".join([self.generate_jsx(child) for child in children[:5]])
            return child_jsx

        return f'{{/* {node.get("name", "Component")} */}}'

    def generate_css(self, node: Dict) -> str:
        """Generate CSS from node"""
        return """
    body { font-family: system-ui, -apple-system, sans-serif; }
    .container { padding: 20px; }
        """

    def generate_html_element(self, node: Dict) -> str:
        """Generate HTML element from node"""
        if node.get("type") == "TEXT":
            return f'<span>{node.get("characters", "")}</span>'

        children = node.get("children", [])
        if children:
            child_html = "\n".join([self.generate_html_element(child) for child in children[:5]])
            return f'<div class="container">\n{child_html}\n</div>'

        return f'<div><!-- {node.get("name", "Component")} --></div>'

    async def handle_list_resources(self, params: Dict) -> Dict:
        """List available resources"""
        return {"resources": []}

    async def handle_read_resource(self, params: Dict) -> Dict:
        """Read a resource"""
        return {"contents": []}

    async def handle_list_prompts(self, params: Dict) -> Dict:
        """List available prompts"""
        return {
            "prompts": [
                {
                    "name": "generate_component",
                    "description": "Generate React component from Figma design",
                    "arguments": [
                        {
                            "name": "file_url",
                            "description": "Figma file URL",
                            "required": True
                        }
                    ]
                }
            ]
        }

    async def handle_get_prompt(self, params: Dict) -> Dict:
        """Get a specific prompt"""
        return {
            "description": "Generate React component from Figma design",
            "messages": [
                {
                    "role": "user",
                    "content": "Generate a React component from this Figma design"
                }
            ]
        }

    async def handle_unknown(self, params: Dict) -> Dict:
        """Handle unknown methods"""
        return {"error": "Unknown method"}

    async def run_stdio_server(self):
        """Run as stdio MCP server"""
        logger.info("Figma Desktop MCP Bridge started")

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer = asyncio.StreamWriter(
            asyncio.get_event_loop()._make_write_pipe_transport(sys.stdout.fileno(), protocol),
            protocol,
            reader,
            asyncio.get_event_loop()
        )

        while True:
            try:
                # Read JSON-RPC request
                line = await reader.readline()
                if not line:
                    break

                # Skip empty lines
                line = line.strip()
                if not line:
                    continue

                # Parse request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Handle request
                response = await self.handle_request(request)

                # Send response
                response_with_id = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": response
                }

                writer.write(json.dumps(response_with_id).encode() + b'\n')
                await writer.drain()

            except Exception as e:
                logger.error(f"Error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                writer.write(json.dumps(error_response).encode() + b'\n')
                await writer.drain()

async def main():
    bridge = FigmaDesktopMCPBridge()
    await bridge.run_stdio_server()

if __name__ == "__main__":
    asyncio.run(main())