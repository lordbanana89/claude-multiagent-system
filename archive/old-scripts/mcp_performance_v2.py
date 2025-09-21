#!/usr/bin/env python3
"""
MCP v2 Performance Optimization Module
Implements caching, connection pooling, query optimization, and monitoring
"""

import asyncio
import json
import time
import logging
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import lru_cache, wraps
import hashlib
import psutil
# import aioredis  # Optional Redis support
from aiocache import Cache, cached
from aiocache.serializers import JsonSerializer
import aiosqlite
from concurrent.futures import ThreadPoolExecutor
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    timestamp: float
    request_count: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    cache_hit_rate: float
    db_query_time: float
    concurrent_connections: int

class MCPPerformance:
    def __init__(self, redis_url: str = "redis://localhost:6379",
                 db_path: str = "/tmp/mcp_state.db"):
        self.redis_url = redis_url
        self.db_path = db_path
        self.cache = Cache(Cache.MEMORY)
        self.redis_cache = None
        self.db_pool = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.metrics_buffer = []
        self.request_times = []
        self.cache_stats = {"hits": 0, "misses": 0}
        self.init_performance_tables()

    async def initialize(self):
        """Initialize async resources"""
        # Redis is optional - use memory cache by default
        self.redis_cache = None
        logger.info("Using memory cache (Redis optional)")

        # Initialize SQLite connection pool
        self.db_pool = await self._create_db_pool()

    async def _create_db_pool(self):
        """Create database connection pool"""
        # SQLite doesn't have true connection pooling, but we can simulate it
        connections = []
        for _ in range(5):
            conn = await aiosqlite.connect(self.db_path)
            await conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=10000")
            await conn.execute("PRAGMA temp_store=MEMORY")
            connections.append(conn)
        return connections

    def init_performance_tables(self):
        """Initialize performance monitoring tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                metadata TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pm_timestamp ON performance_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pm_metric_type ON performance_metrics(metric_type)")

        # Query performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT NOT NULL,
                query_text TEXT,
                execution_time REAL NOT NULL,
                row_count INTEGER,
                timestamp REAL NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qp_query_hash ON query_performance(query_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qp_execution_time ON query_performance(execution_time)")

        # Cache statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                cache_type TEXT NOT NULL,
                hits INTEGER,
                misses INTEGER,
                hit_rate REAL,
                memory_usage INTEGER
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cs_timestamp ON cache_stats(timestamp)")

        conn.commit()
        conn.close()

    # Caching decorators
    def cache_result(self, ttl: int = 300):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)

                # Try to get from cache
                cached_value = await self._get_cached(cache_key)
                if cached_value is not None:
                    self.cache_stats["hits"] += 1
                    return cached_value

                self.cache_stats["misses"] += 1

                # Execute function
                result = await func(*args, **kwargs)

                # Store in cache
                await self._set_cached(cache_key, result, ttl)

                return result
            return wrapper
        return decorator

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key"""
        key_data = {
            "func": func_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or memory)"""
        if self.redis_cache:
            try:
                # Redis cache operations are commented out for now
                # as aioredis is not imported
                pass
            except Exception as e:
                logger.debug(f"Redis get failed: {e}")

        # Fallback to memory cache
        return await self.cache.get(key)

    async def _set_cached(self, key: str, value: Any, ttl: int):
        """Set value in cache (Redis or memory)"""
        if self.redis_cache:
            try:
                # Redis cache operations are commented out for now
                # as aioredis is not imported
                pass
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")

        # Also set in memory cache
        await self.cache.set(key, value, ttl=ttl)

    # Database query optimization
    async def execute_query_optimized(self, query: str, params: tuple = ()) -> Any:
        """Execute database query with optimization and caching"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        start_time = time.time()

        # Check query cache for SELECT statements
        if query.strip().upper().startswith("SELECT"):
            cache_key = f"query_{query_hash}_{str(params)}"
            cached_result = await self._get_cached(cache_key)
            if cached_result:
                return cached_result

        # Get connection from pool
        conn = await self._get_db_connection()

        try:
            cursor = await conn.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                result = await cursor.fetchall()
                # Cache the result
                await self._set_cached(f"query_{query_hash}_{str(params)}", result, 60)
            else:
                await conn.commit()
                result = cursor.lastrowid

            execution_time = time.time() - start_time

            # Log query performance
            await self._log_query_performance(
                query_hash, query, execution_time,
                len(result) if isinstance(result, list) else 1
            )

            return result

        finally:
            # Return connection to pool
            await self._return_db_connection(conn)

    async def _get_db_connection(self):
        """Get a connection from the pool"""
        if self.db_pool:
            return self.db_pool.pop(0) if self.db_pool else await aiosqlite.connect(self.db_path)
        return await aiosqlite.connect(self.db_path)

    async def _return_db_connection(self, conn):
        """Return connection to the pool"""
        if self.db_pool and len(self.db_pool) < 5:
            self.db_pool.append(conn)
        else:
            await conn.close()

    async def _log_query_performance(self, query_hash: str, query: str,
                                    execution_time: float, row_count: int):
        """Log query performance metrics"""
        conn = await aiosqlite.connect(self.db_path)
        await conn.execute("""
            INSERT INTO query_performance
            (query_hash, query_text, execution_time, row_count, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (query_hash, query[:500], execution_time, row_count, time.time()))
        await conn.commit()
        await conn.close()

    # Request batching
    async def batch_requests(self, requests: List[Dict], batch_size: int = 10) -> List:
        """Batch multiple requests for efficient processing"""
        results = []

        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]

            # Process batch concurrently
            tasks = [self._process_single_request(req) for req in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        return results

    async def _process_single_request(self, request: Dict) -> Dict:
        """Process a single request"""
        start_time = time.time()

        try:
            # Simulate request processing
            await asyncio.sleep(0.01)  # Replace with actual processing
            result = {"status": "success", "data": request}
        except Exception as e:
            result = {"status": "error", "error": str(e)}

        self.request_times.append(time.time() - start_time)
        return result

    # Performance monitoring
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        current_time = time.time()

        # Calculate response time percentiles
        if self.request_times:
            sorted_times = sorted(self.request_times[-1000:])  # Last 1000 requests
            avg_time = statistics.mean(sorted_times)
            p95_time = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 20 else avg_time
            p99_time = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 100 else p95_time
        else:
            avg_time = p95_time = p99_time = 0

        # Calculate cache hit rate
        total_cache_ops = self.cache_stats["hits"] + self.cache_stats["misses"]
        cache_hit_rate = self.cache_stats["hits"] / total_cache_ops if total_cache_ops > 0 else 0

        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent

        # Get average database query time
        db_query_time = await self._get_avg_query_time()

        metrics = PerformanceMetrics(
            timestamp=current_time,
            request_count=len(self.request_times),
            avg_response_time=avg_time,
            p95_response_time=p95_time,
            p99_response_time=p99_time,
            error_rate=0.0,  # Calculate from actual errors
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            cache_hit_rate=cache_hit_rate,
            db_query_time=db_query_time,
            concurrent_connections=0  # Get from actual server
        )

        # Store metrics
        await self._store_metrics(metrics)

        return metrics

    async def _get_avg_query_time(self) -> float:
        """Get average database query time"""
        conn = await aiosqlite.connect(self.db_path)
        cursor = await conn.execute("""
            SELECT AVG(execution_time)
            FROM query_performance
            WHERE timestamp > ?
        """, (time.time() - 300,))  # Last 5 minutes

        result = await cursor.fetchone()
        await conn.close()

        return result[0] if result and result[0] else 0.0

    async def _store_metrics(self, metrics: PerformanceMetrics):
        """Store performance metrics"""
        conn = await aiosqlite.connect(self.db_path)

        metrics_data = [
            ("response_time_avg", metrics.avg_response_time),
            ("response_time_p95", metrics.p95_response_time),
            ("response_time_p99", metrics.p99_response_time),
            ("cpu_usage", metrics.cpu_usage),
            ("memory_usage", metrics.memory_usage),
            ("cache_hit_rate", metrics.cache_hit_rate),
            ("db_query_time", metrics.db_query_time)
        ]

        for metric_type, value in metrics_data:
            await conn.execute("""
                INSERT INTO performance_metrics
                (timestamp, metric_type, value, metadata)
                VALUES (?, ?, ?, ?)
            """, (metrics.timestamp, metric_type, value, json.dumps({})))

        await conn.commit()
        await conn.close()

    # Load balancing
    async def get_least_loaded_server(self, servers: List[str]) -> Optional[str]:
        """Get the least loaded server from a list"""
        server_loads = {}

        for server in servers:
            # Check server load (simplified - would check actual metrics)
            load = await self._check_server_load(server)
            server_loads[server] = load

        # Return server with lowest load
        if server_loads:
            return min(server_loads, key=lambda k: server_loads[k])
        return None

    async def _check_server_load(self, server: str) -> float:
        """Check server load (mock implementation)"""
        # In production, would query actual server metrics
        return psutil.cpu_percent() if server == "localhost" else 50.0

    # Query optimization suggestions
    async def analyze_slow_queries(self, threshold: float = 0.1) -> List[Dict]:
        """Analyze and identify slow queries"""
        conn = await aiosqlite.connect(self.db_path)
        cursor = await conn.execute("""
            SELECT query_hash, query_text, AVG(execution_time) as avg_time,
                   COUNT(*) as exec_count
            FROM query_performance
            WHERE execution_time > ?
            GROUP BY query_hash
            ORDER BY avg_time DESC
            LIMIT 10
        """, (threshold,))

        slow_queries = []
        async for row in cursor:
            suggestions = self._get_optimization_suggestions(row[1])
            slow_queries.append({
                "query_hash": row[0],
                "query": row[1],
                "avg_time": row[2],
                "execution_count": row[3],
                "suggestions": suggestions
            })

        await conn.close()
        return slow_queries

    def _get_optimization_suggestions(self, query: str) -> List[str]:
        """Get query optimization suggestions"""
        suggestions = []
        query_upper = query.upper()

        if "SELECT *" in query_upper:
            suggestions.append("Avoid SELECT *, specify only needed columns")

        if "NOT IN" in query_upper:
            suggestions.append("Consider using NOT EXISTS instead of NOT IN")

        if "LIKE '%'" in query_upper:
            suggestions.append("Leading wildcard in LIKE prevents index usage")

        if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
            suggestions.append("Consider adding LIMIT when using ORDER BY")

        if query_upper.count("JOIN") > 3:
            suggestions.append("Multiple JOINs detected, consider denormalization")

        if "WHERE" not in query_upper and "SELECT" in query_upper:
            suggestions.append("No WHERE clause - ensure this is intentional")

        return suggestions

    # Resource cleanup
    async def cleanup(self):
        """Clean up resources"""
        # Redis cleanup if available
        # if self.redis_cache:
        #     self.redis_cache.close()
        #     await self.redis_cache.wait_closed()

        if self.db_pool:
            for conn in self.db_pool:
                await conn.close()

        self.executor.shutdown(wait=True)

    # Performance report generation
    async def generate_performance_report(self, duration_minutes: int = 60) -> Dict:
        """Generate comprehensive performance report"""
        start_time = time.time() - (duration_minutes * 60)

        conn = await aiosqlite.connect(self.db_path)

        # Get metrics summary
        cursor = await conn.execute("""
            SELECT metric_type, AVG(value) as avg_value,
                   MIN(value) as min_value, MAX(value) as max_value
            FROM performance_metrics
            WHERE timestamp > ?
            GROUP BY metric_type
        """, (start_time,))

        metrics_summary = {}
        async for row in cursor:
            metrics_summary[row[0]] = {
                "average": row[1],
                "minimum": row[2],
                "maximum": row[3]
            }

        # Get slow queries
        slow_queries = await self.analyze_slow_queries()

        # Get cache statistics
        cursor = await conn.execute("""
            SELECT AVG(hit_rate), SUM(hits), SUM(misses)
            FROM cache_stats
            WHERE timestamp > ?
        """, (start_time,))

        cache_stats = await cursor.fetchone()

        await conn.close()

        return {
            "report_time": datetime.utcnow().isoformat(),
            "duration_minutes": duration_minutes,
            "metrics": metrics_summary,
            "cache_performance": {
                "average_hit_rate": cache_stats[0] if cache_stats and cache_stats[0] else 0,
                "total_hits": cache_stats[1] if cache_stats and len(cache_stats) > 1 and cache_stats[1] else 0,
                "total_misses": cache_stats[2] if cache_stats and len(cache_stats) > 2 and cache_stats[2] else 0
            },
            "slow_queries": slow_queries[:5],  # Top 5 slow queries
            "recommendations": self._get_performance_recommendations(metrics_summary)
        }

    def _get_performance_recommendations(self, metrics: Dict) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []

        # Check response times
        if metrics.get("response_time_p99", {}).get("average", 0) > 1.0:
            recommendations.append("P99 response time exceeds 1 second - investigate slow endpoints")

        # Check cache hit rate
        if metrics.get("cache_hit_rate", {}).get("average", 0) < 0.8:
            recommendations.append("Cache hit rate below 80% - consider increasing cache TTL")

        # Check CPU usage
        if metrics.get("cpu_usage", {}).get("average", 0) > 70:
            recommendations.append("High CPU usage detected - consider horizontal scaling")

        # Check memory usage
        if metrics.get("memory_usage", {}).get("average", 0) > 80:
            recommendations.append("High memory usage - investigate memory leaks or increase RAM")

        # Check database query times
        if metrics.get("db_query_time", {}).get("average", 0) > 0.05:
            recommendations.append("Database queries averaging >50ms - review slow query log")

        return recommendations


# Performance testing utilities
class LoadTester:
    """Load testing utilities for MCP server"""

    def __init__(self, target_url: str = "http://localhost:8099"):
        self.target_url = target_url

    async def run_load_test(self, num_requests: int = 1000,
                           concurrent_users: int = 10) -> Dict:
        """Run load test against MCP server"""
        start_time = time.time()
        results = {"success": 0, "failure": 0, "response_times": []}

        # Create request batches
        batch_size = num_requests // concurrent_users
        batches = []

        for _ in range(concurrent_users):
            batch = [self._make_request() for _ in range(batch_size)]
            batches.append(batch)

        # Execute batches concurrently
        tasks = [self._execute_batch(batch, results) for batch in batches]
        await asyncio.gather(*tasks)

        # Calculate statistics
        total_time = time.time() - start_time
        avg_response_time = statistics.mean(results["response_times"]) if results["response_times"] else 0

        return {
            "total_requests": num_requests,
            "concurrent_users": concurrent_users,
            "total_time": total_time,
            "requests_per_second": num_requests / total_time,
            "success_count": results["success"],
            "failure_count": results["failure"],
            "average_response_time": avg_response_time,
            "p95_response_time": sorted(results["response_times"])[int(len(results["response_times"]) * 0.95)] if results["response_times"] else 0,
            "p99_response_time": sorted(results["response_times"])[int(len(results["response_times"]) * 0.99)] if results["response_times"] else 0
        }

    async def _make_request(self) -> Dict:
        """Make a single request"""
        import aiohttp

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.target_url}/jsonrpc",
                                       json=payload,
                                       timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    await resp.json()
                    return {
                        "status": "success",
                        "response_time": time.time() - start
                    }
        except Exception as e:
            return {
                "status": "failure",
                "response_time": time.time() - start,
                "error": str(e)
            }

    async def _execute_batch(self, batch: List, results: Dict):
        """Execute a batch of requests"""
        for coro in batch:
            result = await coro
            if result["status"] == "success":
                results["success"] += 1
            else:
                results["failure"] += 1
            results["response_times"].append(result["response_time"])


# Test performance features
if __name__ == "__main__":
    async def main():
        # Initialize performance module
        perf = MCPPerformance()
        await perf.initialize()

        print("\n=== Performance Optimization Tests ===")

        # Test caching
        print("\n1. Testing Cache Performance")

        @perf.cache_result(ttl=60)
        async def expensive_operation(n: int) -> int:
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return n * n

        # First call (cache miss)
        start = time.time()
        result1 = await expensive_operation(5)
        time1 = time.time() - start
        print(f"First call (cache miss): {result1}, Time: {time1:.3f}s")

        # Second call (cache hit)
        start = time.time()
        result2 = await expensive_operation(5)
        time2 = time.time() - start
        print(f"Second call (cache hit): {result2}, Time: {time2:.3f}s")
        print(f"Speed improvement: {time1/time2:.1f}x faster")

        # Test batch processing
        print("\n2. Testing Batch Processing")
        requests = [{"id": i, "data": f"request_{i}"} for i in range(100)]

        start = time.time()
        results = await perf.batch_requests(requests, batch_size=10)
        batch_time = time.time() - start
        print(f"Processed {len(requests)} requests in {batch_time:.2f}s")
        print(f"Throughput: {len(requests)/batch_time:.0f} req/s")

        # Collect metrics
        print("\n3. Collecting Performance Metrics")
        metrics = await perf.collect_metrics()
        print(f"CPU Usage: {metrics.cpu_usage:.1f}%")
        print(f"Memory Usage: {metrics.memory_usage:.1f}%")
        print(f"Cache Hit Rate: {metrics.cache_hit_rate:.2%}")
        print(f"Avg Response Time: {metrics.avg_response_time:.3f}s")

        # Analyze slow queries
        print("\n4. Analyzing Slow Queries")
        slow_queries = await perf.analyze_slow_queries(threshold=0.001)
        for query in slow_queries[:3]:
            print(f"- Query: {query['query'][:50]}...")
            print(f"  Avg Time: {query['avg_time']:.3f}s")
            if query['suggestions']:
                print(f"  Suggestions: {', '.join(query['suggestions'][:2])}")

        # Generate performance report
        print("\n5. Generating Performance Report")
        report = await perf.generate_performance_report(duration_minutes=5)
        print(f"Report generated for last {report['duration_minutes']} minutes")
        print(f"Recommendations:")
        for rec in report['recommendations'][:3]:
            print(f"- {rec}")

        # Run load test
        print("\n6. Running Load Test")
        tester = LoadTester()
        load_results = await tester.run_load_test(
            num_requests=100,
            concurrent_users=5
        )
        print(f"Total Requests: {load_results['total_requests']}")
        print(f"Requests/sec: {load_results['requests_per_second']:.0f}")
        print(f"Success Rate: {(load_results['success_count']/load_results['total_requests']*100):.1f}%")
        print(f"Avg Response: {load_results['average_response_time']:.3f}s")
        print(f"P95 Response: {load_results['p95_response_time']:.3f}s")
        print(f"P99 Response: {load_results['p99_response_time']:.3f}s")

        # Cleanup
        await perf.cleanup()

    asyncio.run(main())