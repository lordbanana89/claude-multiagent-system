#!/usr/bin/env python3
"""
MCP v2 Server with WebSocket Support
Combines HTTP/JSON-RPC with WebSocket real-time transport
"""

import asyncio
import json
import logging
from aiohttp import web
from mcp_server_v2_secure import MCPServer, MCPSecurity
from mcp_websocket_handler import MCPWebSocketHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerWithWebSocket:
    def __init__(self):
        self.mcp_server = MCPServer()
        self.security = MCPSecurity()
        self.ws_handler = MCPWebSocketHandler(self.mcp_server, port=8100)

    async def start_servers(self):
        """Start both HTTP and WebSocket servers"""
        # Start WebSocket server
        ws_task = asyncio.create_task(self.ws_handler.start())

        # Start HTTP server
        app = web.Application()

        # Add routes
        app.router.add_post('/jsonrpc', self.handle_jsonrpc)
        app.router.add_get('/api/mcp/status', self.handle_status)
        app.router.add_get('/api/mcp/health', self.handle_health)
        app.router.add_get('/api/mcp/resources', self.handle_resources)
        app.router.add_get('/api/mcp/prompts', self.handle_prompts)
        app.router.add_get('/api/mcp/capabilities', self.handle_capabilities)
        app.router.add_get('/api/mcp/security', self.handle_security)
        app.router.add_get('/api/mcp/audit', self.handle_audit)
        app.router.add_post('/oauth/token', self.handle_oauth_token)
        app.router.add_get('/api/mcp/consent/{id}', self.handle_consent_get)
        app.router.add_post('/api/mcp/consent/{id}', self.handle_consent_post)

        # Add CORS middleware
        app.middlewares.append(self.cors_middleware)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8099)
        await site.start()

        logger.info("MCP Server v2 with WebSocket running:")
        logger.info("- HTTP/JSON-RPC: http://localhost:8099")
        logger.info("- WebSocket: ws://localhost:8100")

        # Keep running
        await asyncio.Future()

    @web.middleware
    async def cors_middleware(self, request, handler):
        """CORS middleware"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    async def handle_jsonrpc(self, request):
        """Handle JSON-RPC requests"""
        try:
            data = await request.json()

            # Check authentication
            auth_header = request.headers.get('Authorization')
            if auth_header:
                token = auth_header.replace('Bearer ', '')
                if not self.security.validate_token(token):
                    return web.json_response({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32001,
                            "message": "Unauthorized"
                        },
                        "id": data.get("id")
                    }, status=401)

            # Process request
            result = await self.mcp_server.handle_jsonrpc(data)

            # Notify WebSocket clients of relevant events
            if data.get("method") == "tools/call":
                await self.ws_handler.notify_event("tool_call", {
                    "tool": data.get("params", {}).get("name"),
                    "result": result
                })
            elif data.get("method") == "resources/read":
                await self.ws_handler.notify_event("resource_access", {
                    "uri": data.get("params", {}).get("uri")
                })

            return web.json_response(result)

        except Exception as e:
            logger.error(f"Error handling JSON-RPC: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": None
            }, status=500)

    async def handle_status(self, request):
        """Get system status"""
        status = {
            "status": "operational",
            "version": "2.0",
            "protocol": "2025-06-18",
            "transports": ["http", "websocket"],
            "websocket_clients": len(self.ws_handler.clients),
            "capabilities": self.mcp_server.capabilities
        }
        return web.json_response(status)

    async def handle_health(self, request):
        """Health check"""
        return web.json_response({"status": "healthy"})

    async def handle_resources(self, request):
        """List resources"""
        resources = await self.mcp_server._list_resources()
        return web.json_response({"resources": resources})

    async def handle_prompts(self, request):
        """List prompts"""
        prompts = await self.mcp_server._list_prompts()
        return web.json_response({"prompts": prompts})

    async def handle_capabilities(self, request):
        """Get capabilities"""
        return web.json_response(self.mcp_server.capabilities)

    async def handle_security(self, request):
        """Get security status"""
        status = self.security.get_security_status()
        return web.json_response(status)

    async def handle_audit(self, request):
        """Get audit logs"""
        limit = int(request.query.get('limit', 100))
        logs = self.security.get_audit_logs(limit)
        return web.json_response({"logs": logs})

    async def handle_oauth_token(self, request):
        """OAuth token endpoint"""
        try:
            data = await request.post()
            grant_type = data.get('grant_type')

            if grant_type == 'client_credentials':
                client_id = data.get('client_id')
                client_secret = data.get('client_secret')

                token = self.security.generate_token({
                    'client_id': client_id,
                    'grant_type': grant_type
                })

                return web.json_response({
                    'access_token': token,
                    'token_type': 'Bearer',
                    'expires_in': 86400
                })
            else:
                return web.json_response({
                    'error': 'unsupported_grant_type'
                }, status=400)

        except Exception as e:
            return web.json_response({
                'error': 'server_error',
                'error_description': str(e)
            }, status=500)

    async def handle_consent_get(self, request):
        """Get consent request"""
        consent_id = request.match_info['id']
        consent = self.security.get_consent_request(consent_id)

        if consent:
            return web.json_response(consent)
        else:
            return web.json_response({
                'error': 'Consent request not found'
            }, status=404)

    async def handle_consent_post(self, request):
        """Handle consent response"""
        consent_id = request.match_info['id']
        data = await request.json()
        approved = data.get('approved', False)

        result = self.security.handle_consent_response(consent_id, approved)

        if result:
            return web.json_response({'success': True})
        else:
            return web.json_response({
                'error': 'Invalid consent request'
            }, status=400)

if __name__ == "__main__":
    server = MCPServerWithWebSocket()
    asyncio.run(server.start_servers())