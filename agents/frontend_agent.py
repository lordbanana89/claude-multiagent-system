"""
Frontend UI Agent - Handles UI generation and user interactions
"""

import asyncio
import json
import logging
import aiohttp
import aioredis
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import os
from enum import Enum
from jinja2 import Environment, FileSystemLoader
import hashlib

logger = logging.getLogger(__name__)


class UIComponentType(Enum):
    DASHBOARD = "dashboard"
    FORM = "form"
    TABLE = "table"
    CHART = "chart"
    MODAL = "modal"
    NOTIFICATION = "notification"
    NAVIGATION = "navigation"


class FrontendAgent:
    """
    Intelligent frontend agent that handles:
    - Dynamic UI generation
    - Form validation
    - Real-time updates
    - WebSocket communication
    - Template rendering
    - Asset optimization
    - User session management
    """

    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"frontend-{uuid.uuid4().hex[:8]}"

        # Configuration
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.template_dir = os.getenv('TEMPLATE_DIR', './web/templates')
        self.static_dir = os.getenv('STATIC_DIR', './web/static')

        # WebSocket connections
        self.websocket_connections = {}

        # UI component cache
        self.component_cache = {}
        self.cache_ttl = 300  # 5 minutes

        # Session store
        self.sessions = {}

        # Metrics
        self.metrics = {
            'components_rendered': 0,
            'forms_validated': 0,
            'websocket_messages': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'active_sessions': 0,
            'errors': 0
        }

        # Initialize template engine
        self.template_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )

    async def initialize(self):
        """Initialize connections"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{self.redis_host}:{self.redis_port}'
        )

        self.session = aiohttp.ClientSession()

        # Subscribe to frontend tasks
        await self.subscribe_to_tasks()

        logger.info(f"Frontend agent {self.agent_id} initialized")

    async def subscribe_to_tasks(self):
        """Subscribe to frontend task channels"""
        channels = [
            'frontend:tasks',
            f'agent:{self.agent_id}:tasks',
            'ui:updates'
        ]

        for channel in channels:
            asyncio.create_task(self.process_channel(channel))

    async def process_channel(self, channel: str):
        """Process messages from a specific channel"""
        sub = await aioredis.create_redis(
            f'redis://{self.redis_host}:{self.redis_port}'
        )
        ch = (await sub.subscribe(channel))[0]

        while await ch.wait_message():
            message = await ch.get_json()
            if message:
                await self.handle_task(message)

    async def handle_task(self, task: Dict):
        """Process frontend tasks"""
        task_type = task.get('type')
        task_id = task.get('id', str(uuid.uuid4()))

        logger.info(f"Processing frontend task {task_id} of type {task_type}")

        try:
            if task_type == 'render_component':
                result = await self.render_component(task)
            elif task_type == 'validate_form':
                result = await self.validate_form(task)
            elif task_type == 'generate_dashboard':
                result = await self.generate_dashboard(task)
            elif task_type == 'update_realtime':
                result = await self.update_realtime(task)
            elif task_type == 'create_session':
                result = await self.create_session(task)
            elif task_type == 'generate_report_ui':
                result = await self.generate_report_ui(task)
            elif task_type == 'build_navigation':
                result = await self.build_navigation(task)
            else:
                result = {'error': f'Unknown task type: {task_type}'}

            await self.publish_result(task_id, result)

        except Exception as e:
            logger.error(f"Error processing frontend task {task_id}: {e}")
            self.metrics['errors'] += 1
            await self.publish_result(task_id, {'error': str(e)})

    async def render_component(self, task: Dict) -> Dict:
        """Render UI component"""
        component_type = task.get('component_type')
        data = task.get('data', {})
        options = task.get('options', {})

        # Check cache
        cache_key = self.generate_cache_key(component_type, data)
        cached = self.get_cached_component(cache_key)
        if cached:
            self.metrics['cache_hits'] += 1
            return cached

        self.metrics['cache_misses'] += 1

        # Render based on component type
        renderers = {
            UIComponentType.DASHBOARD.value: self.render_dashboard,
            UIComponentType.FORM.value: self.render_form,
            UIComponentType.TABLE.value: self.render_table,
            UIComponentType.CHART.value: self.render_chart,
            UIComponentType.MODAL.value: self.render_modal,
            UIComponentType.NOTIFICATION.value: self.render_notification,
            UIComponentType.NAVIGATION.value: self.render_navigation
        }

        renderer = renderers.get(component_type)
        if not renderer:
            return {'error': f'Unknown component type: {component_type}'}

        html = await renderer(data, options)
        self.metrics['components_rendered'] += 1

        result = {
            'html': html,
            'component_type': component_type,
            'rendered_at': datetime.now().isoformat()
        }

        # Cache result
        self.cache_component(cache_key, result)

        return result

    async def render_dashboard(self, data: Dict, options: Dict) -> str:
        """Render dashboard component"""
        template = self.template_env.get_template('dashboard.html')

        # Prepare dashboard data
        dashboard_data = {
            'title': data.get('title', 'Dashboard'),
            'widgets': data.get('widgets', []),
            'metrics': data.get('metrics', {}),
            'charts': data.get('charts', []),
            'refresh_interval': options.get('refresh_interval', 30000)
        }

        # Add real-time update script
        dashboard_data['websocket_url'] = f"ws://{os.getenv('WS_HOST', 'localhost')}:8001/ws"

        return template.render(**dashboard_data)

    async def render_form(self, data: Dict, options: Dict) -> str:
        """Render form component"""
        template = self.template_env.get_template('form.html')

        form_data = {
            'action': data.get('action', '/submit'),
            'method': data.get('method', 'POST'),
            'fields': data.get('fields', []),
            'validation': options.get('validation', {}),
            'csrf_token': self.generate_csrf_token()
        }

        # Add field validation attributes
        for field in form_data['fields']:
            if field['name'] in form_data['validation']:
                field['validation'] = form_data['validation'][field['name']]

        return template.render(**form_data)

    async def render_table(self, data: Dict, options: Dict) -> str:
        """Render table component"""
        template = self.template_env.get_template('table.html')

        table_data = {
            'columns': data.get('columns', []),
            'rows': data.get('rows', []),
            'pagination': options.get('pagination', {'enabled': True, 'per_page': 20}),
            'sortable': options.get('sortable', True),
            'filterable': options.get('filterable', True),
            'actions': options.get('actions', [])
        }

        # Add data attributes for JavaScript enhancement
        table_data['data_source'] = options.get('data_source', '/api/data')

        return template.render(**table_data)

    async def render_chart(self, data: Dict, options: Dict) -> str:
        """Render chart component"""
        template = self.template_env.get_template('chart.html')

        chart_types = {
            'line': 'LineChart',
            'bar': 'BarChart',
            'pie': 'PieChart',
            'area': 'AreaChart',
            'scatter': 'ScatterChart'
        }

        chart_data = {
            'type': chart_types.get(data.get('type', 'line'), 'LineChart'),
            'data': json.dumps(data.get('data', [])),
            'options': json.dumps({
                'title': data.get('title', ''),
                'width': options.get('width', 600),
                'height': options.get('height', 400),
                'colors': options.get('colors', ['#4285f4', '#db4437', '#f4b400']),
                'animation': options.get('animation', True)
            }),
            'chart_id': f"chart_{uuid.uuid4().hex[:8]}"
        }

        return template.render(**chart_data)

    async def render_modal(self, data: Dict, options: Dict) -> str:
        """Render modal component"""
        template = self.template_env.get_template('modal.html')

        modal_data = {
            'id': data.get('id', f"modal_{uuid.uuid4().hex[:8]}"),
            'title': data.get('title', 'Modal'),
            'content': data.get('content', ''),
            'footer': data.get('footer', ''),
            'size': options.get('size', 'medium'),
            'closable': options.get('closable', True)
        }

        return template.render(**modal_data)

    async def render_notification(self, data: Dict, options: Dict) -> str:
        """Render notification component"""
        template = self.template_env.get_template('notification.html')

        notification_types = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }

        notification_data = {
            'type': notification_types.get(data.get('type', 'info'), 'alert-info'),
            'message': data.get('message', ''),
            'title': data.get('title', ''),
            'dismissible': options.get('dismissible', True),
            'auto_dismiss': options.get('auto_dismiss', 5000)
        }

        return template.render(**notification_data)

    async def render_navigation(self, data: Dict, options: Dict) -> str:
        """Render navigation component"""
        template = self.template_env.get_template('navigation.html')

        nav_data = {
            'brand': data.get('brand', 'Claude Agent System'),
            'items': data.get('items', []),
            'user': data.get('user'),
            'style': options.get('style', 'navbar'),
            'position': options.get('position', 'top')
        }

        # Add active state based on current path
        current_path = options.get('current_path', '/')
        for item in nav_data['items']:
            item['active'] = item.get('href') == current_path

        return template.render(**nav_data)

    async def validate_form(self, task: Dict) -> Dict:
        """Validate form data"""
        form_data = task.get('data', {})
        rules = task.get('rules', {})

        errors = {}
        validated_data = {}

        for field, value in form_data.items():
            field_rules = rules.get(field, {})

            # Required validation
            if field_rules.get('required') and not value:
                errors[field] = f"{field} is required"
                continue

            # Type validation
            expected_type = field_rules.get('type')
            if expected_type:
                if expected_type == 'email' and '@' not in str(value):
                    errors[field] = f"{field} must be a valid email"
                elif expected_type == 'number':
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        errors[field] = f"{field} must be a number"
                elif expected_type == 'integer':
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        errors[field] = f"{field} must be an integer"

            # Length validation
            min_length = field_rules.get('min_length')
            max_length = field_rules.get('max_length')

            if min_length and len(str(value)) < min_length:
                errors[field] = f"{field} must be at least {min_length} characters"

            if max_length and len(str(value)) > max_length:
                errors[field] = f"{field} must be at most {max_length} characters"

            # Pattern validation
            pattern = field_rules.get('pattern')
            if pattern:
                import re
                if not re.match(pattern, str(value)):
                    errors[field] = f"{field} format is invalid"

            # Custom validation
            custom = field_rules.get('custom')
            if custom and callable(custom):
                error = custom(value)
                if error:
                    errors[field] = error

            if field not in errors:
                validated_data[field] = value

        self.metrics['forms_validated'] += 1

        return {
            'valid': len(errors) == 0,
            'data': validated_data,
            'errors': errors
        }

    async def generate_dashboard(self, task: Dict) -> Dict:
        """Generate complete dashboard"""
        dashboard_type = task.get('dashboard_type', 'default')

        # Fetch data for dashboard
        metrics = await self.fetch_metrics()
        charts = await self.generate_charts(dashboard_type)
        widgets = await self.generate_widgets(dashboard_type)

        dashboard_data = {
            'title': f"{dashboard_type.title()} Dashboard",
            'metrics': metrics,
            'charts': charts,
            'widgets': widgets
        }

        html = await self.render_dashboard(dashboard_data, {})

        return {
            'html': html,
            'data': dashboard_data,
            'generated_at': datetime.now().isoformat()
        }

    async def fetch_metrics(self) -> Dict:
        """Fetch system metrics"""
        # Get metrics from Redis
        metrics = {}

        keys = await self.redis.keys('metrics:*')
        for key in keys:
            metric_name = key.decode().split(':')[1]
            value = await self.redis.get(key)
            if value:
                metrics[metric_name] = json.loads(value)

        return metrics

    async def generate_charts(self, dashboard_type: str) -> List[Dict]:
        """Generate charts for dashboard"""
        charts = []

        if dashboard_type == 'performance':
            charts.append({
                'type': 'line',
                'title': 'Response Time',
                'data': await self.get_performance_data()
            })
            charts.append({
                'type': 'bar',
                'title': 'Request Volume',
                'data': await self.get_request_volume()
            })

        elif dashboard_type == 'agents':
            charts.append({
                'type': 'pie',
                'title': 'Agent Status',
                'data': await self.get_agent_status()
            })
            charts.append({
                'type': 'bar',
                'title': 'Task Distribution',
                'data': await self.get_task_distribution()
            })

        return charts

    async def generate_widgets(self, dashboard_type: str) -> List[Dict]:
        """Generate widgets for dashboard"""
        widgets = []

        if dashboard_type == 'performance':
            widgets.extend([
                {'type': 'metric', 'title': 'Avg Response Time', 'value': '125ms'},
                {'type': 'metric', 'title': 'Success Rate', 'value': '99.5%'},
                {'type': 'metric', 'title': 'Active Connections', 'value': '342'}
            ])

        elif dashboard_type == 'agents':
            widgets.extend([
                {'type': 'metric', 'title': 'Active Agents', 'value': '8'},
                {'type': 'metric', 'title': 'Tasks Completed', 'value': '1,245'},
                {'type': 'metric', 'title': 'Error Rate', 'value': '0.3%'}
            ])

        return widgets

    async def get_performance_data(self) -> List:
        """Get performance data for charts"""
        # Simulated data - in production, fetch from metrics store
        return [
            ['Time', 'Response Time'],
            ['00:00', 120],
            ['01:00', 135],
            ['02:00', 115],
            ['03:00', 128],
            ['04:00', 142]
        ]

    async def get_request_volume(self) -> List:
        """Get request volume data"""
        return [
            ['Hour', 'Requests'],
            ['00:00', 450],
            ['01:00', 380],
            ['02:00', 290],
            ['03:00', 310],
            ['04:00', 425]
        ]

    async def get_agent_status(self) -> List:
        """Get agent status data"""
        return [
            ['Status', 'Count'],
            ['Active', 6],
            ['Idle', 2],
            ['Error', 1]
        ]

    async def get_task_distribution(self) -> List:
        """Get task distribution data"""
        return [
            ['Agent', 'Tasks'],
            ['Backend', 450],
            ['Database', 380],
            ['Frontend', 290],
            ['Testing', 310]
        ]

    async def update_realtime(self, task: Dict) -> Dict:
        """Send real-time updates to connected clients"""
        update_type = task.get('update_type')
        data = task.get('data')

        # Send to all connected WebSocket clients
        for ws_id, ws in self.websocket_connections.items():
            try:
                await ws.send_json({
                    'type': update_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error sending to WebSocket {ws_id}: {e}")
                del self.websocket_connections[ws_id]

        self.metrics['websocket_messages'] += len(self.websocket_connections)

        return {
            'sent_to': len(self.websocket_connections),
            'update_type': update_type
        }

    async def create_session(self, task: Dict) -> Dict:
        """Create user session"""
        user_id = task.get('user_id')
        session_data = task.get('data', {})

        session_id = str(uuid.uuid4())
        session = {
            'id': session_id,
            'user_id': user_id,
            'data': session_data,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat()
        }

        self.sessions[session_id] = session
        self.metrics['active_sessions'] = len(self.sessions)

        # Store in Redis for persistence
        await self.redis.setex(
            f"session:{session_id}",
            3600,  # 1 hour expiry
            json.dumps(session)
        )

        return {
            'session_id': session_id,
            'expires_in': 3600
        }

    async def generate_report_ui(self, task: Dict) -> Dict:
        """Generate report UI"""
        report_data = task.get('data', {})
        report_type = task.get('report_type', 'general')

        template = self.template_env.get_template('report.html')

        report_html = template.render(
            title=report_data.get('title', 'Report'),
            sections=report_data.get('sections', []),
            data=report_data.get('data', {}),
            footer=report_data.get('footer', '')
        )

        return {
            'html': report_html,
            'report_type': report_type
        }

    async def build_navigation(self, task: Dict) -> Dict:
        """Build navigation menu"""
        user_role = task.get('user_role', 'guest')

        # Build menu items based on user role
        menu_items = [
            {'label': 'Dashboard', 'href': '/', 'icon': 'dashboard'}
        ]

        if user_role in ['admin', 'user']:
            menu_items.extend([
                {'label': 'Agents', 'href': '/agents', 'icon': 'robot'},
                {'label': 'Tasks', 'href': '/tasks', 'icon': 'tasks'},
                {'label': 'Workflows', 'href': '/workflows', 'icon': 'workflow'}
            ])

        if user_role == 'admin':
            menu_items.extend([
                {'label': 'Settings', 'href': '/settings', 'icon': 'settings'},
                {'label': 'Users', 'href': '/users', 'icon': 'users'}
            ])

        nav_data = {
            'items': menu_items,
            'user': task.get('user')
        }

        html = await self.render_navigation(nav_data, {})

        return {
            'html': html,
            'menu_items': menu_items
        }

    def generate_cache_key(self, component_type: str, data: Dict) -> str:
        """Generate cache key for component"""
        key_string = f"{component_type}:{json.dumps(data, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_cached_component(self, key: str) -> Optional[Dict]:
        """Get cached component"""
        cached = self.component_cache.get(key)
        if cached and cached['expires'] > datetime.now():
            return cached['data']
        return None

    def cache_component(self, key: str, result: Dict):
        """Cache component result"""
        from datetime import timedelta
        self.component_cache[key] = {
            'data': result,
            'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
        }

    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        token = str(uuid.uuid4())
        # Store token in session or Redis
        return token

    async def publish_result(self, task_id: str, result: Dict):
        """Publish task result"""
        await self.redis.publish(
            f'task:{task_id}:result',
            json.dumps(result)
        )

    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            await self.session.close()

        if hasattr(self, 'redis'):
            self.redis.close()
            await self.redis.wait_closed()

    async def run(self):
        """Main execution loop"""
        try:
            await self.initialize()
            logger.info(f"Frontend agent {self.agent_id} started")

            while True:
                await asyncio.sleep(30)

                # Clean expired sessions
                expired = []
                for sid, session in self.sessions.items():
                    last_accessed = datetime.fromisoformat(session['last_accessed'])
                    if (datetime.now() - last_accessed).seconds > 3600:
                        expired.append(sid)

                for sid in expired:
                    del self.sessions[sid]

                self.metrics['active_sessions'] = len(self.sessions)
                logger.info(f"Frontend metrics: {self.metrics}")

        except KeyboardInterrupt:
            logger.info("Shutting down frontend agent")
        finally:
            await self.cleanup()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    agent = FrontendAgent()
    asyncio.run(agent.run())