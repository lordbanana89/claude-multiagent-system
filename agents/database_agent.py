"""
Database Agent - Handles all database operations with intelligence
"""

import asyncio
import json
import logging
import asyncpg
import aioredis
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass
import os
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class QueryType(Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    JOIN = "join"
    TRANSACTION = "transaction"


class QueryOptimizer:
    """Optimize database queries"""

    @staticmethod
    def optimize_select(query: str, params: Dict) -> Tuple[str, Dict]:
        """Optimize SELECT queries"""
        # Add LIMIT if not present
        if 'LIMIT' not in query.upper() and 'limit' in params:
            query += f" LIMIT {params['limit']}"

        # Add index hints
        if 'use_index' in params:
            query = query.replace('FROM', f"FROM /*+ INDEX({params['use_index']}) */")

        return query, params

    @staticmethod
    def suggest_indexes(table: str, columns: List[str]) -> List[str]:
        """Suggest indexes for better performance"""
        suggestions = []

        # Single column indexes
        for col in columns:
            suggestions.append(f"CREATE INDEX idx_{table}_{col} ON {table}({col});")

        # Composite indexes for common combinations
        if len(columns) > 1:
            suggestions.append(
                f"CREATE INDEX idx_{table}_{'_'.join(columns[:2])} "
                f"ON {table}({', '.join(columns[:2])});"
            )

        return suggestions


class DatabaseAgent:
    """
    Intelligent database agent that handles:
    - Query execution and optimization
    - Connection pooling
    - Transaction management
    - Schema migrations
    - Data validation
    - Backup and recovery
    - Performance monitoring
    """

    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"database-{uuid.uuid4().hex[:8]}"

        # Database configuration
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'claude_agents'),
            'user': os.getenv('POSTGRES_USER', 'claude'),
            'password': os.getenv('POSTGRES_PASSWORD', 'claude_secret')
        }

        # Redis configuration
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))

        # Query optimizer
        self.optimizer = QueryOptimizer()

        # Connection pool settings
        self.pool_min_size = 10
        self.pool_max_size = 50

        # Query cache
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes

        # Metrics
        self.metrics = {
            'queries_executed': 0,
            'queries_cached': 0,
            'transactions_completed': 0,
            'transactions_rolled_back': 0,
            'connection_errors': 0,
            'slow_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Slow query threshold (ms)
        self.slow_query_threshold = 1000

    async def initialize(self):
        """Initialize database connections"""
        # Create PostgreSQL connection pool
        self.pg_pool = await asyncpg.create_pool(**self.db_config,
                                                  min_size=self.pool_min_size,
                                                  max_size=self.pool_max_size)

        # Create Redis connection
        self.redis = await aioredis.create_redis_pool(
            f'redis://{self.redis_host}:{self.redis_port}'
        )

        # Initialize database schema
        await self.initialize_schema()

        # Subscribe to database tasks
        await self.subscribe_to_tasks()

        logger.info(f"Database agent {self.agent_id} initialized")

    async def initialize_schema(self):
        """Initialize database schema"""
        async with self.pg_pool.acquire() as conn:
            # Create tables if not exist
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) UNIQUE NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    capabilities JSONB DEFAULT '[]'::jsonb,
                    metrics JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    agent_id UUID REFERENCES agents(id),
                    command TEXT,
                    data JSONB DEFAULT '{}'::jsonb,
                    result JSONB,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    definition JSONB NOT NULL,
                    variables JSONB DEFAULT '{}'::jsonb,
                    current_step INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    type VARCHAR(100) NOT NULL,
                    source VARCHAR(255),
                    data JSONB DEFAULT '{}'::jsonb,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id UUID REFERENCES agents(id),
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value NUMERIC,
                    tags JSONB DEFAULT '{}'::jsonb,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_agent ON metrics(agent_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')

    async def subscribe_to_tasks(self):
        """Subscribe to database task channels"""
        channels = [
            'database:tasks',
            f'agent:{self.agent_id}:tasks',
            'db:queries'
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
        """Process database tasks"""
        task_type = task.get('type')
        task_id = task.get('id', str(uuid.uuid4()))

        logger.info(f"Processing database task {task_id} of type {task_type}")

        try:
            if task_type == 'query':
                result = await self.execute_query(task)
            elif task_type == 'transaction':
                result = await self.execute_transaction(task)
            elif task_type == 'migration':
                result = await self.execute_migration(task)
            elif task_type == 'backup':
                result = await self.create_backup(task)
            elif task_type == 'optimize':
                result = await self.optimize_database(task)
            elif task_type == 'analyze':
                result = await self.analyze_query(task)
            else:
                result = {'error': f'Unknown task type: {task_type}'}

            await self.publish_result(task_id, result)

        except Exception as e:
            logger.error(f"Error processing database task {task_id}: {e}")
            await self.publish_result(task_id, {'error': str(e)})

    async def execute_query(self, task: Dict) -> Dict:
        """Execute database query with caching and optimization"""
        query = task.get('query')
        params = task.get('params', {})
        use_cache = task.get('use_cache', True)

        if not query:
            return {'error': 'No query provided'}

        # Check cache
        if use_cache:
            cache_key = self.generate_cache_key(query, params)
            cached = self.get_cached_result(cache_key)
            if cached:
                self.metrics['cache_hits'] += 1
                return cached

        self.metrics['cache_misses'] += 1

        # Determine query type
        query_type = self.detect_query_type(query)

        # Optimize query
        if query_type == QueryType.SELECT:
            query, params = self.optimizer.optimize_select(query, params)

        # Execute query
        start_time = datetime.now()

        try:
            async with self.pg_pool.acquire() as conn:
                if query_type in [QueryType.SELECT, QueryType.AGGREGATE]:
                    rows = await conn.fetch(query, *self.prepare_params(params))
                    result = {'rows': [dict(row) for row in rows], 'count': len(rows)}
                else:
                    result = await conn.execute(query, *self.prepare_params(params))
                    result = {'affected': result.split()[-1] if isinstance(result, str) else 0}

            # Track execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            if execution_time > self.slow_query_threshold:
                self.metrics['slow_queries'] += 1
                logger.warning(f"Slow query detected: {execution_time}ms - {query[:100]}")

            self.metrics['queries_executed'] += 1

            # Cache result if applicable
            if use_cache and query_type == QueryType.SELECT:
                self.cache_result(cache_key, result)

            return {
                'success': True,
                'data': result,
                'execution_time': execution_time,
                'query_type': query_type.value
            }

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return {'error': str(e), 'query': query[:100]}

    async def execute_transaction(self, task: Dict) -> Dict:
        """Execute database transaction"""
        operations = task.get('operations', [])

        if not operations:
            return {'error': 'No operations provided'}

        async with self.pg_pool.acquire() as conn:
            async with conn.transaction():
                results = []

                try:
                    for op in operations:
                        query = op.get('query')
                        params = op.get('params', {})

                        if not query:
                            raise ValueError(f"Operation missing query: {op}")

                        result = await conn.execute(query, *self.prepare_params(params))
                        results.append({'query': query[:50], 'result': result})

                    self.metrics['transactions_completed'] += 1

                    return {
                        'success': True,
                        'operations': len(operations),
                        'results': results
                    }

                except Exception as e:
                    self.metrics['transactions_rolled_back'] += 1
                    logger.error(f"Transaction rolled back: {e}")
                    raise

    async def execute_migration(self, task: Dict) -> Dict:
        """Execute database migration"""
        migration_type = task.get('migration_type')
        version = task.get('version')

        migrations = {
            'add_column': self.migration_add_column,
            'drop_column': self.migration_drop_column,
            'create_table': self.migration_create_table,
            'create_index': self.migration_create_index,
            'alter_table': self.migration_alter_table
        }

        migration_func = migrations.get(migration_type)
        if not migration_func:
            return {'error': f'Unknown migration type: {migration_type}'}

        return await migration_func(task)

    async def migration_add_column(self, task: Dict) -> Dict:
        """Add column migration"""
        table = task.get('table')
        column = task.get('column')
        datatype = task.get('datatype')
        default = task.get('default')

        query = f"ALTER TABLE {table} ADD COLUMN {column} {datatype}"
        if default:
            query += f" DEFAULT {default}"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(query)

        return {'success': True, 'migration': 'add_column', 'table': table, 'column': column}

    async def migration_drop_column(self, task: Dict) -> Dict:
        """Drop column migration"""
        table = task.get('table')
        column = task.get('column')

        query = f"ALTER TABLE {table} DROP COLUMN {column}"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(query)

        return {'success': True, 'migration': 'drop_column', 'table': table, 'column': column}

    async def migration_create_table(self, task: Dict) -> Dict:
        """Create table migration"""
        table = task.get('table')
        columns = task.get('columns', {})

        column_defs = []
        for col_name, col_def in columns.items():
            column_defs.append(f"{col_name} {col_def}")

        query = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(query)

        return {'success': True, 'migration': 'create_table', 'table': table}

    async def migration_create_index(self, task: Dict) -> Dict:
        """Create index migration"""
        table = task.get('table')
        columns = task.get('columns', [])
        unique = task.get('unique', False)

        index_name = f"idx_{table}_{'_'.join(columns)}"
        unique_str = "UNIQUE " if unique else ""

        query = f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table}({', '.join(columns)})"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(query)

        return {'success': True, 'migration': 'create_index', 'index': index_name}

    async def migration_alter_table(self, task: Dict) -> Dict:
        """Alter table migration"""
        table = task.get('table')
        alterations = task.get('alterations', [])

        async with self.pg_pool.acquire() as conn:
            for alteration in alterations:
                query = f"ALTER TABLE {table} {alteration}"
                await conn.execute(query)

        return {'success': True, 'migration': 'alter_table', 'table': table}

    async def create_backup(self, task: Dict) -> Dict:
        """Create database backup"""
        backup_type = task.get('backup_type', 'full')
        tables = task.get('tables', [])

        backup_id = str(uuid.uuid4())
        backup_data = {}

        async with self.pg_pool.acquire() as conn:
            if backup_type == 'full' or not tables:
                # Get all tables
                tables_query = """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                """
                tables = [row['tablename'] for row in await conn.fetch(tables_query)]

            for table in tables:
                # Export table data
                rows = await conn.fetch(f"SELECT * FROM {table}")
                backup_data[table] = [dict(row) for row in rows]

        # Store backup metadata
        await self.redis.hset(
            f"backup:{backup_id}",
            mapping={
                'type': backup_type,
                'tables': json.dumps(tables),
                'timestamp': datetime.now().isoformat(),
                'size': len(json.dumps(backup_data))
            }
        )

        # Store backup data
        await self.redis.set(
            f"backup:{backup_id}:data",
            json.dumps(backup_data),
            expire=86400  # 24 hours
        )

        return {
            'success': True,
            'backup_id': backup_id,
            'type': backup_type,
            'tables': len(tables),
            'size': len(json.dumps(backup_data))
        }

    async def optimize_database(self, task: Dict) -> Dict:
        """Optimize database performance"""
        optimization_type = task.get('optimization_type', 'vacuum')

        async with self.pg_pool.acquire() as conn:
            if optimization_type == 'vacuum':
                await conn.execute("VACUUM ANALYZE")
                result = "Vacuum analyze completed"

            elif optimization_type == 'reindex':
                tables = task.get('tables', [])
                for table in tables:
                    await conn.execute(f"REINDEX TABLE {table}")
                result = f"Reindexed {len(tables)} tables"

            elif optimization_type == 'analyze':
                await conn.execute("ANALYZE")
                result = "Database statistics updated"

            else:
                return {'error': f'Unknown optimization type: {optimization_type}'}

        return {'success': True, 'optimization': optimization_type, 'result': result}

    async def analyze_query(self, task: Dict) -> Dict:
        """Analyze query performance"""
        query = task.get('query')

        if not query:
            return {'error': 'No query provided'}

        async with self.pg_pool.acquire() as conn:
            # Get query plan
            plan_query = f"EXPLAIN ANALYZE {query}"
            plan = await conn.fetch(plan_query)

            # Parse execution plan
            plan_text = [row[0] for row in plan]

            # Extract key metrics
            execution_time = None
            planning_time = None

            for line in plan_text:
                if 'Execution Time' in line:
                    execution_time = float(line.split(':')[1].strip().split()[0])
                elif 'Planning Time' in line:
                    planning_time = float(line.split(':')[1].strip().split()[0])

            # Suggest optimizations
            suggestions = []

            if execution_time and execution_time > 1000:
                suggestions.append("Query is slow. Consider adding indexes.")

            if 'Seq Scan' in str(plan_text):
                suggestions.append("Sequential scan detected. Consider adding an index.")

            if 'Sort' in str(plan_text):
                suggestions.append("Sort operation detected. Consider adding an index on ORDER BY columns.")

            return {
                'success': True,
                'execution_time': execution_time,
                'planning_time': planning_time,
                'plan': plan_text,
                'suggestions': suggestions
            }

    def detect_query_type(self, query: str) -> QueryType:
        """Detect type of SQL query"""
        query_upper = query.strip().upper()

        if query_upper.startswith('SELECT'):
            if any(keyword in query_upper for keyword in ['GROUP BY', 'COUNT(', 'SUM(', 'AVG(']):
                return QueryType.AGGREGATE
            elif 'JOIN' in query_upper:
                return QueryType.JOIN
            else:
                return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('BEGIN'):
            return QueryType.TRANSACTION
        else:
            return QueryType.SELECT

    def prepare_params(self, params: Dict) -> List:
        """Prepare query parameters"""
        if isinstance(params, dict):
            return list(params.values())
        elif isinstance(params, list):
            return params
        else:
            return []

    def generate_cache_key(self, query: str, params: Dict) -> str:
        """Generate cache key for query"""
        key_string = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_cached_result(self, key: str) -> Optional[Dict]:
        """Get cached query result"""
        cached = self.query_cache.get(key)
        if cached and cached['expires'] > datetime.now():
            return cached['data']
        return None

    def cache_result(self, key: str, result: Dict):
        """Cache query result"""
        self.query_cache[key] = {
            'data': result,
            'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
        }
        self.metrics['queries_cached'] += 1

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
        if hasattr(self, 'pg_pool'):
            await self.pg_pool.close()

        if hasattr(self, 'redis'):
            self.redis.close()
            await self.redis.wait_closed()

    async def run(self):
        """Main execution loop"""
        try:
            await self.initialize()
            logger.info(f"Database agent {self.agent_id} started")

            # Keep running
            while True:
                await asyncio.sleep(30)

                # Log metrics periodically
                logger.info(f"Database metrics: {self.metrics}")

                # Clean expired cache
                now = datetime.now()
                expired_keys = [
                    key for key, value in self.query_cache.items()
                    if value['expires'] <= now
                ]
                for key in expired_keys:
                    del self.query_cache[key]

        except KeyboardInterrupt:
            logger.info("Shutting down database agent")
        finally:
            await self.cleanup()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    agent = DatabaseAgent()
    asyncio.run(agent.run())