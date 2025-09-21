#!/usr/bin/env python3
"""
Collect baseline metrics for MCP system before migration
"""

import json
import time
import psutil
import requests
import sqlite3
from datetime import datetime
from statistics import mean, median

def collect_api_metrics():
    """Measure API response times"""
    url = "http://localhost:8099/api/mcp/status"
    response_times = []

    print("Collecting API response times...")
    for i in range(10):
        start = time.time()
        try:
            response = requests.get(url)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            response_times.append(elapsed)
            print(f"  Request {i+1}: {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Request {i+1} failed: {e}")
        time.sleep(1)

    return {
        "endpoint": "/api/mcp/status",
        "samples": len(response_times),
        "avg_response_ms": mean(response_times) if response_times else 0,
        "median_response_ms": median(response_times) if response_times else 0,
        "min_response_ms": min(response_times) if response_times else 0,
        "max_response_ms": max(response_times) if response_times else 0
    }

def collect_database_metrics():
    """Measure database query performance"""
    db_path = "/tmp/mcp_state.db"
    query_times = []

    print("\nCollecting database query times...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test query performance
        for i in range(10):
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM activities")
            cursor.fetchone()
            elapsed = (time.time() - start) * 1000
            query_times.append(elapsed)
            print(f"  Query {i+1}: {elapsed:.2f}ms")
            time.sleep(0.1)

        # Get table sizes
        cursor.execute("SELECT COUNT(*) FROM activities")
        activities_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agent_states")
        agent_states_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM components")
        components_count = cursor.fetchone()[0]

        conn.close()

        return {
            "query_type": "SELECT COUNT(*) FROM activities",
            "samples": len(query_times),
            "avg_query_ms": mean(query_times),
            "median_query_ms": median(query_times),
            "table_sizes": {
                "activities": activities_count,
                "agent_states": agent_states_count,
                "components": components_count
            }
        }
    except Exception as e:
        print(f"  Database metrics failed: {e}")
        return {"error": str(e)}

def collect_process_metrics():
    """Measure process resource usage"""
    print("\nCollecting process metrics...")

    # Find MCP processes
    mcp_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'mcp' in cmdline.lower() and 'python' in cmdline.lower():
                proc_info = proc.as_dict(attrs=['pid', 'name', 'memory_info', 'cpu_percent'])
                proc_info['cmdline'] = cmdline[:100]  # Truncate long command lines
                mcp_processes.append(proc_info)
                print(f"  Found process: PID {proc_info['pid']} - {proc_info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Calculate totals
    total_memory_mb = sum(p['memory_info'].rss / 1024 / 1024 for p in mcp_processes)
    total_cpu = sum(p['cpu_percent'] for p in mcp_processes)

    return {
        "process_count": len(mcp_processes),
        "total_memory_mb": round(total_memory_mb, 2),
        "total_cpu_percent": round(total_cpu, 2),
        "processes": [
            {
                "pid": p['pid'],
                "name": p['name'],
                "memory_mb": round(p['memory_info'].rss / 1024 / 1024, 2),
                "cpu_percent": p['cpu_percent']
            }
            for p in mcp_processes
        ]
    }

def collect_system_metrics():
    """Collect overall system metrics"""
    print("\nCollecting system metrics...")

    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/tmp')

    print(f"  CPU Usage: {cpu_percent}%")
    print(f"  Memory Usage: {memory.percent}%")
    print(f"  Disk Usage (/tmp): {disk.percent}%")

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
        "disk_usage_percent": disk.percent,
        "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
    }

def main():
    print("=" * 50)
    print("MCP System Baseline Metrics Collection")
    print("=" * 50)

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "api_metrics": collect_api_metrics(),
        "database_metrics": collect_database_metrics(),
        "process_metrics": collect_process_metrics(),
        "system_metrics": collect_system_metrics()
    }

    # Save to file
    output_file = "baseline_metrics.json"
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "=" * 50)
    print(f"Baseline metrics saved to {output_file}")
    print("=" * 50)

    # Display summary
    print("\nSummary:")
    print(f"  API Avg Response: {metrics['api_metrics'].get('avg_response_ms', 0):.2f}ms")
    print(f"  DB Avg Query: {metrics['database_metrics'].get('avg_query_ms', 0):.2f}ms")
    print(f"  MCP Processes: {metrics['process_metrics']['process_count']}")
    print(f"  Total Memory: {metrics['process_metrics']['total_memory_mb']}MB")
    print(f"  System CPU: {metrics['system_metrics']['cpu_percent']}%")

if __name__ == "__main__":
    main()