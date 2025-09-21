#!/usr/bin/env python3
"""
MCP Bridge v2 Singleton - Prevents duplicate sessions and zombie threads
Maintains a single persistent connection to MCP server
"""

import os
import sys
import json
import time
import asyncio
import threading
import logging
import atexit
from pathlib import Path
from typing import Optional, Dict, Any
import uuid
import requests
from datetime import datetime
import fcntl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global singleton instance
_bridge_instance = None
_instance_lock = threading.Lock()

# Lockfile to prevent multiple processes
LOCKFILE_PATH = "/tmp/mcp_bridge_singleton.lock"


class MCPBridgeSingleton:
    """Singleton MCP Bridge that maintains persistent connection"""

    def __new__(cls):
        global _bridge_instance
        with _instance_lock:
            if _bridge_instance is None:
                _bridge_instance = super().__new__(cls)
                _bridge_instance._initialized = False
            return _bridge_instance

    def __init__(self):
        # Only initialize once
        if self._initialized:
            return

        logger.info("🔧 Initializing MCP Bridge Singleton")

        # Try to acquire lock file
        self.lockfile = None
        if not self._acquire_lock():
            logger.warning("Another MCP bridge instance is already running")
            # Connect to existing instance instead of creating new
            self._connect_to_existing()
            return

        self._initialized = True
        self.mcp_server = "http://localhost:8099"
        self.ws_url = "ws://localhost:8089/ws"
        self.session_id = None
        self.ws_thread = None
        self.ws_connection = None
        self.running = False
        self.event_queue = []
        self.response_cache = {}

        # Register cleanup
        atexit.register(self.cleanup)

        # Initialize connection
        self._initialize_connection()

    def _acquire_lock(self) -> bool:
        """Acquire process lock to prevent duplicates"""
        try:
            self.lockfile = open(LOCKFILE_PATH, 'w')
            fcntl.lockf(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lockfile.write(str(os.getpid()))
            self.lockfile.flush()
            return True
        except IOError:
            if self.lockfile:
                self.lockfile.close()
            return False

    def _release_lock(self):
        """Release process lock"""
        if self.lockfile:
            try:
                fcntl.lockf(self.lockfile.fileno(), fcntl.LOCK_UN)
                self.lockfile.close()
                os.unlink(LOCKFILE_PATH)
            except:
                pass

    def _connect_to_existing(self):
        """Connect to existing MCP bridge instance via IPC"""
        # Try to read PID from lockfile
        try:
            with open(LOCKFILE_PATH, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is still running
            os.kill(pid, 0)

            logger.info(f"Connected to existing MCP bridge (PID: {pid})")
            self._initialized = True
            self.is_proxy = True

            # Use shared memory or socket for IPC
            self.ipc_socket = f"/tmp/mcp_bridge_{pid}.sock"

        except (FileNotFoundError, ProcessLookupError, ValueError):
            logger.error("Failed to connect to existing bridge")
            # Cleanup stale lockfile
            try:
                os.unlink(LOCKFILE_PATH)
            except:
                pass
            # Retry initialization
            self.__init__()

    def _initialize_connection(self):
        """Initialize MCP server connection"""
        if hasattr(self, 'is_proxy') and self.is_proxy:
            return  # Proxy doesn't need direct connection

        try:
            # Initialize MCP session
            response = requests.post(
                f"{self.mcp_server}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "experimental": {},
                            "sampling": {}
                        },
                        "clientInfo": {
                            "name": "mcp-bridge-singleton",
                            "version": "2.0.0"
                        }
                    },
                    "id": str(uuid.uuid4())
                },
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    self.session_id = result['result'].get('sessionId', str(uuid.uuid4()))
                    logger.info(f"✅ MCP session initialized: {self.session_id}")
                    self.running = True

                    # Start background thread for WebSocket
                    self._start_websocket()

                    # Start event processor
                    self._start_event_processor()
                else:
                    logger.error(f"Failed to initialize MCP session: {result}")
            else:
                logger.error(f"MCP server returned {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to initialize MCP connection: {e}")

    def _start_websocket(self):
        """Start WebSocket connection in background thread"""
        if self.ws_thread and self.ws_thread.is_alive():
            return  # Already running

        self.ws_thread = threading.Thread(target=self._websocket_loop, daemon=True)
        self.ws_thread.start()
        logger.info("🔌 WebSocket thread started")

    def _websocket_loop(self):
        """WebSocket connection loop"""
        import asyncio
        import websockets

        async def connect():
            while self.running:
                try:
                    async with websockets.connect(self.ws_url) as websocket:
                        self.ws_connection = websocket
                        logger.info("📡 WebSocket connected")

                        # Send initial subscription
                        await websocket.send(json.dumps({
                            "action": "subscribe",
                            "session_id": self.session_id
                        }))

                        # Listen for messages
                        while self.running:
                            try:
                                message = await asyncio.wait_for(
                                    websocket.recv(),
                                    timeout=30
                                )
                                data = json.loads(message)
                                self._handle_websocket_message(data)
                            except asyncio.TimeoutError:
                                # Send ping to keep alive
                                await websocket.ping()
                            except Exception as e:
                                logger.error(f"WebSocket receive error: {e}")
                                break

                except Exception as e:
                    logger.error(f"WebSocket connection error: {e}")
                    self.ws_connection = None
                    await asyncio.sleep(5)  # Retry after 5 seconds

        # Run async loop
        asyncio.new_event_loop().run_until_complete(connect())

    def _handle_websocket_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        msg_type = data.get('type')

        if msg_type == 'agent_update':
            agent = data.get('agent')
            status = data.get('status')
            logger.info(f"📨 Agent update: {agent} -> {status}")

        elif msg_type == 'task_complete':
            task_id = data.get('task_id')
            result = data.get('result')
            logger.info(f"✅ Task {task_id} completed")
            self.response_cache[task_id] = result

    def _start_event_processor(self):
        """Start background thread to process queued events"""
        threading.Thread(target=self._process_events, daemon=True).start()

    def _process_events(self):
        """Process queued events"""
        while self.running:
            if self.event_queue:
                event = self.event_queue.pop(0)
                try:
                    self._process_single_event(event)
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
            time.sleep(0.1)

    def _process_single_event(self, event: Dict[str, Any]):
        """Process a single event"""
        event_type = event.get('type')

        if event_type == 'tool_call':
            tool = event['tool']
            params = event['params']
            result = self.call_tool(tool, params)

            # Store result if callback provided
            if 'callback_id' in event:
                self.response_cache[event['callback_id']] = result

    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool without creating new session"""
        if hasattr(self, 'is_proxy') and self.is_proxy:
            # Forward to main instance via IPC
            return self._forward_to_main(tool_name, params)

        try:
            response = requests.post(
                f"{self.mcp_server}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": params
                    },
                    "id": str(uuid.uuid4()),
                    "sessionId": self.session_id  # Use existing session
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return {"error": str(e)}

    def _forward_to_main(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forward tool call to main instance via IPC"""
        # Implementation would use socket/shared memory
        # For now, make direct HTTP call
        return self.call_tool(tool_name, params)

    def queue_event(self, event: Dict[str, Any]):
        """Queue an event for processing"""
        self.event_queue.append(event)

    def get_status(self) -> Dict[str, Any]:
        """Get bridge status"""
        return {
            "running": self.running,
            "session_id": self.session_id,
            "ws_connected": self.ws_connection is not None,
            "queued_events": len(self.event_queue),
            "is_proxy": hasattr(self, 'is_proxy') and self.is_proxy
        }

    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up MCP Bridge")
        self.running = False

        # Close WebSocket
        if self.ws_connection:
            try:
                asyncio.run(self.ws_connection.close())
            except:
                pass

        # Release lock
        self._release_lock()

        # Clear singleton
        global _bridge_instance
        _bridge_instance = None


def get_bridge() -> MCPBridgeSingleton:
    """Get or create singleton bridge instance"""
    return MCPBridgeSingleton()


def main():
    """Main entry point for testing"""
    bridge = get_bridge()

    logger.info(f"Bridge status: {bridge.get_status()}")

    # Test tool call
    result = bridge.call_tool("heartbeat", {"agent": "test"})
    logger.info(f"Heartbeat result: {result}")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        bridge.cleanup()


if __name__ == "__main__":
    main()