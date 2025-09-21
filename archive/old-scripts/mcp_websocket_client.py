#!/usr/bin/env python3
"""
MCP WebSocket Client Example
Demonstrates real-time communication with MCP v2 WebSocket server
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPWebSocketClient:
    def __init__(self, url: str = "ws://localhost:8100"):
        self.url = url
        self.websocket = None
        self.client_id = None
        self.running = False

    async def connect(self):
        """Connect to WebSocket server"""
        logger.info(f"Connecting to {self.url}")
        self.websocket = await websockets.connect(self.url)
        self.running = True

        # Start message handler
        asyncio.create_task(self.receive_messages())

    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()

    async def receive_messages(self):
        """Handle incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
            self.running = False

    async def handle_message(self, data: dict):
        """Process received message"""
        msg_type = data.get("type")

        if msg_type == "connection":
            self.client_id = data.get("client_id")
            logger.info(f"Connected with client ID: {self.client_id}")
            logger.info(f"Protocol version: {data.get('protocol_version')}")
            logger.info(f"Features: {data.get('features')}")

        elif msg_type == "heartbeat":
            logger.debug(f"Heartbeat received: {data.get('timestamp')}")

        elif msg_type == "pong":
            logger.info(f"Pong received: {data.get('timestamp')}")

        elif msg_type == "authenticated":
            logger.info(f"Authentication successful, expires in {data.get('expires_in')}s")

        elif msg_type == "subscribed":
            logger.info(f"Subscribed to topics: {data.get('topics')}")

        elif msg_type == "broadcast":
            logger.info(f"Broadcast on '{data.get('topic')}': {data.get('message')}")

        elif msg_type == "stream_data":
            stream_type = data.get("stream_type")
            stream_data = data.get("data")
            logger.info(f"Stream [{stream_type}]: {stream_data}")

        elif msg_type == "rpc_response":
            logger.info(f"RPC Response: {data.get('result')}")

        elif msg_type == "error":
            logger.error(f"Error: {data.get('error')}")

        else:
            logger.info(f"Received: {data}")

    async def send_message(self, message: dict):
        """Send message to server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))

    async def ping(self):
        """Send ping message"""
        await self.send_message({
            "type": "ping",
            "id": datetime.utcnow().isoformat()
        })

    async def authenticate(self, token: str):
        """Authenticate with server"""
        await self.send_message({
            "type": "authenticate",
            "token": token
        })

    async def subscribe(self, topics: list):
        """Subscribe to topics"""
        await self.send_message({
            "type": "subscribe",
            "topics": topics
        })

    async def unsubscribe(self, topics: list):
        """Unsubscribe from topics"""
        await self.send_message({
            "type": "unsubscribe",
            "topics": topics
        })

    async def call_rpc(self, method: str, params: dict = None):
        """Call JSON-RPC method"""
        await self.send_message({
            "type": "rpc",
            "method": method,
            "params": params or {},
            "id": datetime.utcnow().isoformat()
        })

    async def stream_logs(self, level: str = "INFO", follow: bool = True):
        """Stream log entries"""
        await self.send_message({
            "type": "stream",
            "stream_type": "logs",
            "params": {
                "level": level,
                "follow": follow
            }
        })

    async def stream_metrics(self, interval: int = 5):
        """Stream system metrics"""
        await self.send_message({
            "type": "stream",
            "stream_type": "metrics",
            "params": {
                "interval": interval
            }
        })

    async def stream_events(self, event_types: list = None):
        """Stream MCP events"""
        await self.send_message({
            "type": "stream",
            "stream_type": "events",
            "params": {
                "types": event_types or ["all"]
            }
        })

    async def broadcast(self, topic: str, message: any):
        """Broadcast message to topic"""
        await self.send_message({
            "type": "broadcast",
            "topic": topic,
            "message": message
        })

    async def get_state(self):
        """Get server state"""
        await self.send_message({
            "type": "get_state"
        })

async def interactive_client():
    """Interactive WebSocket client for testing"""
    client = MCPWebSocketClient()

    try:
        await client.connect()
        logger.info("Connected! Available commands:")
        logger.info("  1. ping - Send ping")
        logger.info("  2. auth <token> - Authenticate")
        logger.info("  3. subscribe <topic1,topic2> - Subscribe to topics")
        logger.info("  4. unsubscribe <topic1,topic2> - Unsubscribe")
        logger.info("  5. rpc <method> <params> - Call RPC method")
        logger.info("  6. logs - Stream logs")
        logger.info("  7. metrics - Stream metrics")
        logger.info("  8. events - Stream events")
        logger.info("  9. broadcast <topic> <message> - Broadcast message")
        logger.info("  10. state - Get server state")
        logger.info("  11. quit - Exit")

        # Authenticate automatically for testing
        await client.authenticate("test-token-12345")
        await asyncio.sleep(1)

        while client.running:
            try:
                # Read command
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, "\nEnter command: "
                )

                parts = command.strip().split(maxsplit=2)
                if not parts:
                    continue

                cmd = parts[0].lower()

                if cmd == "quit":
                    break

                elif cmd == "ping" or cmd == "1":
                    await client.ping()

                elif cmd == "auth" or cmd == "2":
                    token = parts[1] if len(parts) > 1 else "test-token"
                    await client.authenticate(token)

                elif cmd == "subscribe" or cmd == "3":
                    topics = parts[1].split(",") if len(parts) > 1 else ["test"]
                    await client.subscribe(topics)

                elif cmd == "unsubscribe" or cmd == "4":
                    topics = parts[1].split(",") if len(parts) > 1 else ["test"]
                    await client.unsubscribe(topics)

                elif cmd == "rpc" or cmd == "5":
                    method = parts[1] if len(parts) > 1 else "tools/list"
                    params = json.loads(parts[2]) if len(parts) > 2 else {}
                    await client.call_rpc(method, params)

                elif cmd == "logs" or cmd == "6":
                    await client.stream_logs()

                elif cmd == "metrics" or cmd == "7":
                    await client.stream_metrics()

                elif cmd == "events" or cmd == "8":
                    await client.stream_events()

                elif cmd == "broadcast" or cmd == "9":
                    topic = parts[1] if len(parts) > 1 else "test"
                    message = parts[2] if len(parts) > 2 else "Hello WebSocket!"
                    await client.broadcast(topic, message)

                elif cmd == "state" or cmd == "10":
                    await client.get_state()

                else:
                    logger.info(f"Unknown command: {cmd}")

                # Give time for response
                await asyncio.sleep(0.5)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")

    finally:
        await client.disconnect()
        logger.info("Disconnected")

async def automated_test():
    """Automated test sequence"""
    client = MCPWebSocketClient()

    try:
        # Connect
        await client.connect()
        await asyncio.sleep(1)

        # Authenticate
        logger.info("\n=== Testing Authentication ===")
        await client.authenticate("test-token-12345")
        await asyncio.sleep(1)

        # Test ping/pong
        logger.info("\n=== Testing Ping/Pong ===")
        await client.ping()
        await asyncio.sleep(1)

        # Subscribe to topics
        logger.info("\n=== Testing Subscriptions ===")
        await client.subscribe(["agents", "logs", "metrics"])
        await asyncio.sleep(1)

        # Test RPC calls
        logger.info("\n=== Testing RPC Calls ===")
        await client.call_rpc("tools/list")
        await asyncio.sleep(1)

        await client.call_rpc("resources/list")
        await asyncio.sleep(1)

        # Test broadcasting
        logger.info("\n=== Testing Broadcasting ===")
        await client.broadcast("agents", {
            "event": "test",
            "message": "Hello from WebSocket client!"
        })
        await asyncio.sleep(1)

        # Get server state
        logger.info("\n=== Testing Server State ===")
        await client.get_state()
        await asyncio.sleep(1)

        # Stream events
        logger.info("\n=== Testing Event Streaming ===")
        await client.stream_events(["tool_call", "resource_access"])
        await asyncio.sleep(2)

        # Unsubscribe
        logger.info("\n=== Testing Unsubscribe ===")
        await client.unsubscribe(["agents"])
        await asyncio.sleep(1)

        logger.info("\n=== All tests completed ===")

    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "interactive"

    if mode == "test":
        asyncio.run(automated_test())
    else:
        asyncio.run(interactive_client())