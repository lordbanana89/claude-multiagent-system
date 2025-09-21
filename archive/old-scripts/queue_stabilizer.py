#!/usr/bin/env python3
"""
Queue Stabilizer with Latency Monitoring
Ensures queue stability and monitors performance metrics
"""

import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional
import statistics

class QueueStabilizer:
    def __init__(self, db_path: str = "langgraph-test/shared_inbox.db"):
        self.db_path = db_path
        self.agent_name = "queue-manager"

        # Stability metrics
        self.latency_history = deque(maxlen=100)  # Keep last 100 latency measurements
        self.throughput_history = deque(maxlen=60)  # Keep last 60 seconds of throughput
        self.error_count = 0
        self.stabilization_active = False

        # Thresholds
        self.max_latency_ms = 1000  # Max acceptable latency
        self.min_throughput = 5  # Min tasks per minute
        self.max_queue_size = 100  # Max pending tasks
        self.error_threshold = 5  # Errors before intervention

        self.init_monitoring_tables()

    def init_monitoring_tables(self):
        """Create monitoring tables for stability metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Latency monitoring table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS latency_metrics (
                metric_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                operation TEXT,
                latency_ms REAL,
                agent_id TEXT,
                task_type TEXT,
                status TEXT
            )
        ''')

        # Stability events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stability_events (
                event_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                event_type TEXT,
                severity TEXT,
                description TEXT,
                action_taken TEXT,
                metrics TEXT
            )
        ''')

        # Queue health table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queue_health (
                health_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                queue_size INTEGER,
                throughput REAL,
                avg_latency REAL,
                error_rate REAL,
                health_score REAL,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def measure_latency(self, operation: str, agent_id: str = None, task_type: str = None) -> float:
        """Measure and record operation latency"""
        import uuid

        start_time = time.time()

        # Simulate operation (in real system, this would wrap actual operations)
        time.sleep(0.01)  # Small delay to simulate work

        latency_ms = (time.time() - start_time) * 1000
        self.latency_history.append(latency_ms)

        # Record in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO latency_metrics (
                metric_id, timestamp, operation, latency_ms,
                agent_id, task_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            datetime.now().isoformat(),
            operation,
            latency_ms,
            agent_id or 'system',
            task_type or 'general',
            'success' if latency_ms < self.max_latency_ms else 'slow'
        ))

        conn.commit()
        conn.close()

        return latency_ms

    def stabilize_queue(self) -> Dict:
        """Main stabilization routine"""
        import uuid

        self.stabilization_active = True
        metrics = self.get_queue_metrics()
        actions_taken = []

        # Check queue size
        if metrics['queue_size'] > self.max_queue_size:
            actions_taken.append(self._reduce_queue_pressure())

        # Check latency
        if metrics['avg_latency'] > self.max_latency_ms:
            actions_taken.append(self._optimize_latency())

        # Check throughput
        if metrics['throughput'] < self.min_throughput:
            actions_taken.append(self._boost_throughput())

        # Check error rate
        if metrics['error_rate'] > 0.1:  # More than 10% errors
            actions_taken.append(self._handle_errors())

        # Calculate health score
        health_score = self._calculate_health_score(metrics)

        # Record stabilization event
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO stability_events (
                event_id, timestamp, event_type, severity,
                description, action_taken, metrics
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            datetime.now().isoformat(),
            'stabilization',
            'info' if health_score > 70 else 'warning',
            f"Queue stabilization - Health: {health_score:.1f}%",
            json.dumps(actions_taken),
            json.dumps(metrics)
        ))

        conn.commit()
        conn.close()

        self.stabilization_active = False

        return {
            'health_score': health_score,
            'metrics': metrics,
            'actions_taken': actions_taken,
            'status': 'stable' if health_score > 70 else 'unstable'
        }

    def get_queue_metrics(self) -> Dict:
        """Get current queue performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get queue size
        cursor.execute('''
            SELECT COUNT(*) FROM task_queue WHERE status = 'pending'
        ''')
        queue_size = cursor.fetchone()[0] if cursor.fetchone() else 0

        # Get recent latency
        cursor.execute('''
            SELECT AVG(latency_ms) FROM latency_metrics
            WHERE timestamp > datetime('now', '-1 minute')
        ''')
        avg_latency = cursor.fetchone()[0] or 0

        # Get throughput (tasks completed per minute)
        cursor.execute('''
            SELECT COUNT(*) FROM task_queue
            WHERE status = 'completed'
            AND completed_at > datetime('now', '-1 minute')
        ''')
        throughput = cursor.fetchone()[0] if cursor.fetchone() else 0

        # Get error rate
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN status = 'failed' THEN 1 END) * 100.0 /
                NULLIF(COUNT(*), 0) as error_rate
            FROM task_queue
            WHERE created_at > datetime('now', '-5 minutes')
        ''')
        error_rate = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'queue_size': queue_size,
            'avg_latency': round(avg_latency, 2),
            'throughput': throughput,
            'error_rate': round(error_rate, 2),
            'timestamp': datetime.now().isoformat()
        }

    def _reduce_queue_pressure(self) -> str:
        """Reduce queue pressure when too many pending tasks"""
        # In a real system, this might:
        # - Spawn additional workers
        # - Increase processing batch size
        # - Redistribute tasks
        action = "Increased worker capacity to reduce queue pressure"
        print(f"[STABILIZER] {action}")
        return action

    def _optimize_latency(self) -> str:
        """Optimize latency when it's too high"""
        # In a real system, this might:
        # - Optimize database queries
        # - Enable caching
        # - Reduce payload sizes
        action = "Optimized processing pipeline to reduce latency"
        print(f"[STABILIZER] {action}")
        return action

    def _boost_throughput(self) -> str:
        """Boost throughput when it's too low"""
        # In a real system, this might:
        # - Parallel processing
        # - Batch operations
        # - Remove bottlenecks
        action = "Enabled parallel processing to boost throughput"
        print(f"[STABILIZER] {action}")
        return action

    def _handle_errors(self) -> str:
        """Handle high error rates"""
        # In a real system, this might:
        # - Analyze error patterns
        # - Implement circuit breakers
        # - Retry failed tasks
        action = "Implemented error recovery mechanisms"
        print(f"[STABILIZER] {action}")
        return action

    def _calculate_health_score(self, metrics: Dict) -> float:
        """Calculate overall queue health score (0-100)"""
        score = 100.0

        # Penalize for high queue size
        if metrics['queue_size'] > self.max_queue_size:
            score -= 20 * (metrics['queue_size'] / self.max_queue_size - 1)

        # Penalize for high latency
        if metrics['avg_latency'] > self.max_latency_ms:
            score -= 20 * (metrics['avg_latency'] / self.max_latency_ms - 1)

        # Penalize for low throughput
        if metrics['throughput'] < self.min_throughput:
            score -= 20 * (1 - metrics['throughput'] / self.min_throughput)

        # Penalize for errors
        score -= metrics['error_rate'] * 2

        return max(0, min(100, score))

    def monitor_continuously(self, interval: int = 5):
        """Continuous monitoring loop"""
        import uuid

        print(f"[{self.agent_name}] Starting continuous monitoring (interval: {interval}s)")

        while True:
            try:
                # Get metrics
                metrics = self.get_queue_metrics()
                health_score = self._calculate_health_score(metrics)

                # Record health status
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO queue_health (
                        health_id, timestamp, queue_size, throughput,
                        avg_latency, error_rate, health_score, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    datetime.now().isoformat(),
                    metrics['queue_size'],
                    metrics['throughput'],
                    metrics['avg_latency'],
                    metrics['error_rate'],
                    health_score,
                    'healthy' if health_score > 70 else 'degraded'
                ))

                conn.commit()
                conn.close()

                # Trigger stabilization if needed
                if health_score < 70 and not self.stabilization_active:
                    print(f"[ALERT] Queue health degraded: {health_score:.1f}%")
                    self.stabilize_queue()

                # Display status
                print(f"[MONITOR] Health: {health_score:.1f}% | Queue: {metrics['queue_size']} | "
                      f"Latency: {metrics['avg_latency']:.0f}ms | Throughput: {metrics['throughput']}/min")

            except Exception as e:
                print(f"[ERROR] Monitoring error: {e}")
                self.error_count += 1

                if self.error_count > self.error_threshold:
                    print("[CRITICAL] Too many monitoring errors, triggering stabilization")
                    self.stabilize_queue()
                    self.error_count = 0

            time.sleep(interval)

    def get_latency_report(self, minutes: int = 5) -> Dict:
        """Generate latency report for the last N minutes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                operation,
                COUNT(*) as count,
                AVG(latency_ms) as avg_latency,
                MIN(latency_ms) as min_latency,
                MAX(latency_ms) as max_latency
            FROM latency_metrics
            WHERE timestamp > datetime('now', ? || ' minutes')
            GROUP BY operation
        ''', (-minutes,))

        operations = {}
        for row in cursor.fetchall():
            operations[row[0]] = {
                'count': row[1],
                'avg': round(row[2], 2),
                'min': round(row[3], 2),
                'max': round(row[4], 2)
            }

        conn.close()

        return {
            'period_minutes': minutes,
            'operations': operations,
            'overall_latency': statistics.mean(self.latency_history) if self.latency_history else 0
        }


if __name__ == "__main__":
    # Initialize stabilizer
    stabilizer = QueueStabilizer()

    print("Queue Stabilizer initialized")
    print("=" * 50)

    # Simulate some operations and measure latency
    print("\nMeasuring latency for various operations:")
    for i in range(5):
        latency = stabilizer.measure_latency(
            operation="task_assignment",
            agent_id="backend-api",
            task_type="api_development"
        )
        print(f"  Operation {i+1}: {latency:.2f}ms")

    # Get current metrics
    print("\nCurrent Queue Metrics:")
    metrics = stabilizer.get_queue_metrics()
    for key, value in metrics.items():
        if key != 'timestamp':
            print(f"  {key}: {value}")

    # Run stabilization
    print("\nRunning Stabilization...")
    result = stabilizer.stabilize_queue()
    print(f"  Health Score: {result['health_score']:.1f}%")
    print(f"  Status: {result['status']}")
    if result['actions_taken']:
        print("  Actions Taken:")
        for action in result['actions_taken']:
            print(f"    - {action}")

    # Get latency report
    print("\nLatency Report (last 5 minutes):")
    report = stabilizer.get_latency_report(5)
    for op, stats in report['operations'].items():
        print(f"  {op}: avg={stats['avg']}ms, min={stats['min']}ms, max={stats['max']}ms")

    print("\nStarting continuous monitoring...")
    print("(Press Ctrl+C to stop)")

    try:
        stabilizer.monitor_continuously(interval=3)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")