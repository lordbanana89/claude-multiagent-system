#!/usr/bin/env python3
"""
WebSocket server for MCP v2
Handles real-time communication between agents
"""

import asyncio
import json
import logging
from aiohttp import web, WSMsgType
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MCPWebSocketServer:
    def __init__(self, port=8100):
        self.port = port
        self.app = web.Application()
        self.clients = {}
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get('/', self.websocket_handler)

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        client_id = request.headers.get('X-Client-ID', 'unknown')
        self.clients[client_id] = ws

        logger.info(f"WebSocket client connected: {client_id}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    # Handle handshake
                    if data.get('type') == 'handshake':
                        response = {
                            'type': 'handshake_ack',
                            'status': 'connected',
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                        await ws.send_json(response)

                    # Broadcast to other clients
                    else:
                        await self.broadcast(data, exclude=client_id)

                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")

        return ws

    async def broadcast(self, data, exclude=None):
        """Broadcast message to all connected clients"""
        for client_id, ws in self.clients.items():
            if client_id != exclude:
                try:
                    await ws.send_json(data)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")

    async def start(self):
        """Start WebSocket server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()

        logger.info(f"MCP WebSocket Server started on ws://localhost:{self.port}")

        # Keep running
        await asyncio.Future()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = MCPWebSocketServer()
    asyncio.run(server.start())