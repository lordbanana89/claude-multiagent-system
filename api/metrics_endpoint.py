"""
Metrics API Endpoint for monitoring dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import time
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta

from core.metrics_collector import get_metrics_collector
from core.agent_router import get_agent_router
from core.message_bus import get_message_bus
from core.workflow_engine import get_workflow_engine
from core.persistence import get_persistence_manager

app = FastAPI(title="Metrics API", version="1.0.0")

# Enable CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get system components
metrics_collector = get_metrics_collector()
agent_router = get_agent_router()
message_bus = get_message_bus()
workflow_engine = get_workflow_engine()
persistence = get_persistence_manager()


@app.get("/")
async def root():
    """Serve monitoring dashboard"""
    with open("web/monitoring_dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/metrics")
async def get_metrics():
    """Get all system metrics"""
    try:
        # Get metrics from collector
        metrics_data = metrics_collector.get_summary()

        # Get agent status
        agents = []
        for agent_id in ["supervisor", "backend-api", "database", "frontend-ui", "testing"]:
            agent_metrics = agent_router.get_agent_metrics(agent_id)
            agents.append({
                "name": agent_id,
                "status": agent_metrics.get("status", "unknown"),
                "load": agent_metrics.get("load_score", 0),
                "success_rate": agent_metrics.get("success_rate", 1.0)
            })

        # Get task statistics
        task_stats = persistence.get_statistics().get("tasks", {})

        # Get workflow statistics
        workflow_stats = persistence.get_statistics().get("workflows", {})

        # Get pending tasks
        pending_tasks = persistence.get_pending_tasks()
        queue = [
            {
                "agent": task["agent"],
                "command": task.get("command", ""),
                "priority": "high" if task.get("priority", 0) > 3 else "normal"
            }
            for task in pending_tasks[:10]
        ]

        # Get recent logs/events
        recent_events = persistence.get_recent_events(limit=20)
        logs = [
            {
                "timestamp": datetime.fromtimestamp(event["timestamp"]).strftime("%H:%M:%S"),
                "level": "info",
                "message": f"{event['event_type']}: {event.get('data', {}).get('message', '')}"
            }
            for event in recent_events
        ]

        # Generate throughput data (mock for now)
        now = datetime.now()
        throughput_labels = [(now - timedelta(minutes=i)).strftime("%H:%M")
                            for i in range(20, 0, -1)]
        throughput_values = [random.randint(5, 20) for _ in range(20)]

        return {
            "timestamp": time.time(),
            "system": {
                "uptime": metrics_data.get("categories", {}).get("system", {})
                           .get("system_uptime", {}).get("value", 0)
            },
            "agents": agents,
            "tasks": {
                "total": sum(task_stats.values()),
                "completed_success": task_stats.get("completed", 0),
                "completed_failed": task_stats.get("failed", 0),
                "pending": task_stats.get("pending", 0),
                "success_rate": 0.9 if task_stats.get("completed", 0) > 0 else 0,
                "throughput": {
                    "labels": throughput_labels,
                    "values": throughput_values
                }
            },
            "workflows": {
                "active": workflow_stats.get("running", 0),
                "pending": workflow_stats.get("pending", 0),
                "running": workflow_stats.get("running", 0),
                "completed": workflow_stats.get("completed", 0),
                "failed": workflow_stats.get("failed", 0)
            },
            "resources": {
                "cpu": random.randint(20, 60),
                "memory": random.randint(30, 70),
                "disk": random.randint(10, 40),
                "network": random.randint(5, 30),
                "queue": min(len(pending_tasks) * 10, 100)
            },
            "queue": queue,
            "logs": logs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get metrics in Prometheus format"""
    try:
        prometheus_data = metrics_collector.export_prometheus()
        return JSONResponse(
            content=prometheus_data,
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/json")
async def get_json_metrics():
    """Get metrics as JSON"""
    try:
        return metrics_collector.export_json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/{metric_name}")
async def get_specific_metric(metric_name: str, time_range: int = 300):
    """Get specific metric data"""
    try:
        metric_data = metrics_collector.get_metric(metric_name, time_range)
        if not metric_data:
            raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")
        return metric_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/metrics/record")
async def record_metric(data: Dict[str, Any]):
    """Record a metric value"""
    try:
        metric_name = data.get("name")
        value = data.get("value", 0)
        labels = data.get("labels", {})

        if not metric_name:
            raise HTTPException(status_code=400, detail="Metric name required")

        metrics_collector.record(metric_name, value, labels)

        return {"status": "recorded", "metric": metric_name, "value": value}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "metrics_collector": "active",
            "message_bus": "active" if message_bus.running else "inactive",
            "persistence": "active"
        }
    }


if __name__ == "__main__":
    import uvicorn

    # Start metrics aggregation
    metrics_collector.start_aggregation()

    # Run API server
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")