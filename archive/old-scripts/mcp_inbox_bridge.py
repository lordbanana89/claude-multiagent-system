#!/usr/bin/env python3
"""
Bridge between MCP v2 Server and Inbox System
Enables bidirectional communication between MCP tasks and Inbox messages
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
from aiohttp import web
import aiohttp_cors

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPInboxBridge:
    """Bridge between MCP v2 and Inbox System"""

    def __init__(self, mcp_server_url="http://localhost:8099", inbox_api_port=8098):
        """
        Initialize the bridge

        Args:
            mcp_server_url: URL of the MCP v2 server
            inbox_api_port: Port for the Inbox API server
        """
        self.mcp_server_url = mcp_server_url
        self.inbox_api_port = inbox_api_port
        self.app = web.Application()
        self.messages = []  # In-memory store for messages
        self.task_to_message = {}  # Maps MCP task IDs to inbox message IDs
        self.message_to_task = {}  # Maps inbox message IDs to MCP task IDs
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes for Inbox integration"""
        # CORS setup
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })

        # API Routes
        resource = self.app.router.add_resource("/api/inbox/messages")
        cors.add(resource.add_route("GET", self.get_messages))
        cors.add(resource.add_route("POST", self.add_message))

        resource = self.app.router.add_resource("/api/inbox/messages/{message_id}")
        cors.add(resource.add_route("GET", self.get_message))
        cors.add(resource.add_route("PUT", self.update_message))
        cors.add(resource.add_route("DELETE", self.delete_message))

        resource = self.app.router.add_resource("/api/inbox/messages/{message_id}/read")
        cors.add(resource.add_route("POST", self.mark_as_read))

        resource = self.app.router.add_resource("/api/inbox/messages/{message_id}/unread")
        cors.add(resource.add_route("POST", self.mark_as_unread))

        resource = self.app.router.add_resource("/api/inbox/messages/{message_id}/archive")
        cors.add(resource.add_route("POST", self.archive_message))

        # MCP Bridge endpoints
        resource = self.app.router.add_resource("/api/mcp/task-to-inbox")
        cors.add(resource.add_route("POST", self.mcp_task_to_inbox))

        resource = self.app.router.add_resource("/api/mcp/inbox-to-task")
        cors.add(resource.add_route("POST", self.inbox_to_mcp_task))

        # WebSocket for real-time updates
        self.app.router.add_route("GET", "/ws", self.websocket_handler)

        logger.info("✅ Inbox API routes configured")

    async def get_messages(self, request):
        """Get all messages with optional filtering"""
        filter_type = request.query.get('filter', 'all')
        search_query = request.query.get('search', '')

        filtered_messages = self.messages.copy()

        # Apply filter
        if filter_type == 'unread':
            filtered_messages = [m for m in filtered_messages if m['status'] == 'unread']
        elif filter_type == 'high-priority':
            filtered_messages = [m for m in filtered_messages if m['priority'] in ['high', 'urgent']]
        elif filter_type == 'archived':
            filtered_messages = [m for m in filtered_messages if m['status'] == 'archived']

        # Apply search
        if search_query:
            filtered_messages = [
                m for m in filtered_messages
                if search_query.lower() in m.get('subject', '').lower()
                or search_query.lower() in m.get('content', '').lower()
                or search_query.lower() in m.get('from', '').lower()
            ]

        return web.json_response({
            'messages': filtered_messages,
            'total': len(filtered_messages),
            'unread': len([m for m in self.messages if m['status'] == 'unread'])
        })

    async def get_message(self, request):
        """Get a specific message by ID"""
        message_id = request.match_info['message_id']
        message = next((m for m in self.messages if m['id'] == message_id), None)

        if message:
            return web.json_response(message)
        else:
            return web.json_response({'error': 'Message not found'}, status=404)

    async def add_message(self, request):
        """Add a new message to the inbox"""
        try:
            data = await request.json()

            # Create message with defaults
            message = {
                'id': data.get('id', str(uuid.uuid4())),
                'from': data.get('from', 'System'),
                'to': data.get('to', 'User'),
                'subject': data.get('subject', 'No Subject'),
                'content': data.get('content', ''),
                'priority': data.get('priority', 'normal'),
                'status': data.get('status', 'unread'),
                'timestamp': data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'type': data.get('type', 'notification'),
                'metadata': data.get('metadata', {}),
                'attachments': data.get('attachments', [])
            }

            self.messages.append(message)
            logger.info(f"📥 Added message {message['id']} to inbox")

            # Check if this is from MCP
            if 'mcp_task_id' in message['metadata']:
                task_id = message['metadata']['mcp_task_id']
                self.task_to_message[task_id] = message['id']
                self.message_to_task[message['id']] = task_id

            return web.json_response({'success': True, 'message': message})

        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return web.json_response({'error': str(e)}, status=400)

    async def update_message(self, request):
        """Update an existing message"""
        message_id = request.match_info['message_id']
        data = await request.json()

        for i, message in enumerate(self.messages):
            if message['id'] == message_id:
                self.messages[i].update(data)
                return web.json_response({'success': True, 'message': self.messages[i]})

        return web.json_response({'error': 'Message not found'}, status=404)

    async def delete_message(self, request):
        """Delete a message"""
        message_id = request.match_info['message_id']
        self.messages = [m for m in self.messages if m['id'] != message_id]

        # Clean up mappings
        if message_id in self.message_to_task:
            task_id = self.message_to_task[message_id]
            del self.message_to_task[message_id]
            if task_id in self.task_to_message:
                del self.task_to_message[task_id]

        return web.json_response({'success': True})

    async def mark_as_read(self, request):
        """Mark a message as read"""
        message_id = request.match_info['message_id']

        for message in self.messages:
            if message['id'] == message_id:
                message['status'] = 'read'

                # If linked to MCP task, update MCP
                if message_id in self.message_to_task:
                    task_id = self.message_to_task[message_id]
                    await self._update_mcp_task_status(task_id, 'acknowledged')

                return web.json_response({'success': True})

        return web.json_response({'error': 'Message not found'}, status=404)

    async def mark_as_unread(self, request):
        """Mark a message as unread"""
        message_id = request.match_info['message_id']

        for message in self.messages:
            if message['id'] == message_id:
                message['status'] = 'unread'
                return web.json_response({'success': True})

        return web.json_response({'error': 'Message not found'}, status=404)

    async def archive_message(self, request):
        """Archive a message"""
        message_id = request.match_info['message_id']

        for message in self.messages:
            if message['id'] == message_id:
                message['status'] = 'archived'

                # If linked to MCP task, update MCP
                if message_id in self.message_to_task:
                    task_id = self.message_to_task[message_id]
                    await self._complete_mcp_task(task_id, 'archived')

                return web.json_response({'success': True})

        return web.json_response({'error': 'Message not found'}, status=404)

    async def mcp_task_to_inbox(self, request):
        """Convert MCP task to inbox message"""
        try:
            data = await request.json()

            # Extract MCP task details
            task_id = data.get('task_id')
            from_agent = data.get('from_agent', 'MCP System')
            to_agent = data.get('to_agent', 'User')
            task = data.get('task', '')
            priority = data.get('priority', 'normal')
            metadata = data.get('metadata', {})

            # Create inbox message
            message = {
                'id': str(uuid.uuid4()),
                'from': f"MCP:{from_agent}",
                'to': to_agent,
                'subject': f"Task: {task[:50]}..." if len(task) > 50 else f"Task: {task}",
                'content': f"**Task Details:**\n\n{task}\n\n**From:** {from_agent}\n**Priority:** {priority}",
                'priority': priority,
                'status': 'unread',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': 'task',
                'metadata': {
                    'mcp_task_id': task_id,
                    'from_agent': from_agent,
                    'original_metadata': metadata
                }
            }

            self.messages.append(message)

            # Store mapping
            self.task_to_message[task_id] = message['id']
            self.message_to_task[message['id']] = task_id

            logger.info(f"✅ Converted MCP task {task_id} to inbox message {message['id']}")

            return web.json_response({
                'success': True,
                'message_id': message['id'],
                'task_id': task_id
            })

        except Exception as e:
            logger.error(f"Error converting MCP task to inbox: {e}")
            return web.json_response({'error': str(e)}, status=400)

    async def inbox_to_mcp_task(self, request):
        """Convert inbox message/action to MCP task"""
        try:
            data = await request.json()

            # Extract inbox message details
            message_id = data.get('message_id')
            action = data.get('action', 'process')
            response = data.get('response', '')

            # Find the message
            message = next((m for m in self.messages if m['id'] == message_id), None)
            if not message:
                return web.json_response({'error': 'Message not found'}, status=404)

            # Check if linked to MCP task
            if message_id in self.message_to_task:
                task_id = self.message_to_task[message_id]

                # Update MCP based on action
                if action == 'accept':
                    await self._update_mcp_task_status(task_id, 'accepted')
                elif action == 'reject':
                    await self._update_mcp_task_status(task_id, 'rejected')
                elif action == 'complete':
                    await self._complete_mcp_task(task_id, response)

                return web.json_response({
                    'success': True,
                    'task_id': task_id,
                    'action': action
                })
            else:
                # Create new MCP task from inbox action
                task_id = await self._create_mcp_task(message, action, response)

                return web.json_response({
                    'success': True,
                    'task_id': task_id,
                    'action': 'created'
                })

        except Exception as e:
            logger.error(f"Error converting inbox to MCP task: {e}")
            return web.json_response({'error': str(e)}, status=400)

    async def websocket_handler(self, request):
        """WebSocket handler for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    if data.get('action') == 'subscribe':
                        # Client wants to subscribe to updates
                        await ws.send_json({
                            'type': 'subscribed',
                            'message': 'Connected to inbox updates'
                        })

                        # Send initial message count
                        await ws.send_json({
                            'type': 'update',
                            'unread_count': len([m for m in self.messages if m['status'] == 'unread']),
                            'total_count': len(self.messages)
                        })

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")

        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            await ws.close()

        return ws

    async def _update_mcp_task_status(self, task_id: str, status: str):
        """Update MCP task status"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "propose_decision",
                    "arguments": {
                        "agent": "inbox-bridge",
                        "decision": f"Task {task_id} status: {status}",
                        "confidence": 1.0 if status == 'accepted' else 0.5,
                        "alternatives": []
                    }
                },
                "id": str(uuid.uuid4())
            }

            response = requests.post(
                f"{self.mcp_server_url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            logger.info(f"Updated MCP task {task_id} status to {status}")

        except Exception as e:
            logger.error(f"Failed to update MCP task status: {e}")

    async def _complete_mcp_task(self, task_id: str, result: str):
        """Mark MCP task as completed"""
        await self._update_mcp_task_status(task_id, f"completed: {result}")

    async def _create_mcp_task(self, message: Dict, action: str, details: str) -> str:
        """Create a new MCP task from inbox message"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "request_collaboration",
                    "arguments": {
                        "from_agent": "inbox-user",
                        "to_agent": message.get('to', 'supervisor'),
                        "task": f"{action}: {message.get('subject', '')} - {details}",
                        "priority": message.get('priority', 'normal')
                    }
                },
                "id": str(uuid.uuid4())
            }

            response = requests.post(
                f"{self.mcp_server_url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result'].get('request_id', 'unknown')

        except Exception as e:
            logger.error(f"Failed to create MCP task: {e}")

        return str(uuid.uuid4())

    async def start(self):
        """Start the Inbox API server"""
        logger.info(f"🚀 Starting Inbox API server on port {self.inbox_api_port}...")

        # Add some test messages
        self._add_test_messages()

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.inbox_api_port)
        await site.start()

        logger.info(f"✅ Inbox API server running at http://localhost:{self.inbox_api_port}")

    def _add_test_messages(self):
        """Add some test messages to the inbox"""
        test_messages = [
            {
                'id': str(uuid.uuid4()),
                'from': 'System',
                'to': 'Admin',
                'subject': 'Welcome to MCP Inbox Integration',
                'content': 'The MCP-Inbox bridge is now active. You can receive MCP tasks as inbox messages.',
                'priority': 'normal',
                'status': 'unread',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': 'notification'
            },
            {
                'id': str(uuid.uuid4()),
                'from': 'MCP:supervisor',
                'to': 'backend-api',
                'subject': 'Task: Implement Authentication System',
                'content': 'Please implement JWT-based authentication with login and registration endpoints.',
                'priority': 'high',
                'status': 'unread',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': 'task',
                'metadata': {
                    'mcp_task_id': 'test_task_001'
                }
            }
        ]

        self.messages.extend(test_messages)
        logger.info(f"Added {len(test_messages)} test messages to inbox")


async def main():
    """Main function to run the bridge"""
    bridge = MCPInboxBridge()
    await bridge.start()

    # Keep the server running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())