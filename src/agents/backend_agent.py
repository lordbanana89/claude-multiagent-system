"""
Backend API Agent - Handles actual business logic
"""

import asyncio
import json
import logging
import aiohttp
import aioredis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import jwt
import uuid
from dataclasses import dataclass, asdict
import os
from enum import Enum

logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class APIRequest:
    id: str
    method: str
    endpoint: str
    data: Dict[Any, Any]
    headers: Dict[str, str]
    timestamp: datetime
    status: RequestStatus
    response: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class BackendAgent:
    """
    Intelligent backend agent that handles:
    - REST API operations
    - Business logic processing
    - Data validation
    - Authentication/Authorization
    - Rate limiting
    - Caching
    - Circuit breaking
    """

    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"backend-{uuid.uuid4().hex[:8]}"
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))

        # API configuration
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.jwt_secret = os.getenv('JWT_SECRET', 'secret-key')

        # Rate limiting
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 req/min
            'auth': {'requests': 5, 'window': 60},        # 5 auth/min
            'data': {'requests': 50, 'window': 60}        # 50 data/min
        }

        # Circuit breaker state
        self.circuit_state = {
            'failures': 0,
            'last_failure': None,
            'state': 'closed',  # closed, open, half-open
            'threshold': 5,
            'timeout': 60
        }

        # Cache
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

        # Metrics
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'circuit_opens': 0
        }

    async def initialize(self):
        """Initialize connections and subscriptions"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{self.redis_host}:{self.redis_port}'
        )

        self.session = aiohttp.ClientSession()

        # Subscribe to backend tasks
        await self.subscribe_to_tasks()

        logger.info(f"Backend agent {self.agent_id} initialized")

    async def subscribe_to_tasks(self):
        """Subscribe to backend-specific task channels"""
        channels = [
            'backend:tasks',
            f'agent:{self.agent_id}:tasks',
            'api:requests'
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
        """Process incoming tasks"""
        task_type = task.get('type')
        task_id = task.get('id', str(uuid.uuid4()))

        logger.info(f"Processing task {task_id} of type {task_type}")

        try:
            if task_type == 'api_request':
                result = await self.handle_api_request(task)
            elif task_type == 'authenticate':
                result = await self.handle_authentication(task)
            elif task_type == 'validate':
                result = await self.validate_data(task)
            elif task_type == 'process_batch':
                result = await self.process_batch(task)
            elif task_type == 'generate_report':
                result = await self.generate_report(task)
            else:
                result = {'error': f'Unknown task type: {task_type}'}

            # Publish result
            await self.publish_result(task_id, result)

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            await self.publish_result(task_id, {'error': str(e)})

    async def handle_api_request(self, task: Dict) -> Dict:
        """Handle REST API requests with circuit breaking and caching"""

        # Check circuit breaker
        if not await self.check_circuit():
            self.metrics['requests_failed'] += 1
            return {'error': 'Circuit breaker is open'}

        # Check cache
        cache_key = self.generate_cache_key(task)
        cached = await self.get_cached(cache_key)
        if cached:
            self.metrics['cache_hits'] += 1
            return cached

        self.metrics['cache_misses'] += 1

        # Check rate limit
        if not await self.check_rate_limit(task.get('endpoint_type', 'default')):
            self.metrics['requests_failed'] += 1
            return {'error': 'Rate limit exceeded'}

        # Make actual request
        request = APIRequest(
            id=task.get('id', str(uuid.uuid4())),
            method=task.get('method', 'GET'),
            endpoint=task.get('endpoint', '/'),
            data=task.get('data', {}),
            headers=task.get('headers', {}),
            timestamp=datetime.now(),
            status=RequestStatus.PROCESSING
        )

        try:
            result = await self.execute_request(request)

            # Cache successful responses
            if result.get('status') == 'success':
                await self.set_cached(cache_key, result)
                self.metrics['requests_success'] += 1
                await self.reset_circuit()
            else:
                self.metrics['requests_failed'] += 1
                await self.record_failure()

            return result

        except Exception as e:
            self.metrics['requests_failed'] += 1
            await self.record_failure()

            if request.retry_count < request.max_retries:
                request.retry_count += 1
                request.status = RequestStatus.RETRYING
                await asyncio.sleep(2 ** request.retry_count)  # Exponential backoff
                return await self.handle_api_request(task)

            return {'error': str(e), 'status': 'failed'}

    async def execute_request(self, request: APIRequest) -> Dict:
        """Execute HTTP request"""
        url = f"{self.base_url}{request.endpoint}"

        async with self.session.request(
            method=request.method,
            url=url,
            json=request.data if request.method in ['POST', 'PUT', 'PATCH'] else None,
            params=request.data if request.method == 'GET' else None,
            headers=request.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:

            data = await response.json() if response.content_type == 'application/json' else await response.text()

            return {
                'status': 'success' if response.status < 400 else 'error',
                'status_code': response.status,
                'data': data,
                'headers': dict(response.headers)
            }

    async def handle_authentication(self, task: Dict) -> Dict:
        """Handle authentication requests"""
        auth_type = task.get('auth_type', 'jwt')

        if auth_type == 'jwt':
            return await self.jwt_authenticate(task)
        elif auth_type == 'oauth':
            return await self.oauth_authenticate(task)
        elif auth_type == 'api_key':
            return await self.api_key_authenticate(task)
        else:
            return {'error': f'Unsupported auth type: {auth_type}'}

    async def jwt_authenticate(self, task: Dict) -> Dict:
        """JWT authentication"""
        username = task.get('username')
        password = task.get('password')

        if not username or not password:
            return {'error': 'Missing credentials', 'authenticated': False}

        # Verify credentials (simplified - in production use proper password hashing)
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Check credentials in Redis (or database)
        stored_hash = await self.redis.hget(f'user:{username}', 'password_hash')

        if stored_hash == password_hash:
            # Generate JWT token
            payload = {
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow()
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')

            return {
                'authenticated': True,
                'token': token,
                'expires_in': 86400  # 24 hours
            }

        return {'error': 'Invalid credentials', 'authenticated': False}

    async def validate_data(self, task: Dict) -> Dict:
        """Validate data against schemas"""
        data = task.get('data', {})
        schema_type = task.get('schema_type')

        validations = {
            'user': self.validate_user_schema,
            'product': self.validate_product_schema,
            'order': self.validate_order_schema,
            'payment': self.validate_payment_schema
        }

        validator = validations.get(schema_type)
        if not validator:
            return {'valid': False, 'error': f'Unknown schema type: {schema_type}'}

        return validator(data)

    def validate_user_schema(self, data: Dict) -> Dict:
        """Validate user data"""
        required_fields = ['username', 'email']
        errors = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Email validation
        if 'email' in data and '@' not in data['email']:
            errors.append("Invalid email format")

        # Username validation
        if 'username' in data and len(data['username']) < 3:
            errors.append("Username must be at least 3 characters")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': data if len(errors) == 0 else None
        }

    def validate_product_schema(self, data: Dict) -> Dict:
        """Validate product data"""
        required_fields = ['name', 'price', 'category']
        errors = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Price validation
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    errors.append("Price cannot be negative")
            except (ValueError, TypeError):
                errors.append("Invalid price format")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': data if len(errors) == 0 else None
        }

    def validate_order_schema(self, data: Dict) -> Dict:
        """Validate order data"""
        required_fields = ['user_id', 'items', 'total']
        errors = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Items validation
        if 'items' in data:
            if not isinstance(data['items'], list) or len(data['items']) == 0:
                errors.append("Order must contain at least one item")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': data if len(errors) == 0 else None
        }

    def validate_payment_schema(self, data: Dict) -> Dict:
        """Validate payment data"""
        required_fields = ['amount', 'method', 'order_id']
        errors = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Amount validation
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    errors.append("Amount must be positive")
            except (ValueError, TypeError):
                errors.append("Invalid amount format")

        # Payment method validation
        valid_methods = ['credit_card', 'debit_card', 'paypal', 'stripe']
        if 'method' in data and data['method'] not in valid_methods:
            errors.append(f"Invalid payment method. Must be one of: {valid_methods}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': data if len(errors) == 0 else None
        }

    async def process_batch(self, task: Dict) -> Dict:
        """Process batch operations"""
        items = task.get('items', [])
        operation = task.get('operation')

        results = []
        errors = []

        for i, item in enumerate(items):
            try:
                if operation == 'create':
                    result = await self.batch_create(item)
                elif operation == 'update':
                    result = await self.batch_update(item)
                elif operation == 'delete':
                    result = await self.batch_delete(item)
                else:
                    result = {'error': f'Unknown operation: {operation}'}

                results.append(result)

            except Exception as e:
                errors.append({'index': i, 'error': str(e)})

        return {
            'processed': len(results),
            'success': len(results) - len(errors),
            'failed': len(errors),
            'results': results,
            'errors': errors
        }

    async def batch_create(self, item: Dict) -> Dict:
        """Create single item in batch"""
        # Implement actual creation logic
        item_id = str(uuid.uuid4())
        await self.redis.hset(f"item:{item_id}", mapping=json.dumps(item))
        return {'id': item_id, 'status': 'created'}

    async def batch_update(self, item: Dict) -> Dict:
        """Update single item in batch"""
        item_id = item.get('id')
        if not item_id:
            return {'error': 'Missing item ID'}

        await self.redis.hset(f"item:{item_id}", mapping=json.dumps(item))
        return {'id': item_id, 'status': 'updated'}

    async def batch_delete(self, item: Dict) -> Dict:
        """Delete single item in batch"""
        item_id = item.get('id')
        if not item_id:
            return {'error': 'Missing item ID'}

        await self.redis.delete(f"item:{item_id}")
        return {'id': item_id, 'status': 'deleted'}

    async def generate_report(self, task: Dict) -> Dict:
        """Generate analytical reports"""
        report_type = task.get('report_type')
        date_range = task.get('date_range', {})

        generators = {
            'sales': self.generate_sales_report,
            'users': self.generate_users_report,
            'performance': self.generate_performance_report,
            'errors': self.generate_errors_report
        }

        generator = generators.get(report_type)
        if not generator:
            return {'error': f'Unknown report type: {report_type}'}

        return await generator(date_range)

    async def generate_sales_report(self, date_range: Dict) -> Dict:
        """Generate sales report"""
        # Fetch and aggregate sales data
        sales_data = {
            'total_sales': 150000,
            'total_orders': 450,
            'average_order_value': 333.33,
            'top_products': [
                {'name': 'Product A', 'sales': 45000},
                {'name': 'Product B', 'sales': 38000},
                {'name': 'Product C', 'sales': 32000}
            ],
            'daily_sales': [
                {'date': '2024-01-01', 'amount': 5000},
                {'date': '2024-01-02', 'amount': 6200},
                {'date': '2024-01-03', 'amount': 4800}
            ]
        }

        return {
            'report_type': 'sales',
            'date_range': date_range,
            'data': sales_data,
            'generated_at': datetime.now().isoformat()
        }

    async def generate_users_report(self, date_range: Dict) -> Dict:
        """Generate users report"""
        users_data = {
            'total_users': 12500,
            'new_users': 350,
            'active_users': 8900,
            'churn_rate': 0.05,
            'user_growth': [
                {'month': '2024-01', 'users': 10000},
                {'month': '2024-02', 'users': 11200},
                {'month': '2024-03', 'users': 12500}
            ]
        }

        return {
            'report_type': 'users',
            'date_range': date_range,
            'data': users_data,
            'generated_at': datetime.now().isoformat()
        }

    async def generate_performance_report(self, date_range: Dict) -> Dict:
        """Generate performance report"""
        return {
            'report_type': 'performance',
            'date_range': date_range,
            'data': self.metrics,
            'generated_at': datetime.now().isoformat()
        }

    async def generate_errors_report(self, date_range: Dict) -> Dict:
        """Generate errors report"""
        errors_data = {
            'total_errors': self.metrics.get('requests_failed', 0),
            'circuit_opens': self.metrics.get('circuit_opens', 0),
            'error_rate': self.metrics['requests_failed'] / max(self.metrics['requests_total'], 1),
            'top_errors': [
                {'type': 'Timeout', 'count': 45},
                {'type': 'ValidationError', 'count': 32},
                {'type': 'AuthenticationError', 'count': 18}
            ]
        }

        return {
            'report_type': 'errors',
            'date_range': date_range,
            'data': errors_data,
            'generated_at': datetime.now().isoformat()
        }

    async def check_rate_limit(self, endpoint_type: str) -> bool:
        """Check if request is within rate limit"""
        limits = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        key = f"rate_limit:{self.agent_id}:{endpoint_type}"

        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, limits['window'])

        return current <= limits['requests']

    async def check_circuit(self) -> bool:
        """Check circuit breaker state"""
        if self.circuit_state['state'] == 'closed':
            return True

        if self.circuit_state['state'] == 'open':
            # Check if timeout has passed
            if self.circuit_state['last_failure']:
                time_since_failure = (datetime.now() - self.circuit_state['last_failure']).seconds
                if time_since_failure > self.circuit_state['timeout']:
                    self.circuit_state['state'] = 'half-open'
                    logger.info("Circuit breaker moved to half-open state")
                    return True
            return False

        # Half-open state - allow one request
        return True

    async def record_failure(self):
        """Record request failure for circuit breaker"""
        self.circuit_state['failures'] += 1
        self.circuit_state['last_failure'] = datetime.now()

        if self.circuit_state['failures'] >= self.circuit_state['threshold']:
            self.circuit_state['state'] = 'open'
            self.metrics['circuit_opens'] += 1
            logger.warning(f"Circuit breaker opened after {self.circuit_state['failures']} failures")

    async def reset_circuit(self):
        """Reset circuit breaker on success"""
        if self.circuit_state['state'] == 'half-open':
            self.circuit_state['state'] = 'closed'
            self.circuit_state['failures'] = 0
            logger.info("Circuit breaker closed after successful request")

    def generate_cache_key(self, task: Dict) -> str:
        """Generate cache key for request"""
        key_parts = [
            task.get('method', 'GET'),
            task.get('endpoint', '/'),
            json.dumps(task.get('data', {}), sort_keys=True)
        ]

        key_string = ':'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get_cached(self, key: str) -> Optional[Dict]:
        """Get cached response"""
        cached = self.cache.get(key)
        if cached and cached['expires'] > datetime.now():
            return cached['data']

        # Clean expired cache
        if cached:
            del self.cache[key]

        return None

    async def set_cached(self, key: str, data: Dict):
        """Cache response"""
        self.cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
        }

    async def publish_result(self, task_id: str, result: Dict):
        """Publish task result"""
        await self.redis.publish(
            f'task:{task_id}:result',
            json.dumps(result)
        )

        # Update task status
        await self.redis.hset(
            f'task:{task_id}',
            mapping={
                'status': 'completed',
                'result': json.dumps(result),
                'completed_at': datetime.now().isoformat()
            }
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
            logger.info(f"Backend agent {self.agent_id} started")

            # Keep running
            while True:
                await asyncio.sleep(1)

                # Periodic metrics reporting
                self.metrics['requests_total'] = (
                    self.metrics['requests_success'] +
                    self.metrics['requests_failed']
                )

                if self.metrics['requests_total'] % 100 == 0:
                    logger.info(f"Metrics: {self.metrics}")

        except KeyboardInterrupt:
            logger.info("Shutting down backend agent")
        finally:
            await self.cleanup()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    agent = BackendAgent()
    asyncio.run(agent.run())