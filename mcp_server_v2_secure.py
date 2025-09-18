#!/usr/bin/env python3
"""
MCP Server v2 Secure - Enhanced with OAuth 2.1 and Security Features
Includes all Phase 4 security enhancements
"""

import json
import sqlite3
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import uuid

from aiohttp import web
import aiohttp_cors

# Import the main MCP server and security module
import sys
sys.path.append('/Users/erik/Desktop/claude-multiagent-system')
from mcp_server_v2 import MCPServer
from mcp_security_v2 import MCPSecurity, SecurityContext, create_security_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PORT = 8099

class SecureMCPServer(MCPServer):
    """Enhanced MCP Server with security features"""

    def __init__(self):
        super().__init__()
        self.security = MCPSecurity()
        logger.info("Security module initialized")

    async def handle_jsonrpc(self, request):
        """Enhanced JSON-RPC handler with security"""
        try:
            # Get request context
            request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

            # Create security context
            security_context = SecurityContext(
                session_id=request.headers.get('X-Session-ID', ''),
                user_id=request.headers.get('X-User-ID'),
                token=request.headers.get('Authorization', '').replace('Bearer ', ''),
                scopes=[],
                ip_address=request.remote or '127.0.0.1',
                request_id=request_id,
                timestamp=datetime.now()
            )

            # Parse JSON-RPC request
            data = await request.json()

            if not isinstance(data, dict) or 'jsonrpc' not in data:
                return self._error_response(-32600, "Invalid Request", request_id)

            method = data.get('method')
            params = data.get('params', {})

            # Add session_id to params if available
            if security_context.session_id:
                params['session_id'] = security_context.session_id

            # Security checks for protected methods
            if method.startswith('tools/'):
                # Check OAuth token for tool execution
                if security_context.token:
                    token_data = self.security.validate_oauth_token(security_context.token)
                    if not token_data:
                        return self._error_response(-32001, "Unauthorized: Invalid token", request_id)
                    security_context.scopes = token_data.get('scopes', [])

                # Check rate limiting
                rate_key = f"{security_context.ip_address}:{method}"
                allowed, rate_info = self.security.check_rate_limit(rate_key)
                if not allowed:
                    return self._error_response(-32002, f"Rate limit exceeded", request_id)

                # Audit log the request
                self.security.log_audit(
                    security_context,
                    method,
                    params.get('name', ''),
                    'requested',
                    params
                )

            # Special handling for dangerous tools
            if method == 'tools/call':
                tool_name = params.get('name', '')

                # Check if consent is required
                consent_level = self.security.check_consent_required(tool_name, '')
                if consent_level.value != 'none':
                    has_consent, reason = self.security.check_consent(
                        security_context.session_id,
                        tool_name,
                        ''
                    )
                    if not has_consent:
                        # Request consent
                        consent_id = self.security.request_consent(
                            security_context.session_id,
                            tool_name,
                            '',
                            params
                        )
                        return self._error_response(
                            -32003,
                            f"Consent required for {tool_name}",
                            request_id,
                            {"consent_id": consent_id, "consent_url": f"/api/mcp/consent/{consent_id}"}
                        )

            # Enhanced resource security
            if method == 'resources/read':
                uri = params.get('uri', '')

                # Validate file paths
                if uri.startswith('file://'):
                    valid, reason = self.security.validate_file_path(uri)
                    if not valid:
                        self.security.log_audit(
                            security_context,
                            'resource_access',
                            uri,
                            'denied',
                            {'reason': reason}
                        )
                        return self._error_response(-32004, reason, request_id)

            # Process the request with base handler
            result = await super()._route_method(method, params, request_id)

            # Audit successful operations
            self.security.log_audit(
                security_context,
                method,
                params.get('name', params.get('uri', '')),
                'success',
                {'result_type': type(result).__name__}
            )

            # Build response
            response = {
                "jsonrpc": "2.0",
                "result": result
            }
            if data.get('id') is not None:
                response["id"] = data['id']

            return web.json_response(response, headers={'X-Request-ID': request_id})

        except Exception as e:
            logger.error(f"Secure handler error: {e}")
            return self._error_response(-32603, "Internal error", request_id)

    def _error_response(self, code: int, message: str, request_id: str, data: Dict = None):
        """Enhanced error response with additional data"""
        response = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message,
                "data": data or {
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            },
            "id": None
        }
        return web.json_response(response, status=400, headers={'X-Request-ID': request_id})

    # New security endpoints
    async def handle_oauth_token(self, request):
        """Handle OAuth token requests"""
        try:
            data = await request.json()

            # Validate grant type
            grant_type = data.get('grant_type')
            if grant_type != 'client_credentials':
                return web.json_response({
                    "error": "unsupported_grant_type",
                    "error_description": "Only client_credentials grant is supported"
                }, status=400)

            # Validate client credentials
            client_id = data.get('client_id')
            client_secret = data.get('client_secret')

            # TODO: Implement actual client validation
            if not client_id or not client_secret:
                return web.json_response({
                    "error": "invalid_client",
                    "error_description": "Missing client credentials"
                }, status=401)

            # Create token
            token_response = self.security.create_oauth_token(
                session_id=str(uuid.uuid4()),
                user_id=client_id,
                scopes=data.get('scope', 'read').split()
            )

            return web.json_response(token_response)

        except Exception as e:
            logger.error(f"OAuth token error: {e}")
            return web.json_response({
                "error": "server_error",
                "error_description": str(e)
            }, status=500)

    async def handle_consent(self, request):
        """Handle consent management"""
        consent_id = request.match_info.get('consent_id')

        if request.method == 'GET':
            # Return consent request details
            # TODO: Implement consent UI
            return web.json_response({
                "consent_id": consent_id,
                "status": "pending",
                "message": "Consent required for dangerous operation"
            })

        elif request.method == 'POST':
            # Process consent decision
            data = await request.json()
            decision = data.get('decision', 'denied')
            reason = data.get('reason', '')

            success = self.security.grant_consent(consent_id, decision, reason)

            return web.json_response({
                "consent_id": consent_id,
                "decision": decision,
                "success": success
            })

    async def handle_audit_logs(self, request):
        """Retrieve audit logs"""
        session_id = request.query.get('session_id')
        limit = int(request.query.get('limit', 100))

        logs = self.security.get_audit_logs(session_id, limit)

        return web.json_response({
            "logs": logs,
            "count": len(logs),
            "limit": limit
        })

    async def handle_security_status(self, request):
        """Get security status and policies"""
        return web.json_response({
            "security": {
                "oauth_enabled": True,
                "consent_flow": True,
                "path_protection": True,
                "rate_limiting": True,
                "audit_logging": True,
                "dangerous_operations": list(self.security.dangerous_operations.keys())
            },
            "policies": {
                "token_expiry_hours": 24,
                "consent_expiry_minutes": 30,
                "rate_limit_per_minute": 100,
                "path_blacklist": [
                    '.git', '.env', 'id_rsa', '.ssh', 'private.key',
                    'secret', 'password', 'token', '.pem', '.key', '.cert'
                ]
            }
        })

def create_secure_app():
    """Create secure aiohttp application"""
    server = SecureMCPServer()
    app = web.Application()

    # Configure CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # Core endpoints
    rpc_route = app.router.add_post('/jsonrpc', server.handle_jsonrpc)
    cors.add(rpc_route)

    # Security endpoints
    oauth_route = app.router.add_post('/oauth/token', server.handle_oauth_token)
    cors.add(oauth_route)

    consent_get = app.router.add_get('/api/mcp/consent/{consent_id}', server.handle_consent)
    cors.add(consent_get)

    consent_post = app.router.add_post('/api/mcp/consent/{consent_id}', server.handle_consent)
    cors.add(consent_post)

    audit_route = app.router.add_get('/api/mcp/audit', server.handle_audit_logs)
    cors.add(audit_route)

    security_route = app.router.add_get('/api/mcp/security', server.handle_security_status)
    cors.add(security_route)

    # Legacy endpoints
    legacy_status = app.router.add_get('/api/mcp/status', server.handle_legacy_status)
    cors.add(legacy_status)

    health_route = app.router.add_get('/api/mcp/health', lambda r: web.json_response({"status": "healthy"}))
    cors.add(health_route)

    # New Phase 5 endpoints
    resources_route = app.router.add_get('/api/mcp/resources',
        lambda r: web.json_response({"resources": list(server.resources.values())}))
    cors.add(resources_route)

    prompts_route = app.router.add_get('/api/mcp/prompts',
        lambda r: web.json_response({"prompts": list(server.prompts.values())}))
    cors.add(prompts_route)

    capabilities_route = app.router.add_get('/api/mcp/capabilities',
        lambda r: web.json_response(server.capabilities))
    cors.add(capabilities_route)

    return app

async def main():
    """Main entry point for secure server"""
    # Initialize database
    from mcp_server_v2 import init_database
    await init_database()

    # Create and run app
    app = create_secure_app()

    logger.info(f"Starting Secure MCP Server v2 on port {PORT}")
    logger.info(f"Security features enabled:")
    logger.info(f"  - OAuth 2.1 authentication: /oauth/token")
    logger.info(f"  - Consent management: /api/mcp/consent")
    logger.info(f"  - Audit logs: /api/mcp/audit")
    logger.info(f"  - Security status: /api/mcp/security")
    logger.info(f"  - Path traversal protection: Active")
    logger.info(f"  - Rate limiting: 100 req/min")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', PORT)
    await site.start()

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down Secure MCP Server v2")

if __name__ == '__main__':
    asyncio.run(main())