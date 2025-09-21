#!/usr/bin/env python3
"""
MCP v2 WebSocket Handler
Implements real-time bidirectional communication
Protocol Version: 2025-06-18
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, Set, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
import aiohttp
from aiohttp import web
import sqlite3
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPWebSocketHandler:
    def __init__(self, mcp_server, port: int = 8100):
        self.mcp_server = mcp_server
        self.port = port
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.client_sessions: Dict[str, Dict] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        self.heartbeat_interval = 30
        self.message_buffer: Dict[str, list] = {}

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        client_id = str(uuid.uuid4())
        logger.info(f"WebSocket connection established: {client_id}")

        try:
            # Store client connection
            self.clients[client_id] = websocket
            self.client_sessions[client_id] = {
                "connected_at": datetime.utcnow().isoformat(),
                "subscriptions": set(),
                "capabilities": {},
                "authenticated": False
            }

            # Send welcome message
            await self.send_message(client_id, {
                "type": "connection",
                "client_id": client_id,
                "protocol_version": "2025-06-18",
                "features": {
                    "streaming": True,
                    "subscriptions": True,
                    "heartbeat": True,
                    "reconnect": True
                }
            })

            # Start heartbeat
            heartbeat_task = asyncio.create_task(self.heartbeat(client_id))

            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(client_id, data)
                except json.JSONDecodeError as e:
                    await self.send_error(client_id, f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self.send_error(client_id, str(e))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Cleanup
            heartbeat_task.cancel()
            await self.cleanup_client(client_id)

    async def handle_message(self, client_id: str, data: Dict):
        """Route WebSocket messages"""
        msg_type = data.get("type")
        msg_id = data.get("id", str(uuid.uuid4()))

        handlers = {
            "ping": self.handle_ping,
            "authenticate": self.handle_authenticate,
            "subscribe": self.handle_subscribe,
            "unsubscribe": self.handle_unsubscribe,
            "rpc": self.handle_rpc,
            "stream": self.handle_stream,
            "broadcast": self.handle_broadcast,
            "get_state": self.handle_get_state
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(client_id, data, msg_id)
        else:
            await self.send_error(client_id, f"Unknown message type: {msg_type}", msg_id)

    async def handle_ping(self, client_id: str, data: Dict, msg_id: str):
        """Handle ping/pong for connection health"""
        await self.send_message(client_id, {
            "type": "pong",
            "id": msg_id,
            "timestamp": time.time()
        })

    async def handle_authenticate(self, client_id: str, data: Dict, msg_id: str):
        """Handle OAuth authentication over WebSocket"""
        token = data.get("token")

        if not token:
            await self.send_error(client_id, "Token required", msg_id)
            return

        # Validate token (simplified)
        is_valid = await self.validate_token(token)

        if is_valid:
            self.client_sessions[client_id]["authenticated"] = True
            await self.send_message(client_id, {
                "type": "authenticated",
                "id": msg_id,
                "success": True,
                "expires_in": 3600
            })
        else:
            await self.send_error(client_id, "Invalid token", msg_id)

    async def handle_subscribe(self, client_id: str, data: Dict, msg_id: str):
        """Subscribe to real-time events"""
        topics = data.get("topics", [])

        if not self.client_sessions[client_id]["authenticated"]:
            await self.send_error(client_id, "Authentication required", msg_id)
            return

        subscribed = []
        for topic in topics:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)
            self.client_sessions[client_id]["subscriptions"].add(topic)
            subscribed.append(topic)

        await self.send_message(client_id, {
            "type": "subscribed",
            "id": msg_id,
            "topics": subscribed
        })

    async def handle_unsubscribe(self, client_id: str, data: Dict, msg_id: str):
        """Unsubscribe from topics"""
        topics = data.get("topics", [])

        unsubscribed = []
        for topic in topics:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)
                self.client_sessions[client_id]["subscriptions"].discard(topic)
                unsubscribed.append(topic)

        await self.send_message(client_id, {
            "type": "unsubscribed",
            "id": msg_id,
            "topics": unsubscribed
        })

    async def handle_rpc(self, client_id: str, data: Dict, msg_id: str):
        """Handle JSON-RPC calls over WebSocket"""
        if not self.client_sessions[client_id]["authenticated"]:
            await self.send_error(client_id, "Authentication required", msg_id)
            return

        # Forward to MCP server
        rpc_request = {
            "jsonrpc": "2.0",
            "method": data.get("method"),
            "params": data.get("params", {}),
            "id": msg_id
        }

        try:
            # Call MCP server
            response = await self.mcp_server.handle_jsonrpc(rpc_request)

            # Send response
            await self.send_message(client_id, {
                "type": "rpc_response",
                "id": msg_id,
                "result": response
            })
        except Exception as e:
            await self.send_error(client_id, str(e), msg_id)

    async def handle_stream(self, client_id: str, data: Dict, msg_id: str):
        """Handle streaming responses"""
        if not self.client_sessions[client_id]["authenticated"]:
            await self.send_error(client_id, "Authentication required", msg_id)
            return

        stream_type = data.get("stream_type")
        params = data.get("params", {})

        if stream_type == "logs":
            await self.stream_logs(client_id, params, msg_id)
        elif stream_type == "metrics":
            await self.stream_metrics(client_id, params, msg_id)
        elif stream_type == "events":
            await self.stream_events(client_id, params, msg_id)
        else:
            await self.send_error(client_id, f"Unknown stream type: {stream_type}", msg_id)

    async def handle_broadcast(self, client_id: str, data: Dict, msg_id: str):
        """Broadcast message to subscribed clients"""
        if not self.client_sessions[client_id]["authenticated"]:
            await self.send_error(client_id, "Authentication required", msg_id)
            return

        topic = data.get("topic")
        message = data.get("message")

        if not topic or not message:
            await self.send_error(client_id, "Topic and message required", msg_id)
            return

        # Broadcast to all subscribers
        await self.broadcast(topic, message, exclude_client=client_id)

        await self.send_message(client_id, {
            "type": "broadcast_sent",
            "id": msg_id,
            "topic": topic,
            "recipients": len(self.subscriptions.get(topic, set()))
        })

    async def handle_get_state(self, client_id: str, data: Dict, msg_id: str):
        """Get current system state"""
        state = {
            "connected_clients": len(self.clients),
            "subscriptions": {
                topic: len(subscribers)
                for topic, subscribers in self.subscriptions.items()
            },
            "server_time": datetime.utcnow().isoformat(),
            "protocol_version": "2025-06-18"
        }

        await self.send_message(client_id, {
            "type": "state",
            "id": msg_id,
            "state": state
        })

    async def stream_logs(self, client_id: str, params: Dict, msg_id: str):
        """Stream log entries in real-time"""
        level = params.get("level", "INFO")
        follow = params.get("follow", True)

        # Stream historical logs first
        conn = sqlite3.connect('/tmp/mcp_state.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, level, message, metadata
            FROM audit_log
            WHERE level >= ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (level,))

        for row in cursor.fetchall():
            await self.send_message(client_id, {
                "type": "stream_data",
                "id": msg_id,
                "stream_type": "logs",
                "data": {
                    "timestamp": row[0],
                    "level": row[1],
                    "message": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {}
                }
            })

        conn.close()

        if follow:
            # Subscribe to future logs
            self.subscriptions.setdefault("logs", set()).add(client_id)

    async def stream_metrics(self, client_id: str, params: Dict, msg_id: str):
        """Stream system metrics"""
        interval = params.get("interval", 5)

        while client_id in self.clients:
            metrics = await self.collect_metrics()

            await self.send_message(client_id, {
                "type": "stream_data",
                "id": msg_id,
                "stream_type": "metrics",
                "data": metrics
            })

            await asyncio.sleep(interval)

    async def stream_events(self, client_id: str, params: Dict, msg_id: str):
        """Stream MCP events"""
        event_types = params.get("types", ["all"])

        # Subscribe to events
        for event_type in event_types:
            self.subscriptions.setdefault(f"event:{event_type}", set()).add(client_id)

        await self.send_message(client_id, {
            "type": "stream_started",
            "id": msg_id,
            "stream_type": "events",
            "subscribed_to": event_types
        })

    async def broadcast(self, topic: str, message: Any, exclude_client: Optional[str] = None):
        """Broadcast message to all subscribers of a topic"""
        subscribers = self.subscriptions.get(topic, set())

        for client_id in subscribers:
            if client_id != exclude_client and client_id in self.clients:
                await self.send_message(client_id, {
                    "type": "broadcast",
                    "topic": topic,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })

    async def send_message(self, client_id: str, message: Dict):
        """Send message to specific client"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                await self.cleanup_client(client_id)

    async def send_error(self, client_id: str, error: str, msg_id: Optional[str] = None):
        """Send error message"""
        await self.send_message(client_id, {
            "type": "error",
            "id": msg_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def heartbeat(self, client_id: str):
        """Send periodic heartbeat"""
        while client_id in self.clients:
            await self.send_message(client_id, {
                "type": "heartbeat",
                "timestamp": time.time()
            })
            await asyncio.sleep(self.heartbeat_interval)

    async def cleanup_client(self, client_id: str):
        """Clean up disconnected client"""
        if client_id in self.clients:
            del self.clients[client_id]

        if client_id in self.client_sessions:
            # Remove from all subscriptions
            for topic in self.client_sessions[client_id]["subscriptions"]:
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(client_id)
            del self.client_sessions[client_id]

        if client_id in self.message_buffer:
            del self.message_buffer[client_id]

        logger.info(f"Cleaned up client: {client_id}")

    async def validate_token(self, token: str) -> bool:
        """Validate OAuth token"""
        # Simplified validation - in production, check with auth server
        return len(token) > 10

    async def collect_metrics(self) -> Dict:
        """Collect system metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "connections": len(self.clients),
            "subscriptions": sum(len(s) for s in self.subscriptions.values()),
            "memory_usage": 0,  # Would use psutil in production
            "cpu_usage": 0,
            "message_rate": 0
        }

    async def notify_event(self, event_type: str, event_data: Dict):
        """Notify subscribers of an event"""
        await self.broadcast(f"event:{event_type}", {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def start(self):
        """Start WebSocket server"""
        logger.info(f"Starting WebSocket server on port {self.port}")
        await websockets.serve(
            lambda ws: self.handle_connection(ws, "/"),
            "localhost",
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        logger.info(f"WebSocket server listening on ws://localhost:{self.port}")

# Standalone server for testing
if __name__ == "__main__":
    # Create minimal MCP server mock for testing
    class MockMCPServer:
        async def handle_jsonrpc(self, request):
            return {"result": "ok", "id": request.get("id")}

    mock_server = MockMCPServer()
    ws_handler = MCPWebSocketHandler(mock_server, port=8100)

    async def main():
        await ws_handler.start()
        await asyncio.Future()  # Run forever

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped")