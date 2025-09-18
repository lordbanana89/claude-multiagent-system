"""
Real-time Metrics Collection and Monitoring System
"""

import time
import json
import threading
from typing import Dict, List, Optional, Any, Deque
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"      # Cumulative count
    GAUGE = "gauge"          # Current value
    HISTOGRAM = "histogram"  # Distribution of values
    RATE = "rate"           # Rate per second
    SUMMARY = "summary"      # Statistical summary


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Metric definition and data"""
    name: str
    type: MetricType
    description: str
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    points: Deque[MetricPoint] = field(default_factory=lambda: deque(maxlen=10000))

    def add_point(self, value: float, labels: Dict[str, str] = None):
        """Add data point to metric"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)


class MetricsCollector:
    """Collects and aggregates system metrics"""

    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
        self._aggregation_thread = None
        self._running = False

        # Initialize core metrics
        self._initialize_metrics()

        logger.info("MetricsCollector initialized")

    def _initialize_metrics(self):
        """Initialize core system metrics"""
        # Task metrics
        self.register_metric("tasks_submitted", MetricType.COUNTER,
                           "Total tasks submitted", "count", ["agent", "priority"])
        self.register_metric("tasks_completed", MetricType.COUNTER,
                           "Total tasks completed", "count", ["agent", "status"])
        self.register_metric("tasks_pending", MetricType.GAUGE,
                           "Current pending tasks", "count", ["agent"])
        self.register_metric("task_duration", MetricType.HISTOGRAM,
                           "Task execution duration", "seconds", ["agent", "type"])
        self.register_metric("task_success_rate", MetricType.RATE,
                           "Task success rate", "per_second", ["agent"])

        # Agent metrics
        self.register_metric("agent_load", MetricType.GAUGE,
                           "Agent current load", "percent", ["agent"])
        self.register_metric("agent_memory", MetricType.GAUGE,
                           "Agent memory usage", "bytes", ["agent"])
        self.register_metric("agent_cpu", MetricType.GAUGE,
                           "Agent CPU usage", "percent", ["agent"])
        self.register_metric("agent_heartbeats", MetricType.COUNTER,
                           "Agent heartbeat count", "count", ["agent"])
        self.register_metric("agent_errors", MetricType.COUNTER,
                           "Agent error count", "count", ["agent", "error_type"])

        # Workflow metrics
        self.register_metric("workflows_started", MetricType.COUNTER,
                           "Total workflows started", "count", ["workflow_type"])
        self.register_metric("workflows_completed", MetricType.COUNTER,
                           "Total workflows completed", "count", ["workflow_type", "status"])
        self.register_metric("workflow_duration", MetricType.HISTOGRAM,
                           "Workflow execution duration", "seconds", ["workflow_type"])
        self.register_metric("workflow_steps_completed", MetricType.COUNTER,
                           "Workflow steps completed", "count", ["workflow_type", "step"])

        # Message bus metrics
        self.register_metric("messages_sent", MetricType.COUNTER,
                           "Total messages sent", "count", ["source", "target", "type"])
        self.register_metric("messages_received", MetricType.COUNTER,
                           "Total messages received", "count", ["agent", "type"])
        self.register_metric("message_latency", MetricType.HISTOGRAM,
                           "Message delivery latency", "milliseconds", ["source", "target"])
        self.register_metric("message_queue_size", MetricType.GAUGE,
                           "Message queue size", "count", ["agent"])

        # System metrics
        self.register_metric("system_uptime", MetricType.GAUGE,
                           "System uptime", "seconds")
        self.register_metric("redis_connections", MetricType.GAUGE,
                           "Active Redis connections", "count")
        self.register_metric("database_queries", MetricType.COUNTER,
                           "Database queries executed", "count", ["query_type"])
        self.register_metric("api_requests", MetricType.COUNTER,
                           "API requests received", "count", ["method", "endpoint", "status"])
        self.register_metric("api_response_time", MetricType.HISTOGRAM,
                           "API response time", "milliseconds", ["method", "endpoint"])

        # Coordination metrics
        self.register_metric("coordinations_initiated", MetricType.COUNTER,
                           "Coordination tasks initiated", "count", ["type"])
        self.register_metric("consensus_reached", MetricType.COUNTER,
                           "Consensus agreements reached", "count")
        self.register_metric("negotiations_completed", MetricType.COUNTER,
                           "Negotiations completed", "count", ["outcome"])
        self.register_metric("votes_cast", MetricType.COUNTER,
                           "Votes cast in decisions", "count", ["topic"])

    def register_metric(self, name: str, type: MetricType,
                       description: str, unit: str = "", labels: List[str] = None):
        """Register a new metric"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = Metric(
                    name=name,
                    type=type,
                    description=description,
                    unit=unit,
                    labels=labels or []
                )
                logger.debug(f"Registered metric: {name}")

    def record(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value"""
        with self._lock:
            if metric_name in self.metrics:
                metric = self.metrics[metric_name]

                if metric.type == MetricType.COUNTER:
                    # For counters, add to existing value
                    last_value = metric.points[-1].value if metric.points else 0
                    metric.add_point(last_value + value, labels)
                else:
                    metric.add_point(value, labels)
            else:
                logger.warning(f"Unknown metric: {metric_name}")

    def increment(self, metric_name: str, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        self.record(metric_name, 1, labels)

    def set_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        self.record(metric_name, value, labels)

    def observe(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Observe a value for histogram/summary"""
        self.record(metric_name, value, labels)

    def get_metric(self, name: str, time_range: int = 300) -> Optional[Dict]:
        """Get metric data for time range (seconds)"""
        with self._lock:
            if name not in self.metrics:
                return None

            metric = self.metrics[name]
            cutoff = time.time() - time_range

            # Filter points within time range
            points = [p for p in metric.points if p.timestamp >= cutoff]

            if not points:
                return {
                    'name': name,
                    'type': metric.type.value,
                    'description': metric.description,
                    'unit': metric.unit,
                    'data': []
                }

            # Calculate statistics based on type
            values = [p.value for p in points]

            stats = {}
            if metric.type == MetricType.COUNTER:
                stats['total'] = values[-1] if values else 0
                stats['rate'] = (values[-1] - values[0]) / time_range if len(values) > 1 else 0

            elif metric.type == MetricType.GAUGE:
                stats['current'] = values[-1]
                stats['min'] = min(values)
                stats['max'] = max(values)
                stats['avg'] = statistics.mean(values)

            elif metric.type in [MetricType.HISTOGRAM, MetricType.SUMMARY]:
                stats['count'] = len(values)
                stats['min'] = min(values)
                stats['max'] = max(values)
                stats['avg'] = statistics.mean(values)
                stats['median'] = statistics.median(values)
                if len(values) > 1:
                    stats['stddev'] = statistics.stdev(values)
                    stats['p95'] = self._percentile(values, 0.95)
                    stats['p99'] = self._percentile(values, 0.99)

            elif metric.type == MetricType.RATE:
                if len(values) > 1:
                    time_diff = points[-1].timestamp - points[0].timestamp
                    stats['rate'] = len(values) / time_diff if time_diff > 0 else 0
                else:
                    stats['rate'] = 0

            return {
                'name': name,
                'type': metric.type.value,
                'description': metric.description,
                'unit': metric.unit,
                'stats': stats,
                'data': [{'timestamp': p.timestamp, 'value': p.value, 'labels': p.labels}
                        for p in points[-100:]]  # Limit to last 100 points
            }

    def get_all_metrics(self, time_range: int = 300) -> Dict[str, Dict]:
        """Get all metrics for time range"""
        results = {}
        for name in self.metrics:
            metric_data = self.get_metric(name, time_range)
            if metric_data:
                results[name] = metric_data
        return results

    def get_summary(self) -> Dict:
        """Get summary of all metrics"""
        with self._lock:
            summary = {
                'timestamp': time.time(),
                'metrics_count': len(self.metrics),
                'categories': {}
            }

            # Group metrics by category
            categories = {
                'tasks': ['tasks_', 'task_'],
                'agents': ['agent_'],
                'workflows': ['workflow_', 'workflows_'],
                'messages': ['message_', 'messages_'],
                'system': ['system_', 'redis_', 'database_', 'api_'],
                'coordination': ['coordination_', 'consensus_', 'negotiation_', 'vote_']
            }

            for category, prefixes in categories.items():
                category_metrics = {}
                for name, metric in self.metrics.items():
                    if any(name.startswith(prefix) for prefix in prefixes):
                        # Get latest value
                        if metric.points:
                            latest = metric.points[-1]
                            category_metrics[name] = {
                                'value': latest.value,
                                'timestamp': latest.timestamp,
                                'type': metric.type.value
                            }
                summary['categories'][category] = category_metrics

            return summary

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        with self._lock:
            for name, metric in self.metrics.items():
                if not metric.points:
                    continue

                # Add metric help and type
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} {metric.type.value}")

                # Get latest points by label combination
                latest_by_labels = {}
                for point in metric.points:
                    label_key = json.dumps(sorted(point.labels.items()))
                    latest_by_labels[label_key] = point

                # Format each point
                for label_key, point in latest_by_labels.items():
                    labels_str = ""
                    if point.labels:
                        label_parts = [f'{k}="{v}"' for k, v in point.labels.items()]
                        labels_str = "{" + ",".join(label_parts) + "}"

                    lines.append(f"{name}{labels_str} {point.value}")

        return "\n".join(lines)

    def export_json(self) -> Dict:
        """Export metrics as JSON"""
        with self._lock:
            return {
                'timestamp': time.time(),
                'metrics': {
                    name: {
                        'type': metric.type.value,
                        'description': metric.description,
                        'unit': metric.unit,
                        'points': [
                            {
                                'timestamp': p.timestamp,
                                'value': p.value,
                                'labels': p.labels
                            }
                            for p in list(metric.points)[-100:]  # Last 100 points
                        ]
                    }
                    for name, metric in self.metrics.items()
                }
            }

    def start_aggregation(self, interval: int = 60):
        """Start metrics aggregation thread"""
        if self._running:
            return

        self._running = True
        self._aggregation_thread = threading.Thread(
            target=self._aggregate_loop,
            args=(interval,)
        )
        self._aggregation_thread.daemon = True
        self._aggregation_thread.start()
        logger.info("Metrics aggregation started")

    def stop_aggregation(self):
        """Stop metrics aggregation"""
        self._running = False
        if self._aggregation_thread:
            self._aggregation_thread.join(timeout=2)
        logger.info("Metrics aggregation stopped")

    def _aggregate_loop(self, interval: int):
        """Aggregation loop for computed metrics"""
        while self._running:
            try:
                self._compute_derived_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}")

    def _compute_derived_metrics(self):
        """Compute derived metrics from raw data"""
        # Calculate task success rate
        completed = self.get_metric("tasks_completed", 60)
        if completed and completed['stats'].get('total', 0) > 0:
            # Simple success rate calculation
            success_rate = 0.9  # Placeholder - should calculate from actual data
            self.set_gauge("task_success_rate", success_rate)

        # Calculate system uptime
        # This would normally check actual start time
        self.set_gauge("system_uptime", time.time())


# Singleton instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector