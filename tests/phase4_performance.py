#!/usr/bin/env python3
"""
Phase 4: Performance Benchmarking
"""

import time
import requests
import sqlite3
import statistics

def benchmark_mcp_server():
    """Benchmark MCP server response times"""
    print("\n[PERF] 1. MCP Server Response Time:")

    url = "http://localhost:9999/jsonrpc"
    times = []

    for i in range(20):
        start = time.time()
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "heartbeat",
                    "arguments": {"agent": f"perf_test_{i}"}
                },
                "id": i
            }
            response = requests.post(url, json=payload, timeout=5)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
        except:
            pass

    if times:
        print(f"  Average: {statistics.mean(times):.2f}ms")
        print(f"  Median: {statistics.median(times):.2f}ms")
        print(f"  Min: {min(times):.2f}ms")
        print(f"  Max: {max(times):.2f}ms")

        if statistics.mean(times) < 50:
            print("  ✅ EXCELLENT performance")
        elif statistics.mean(times) < 100:
            print("  ✅ GOOD performance")
        else:
            print("  ⚠️ SLOW performance")

    return times

def benchmark_auth_api():
    """Benchmark Auth API response times"""
    print("\n[PERF] 2. Auth API Response Time:")

    url = "http://localhost:5002/api/auth/login"
    times = []

    for i in range(20):
        start = time.time()
        try:
            payload = {"username": f"test_{i}", "password": "test"}
            response = requests.post(url, json=payload, timeout=5)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
        except:
            pass

    if times:
        print(f"  Average: {statistics.mean(times):.2f}ms")
        print(f"  Median: {statistics.median(times):.2f}ms")
        print(f"  Min: {min(times):.2f}ms")
        print(f"  Max: {max(times):.2f}ms")

        if statistics.mean(times) < 50:
            print("  ✅ EXCELLENT performance")
        elif statistics.mean(times) < 100:
            print("  ✅ GOOD performance")
        else:
            print("  ⚠️ SLOW performance")

    return times

def benchmark_database():
    """Benchmark database query performance"""
    print("\n[PERF] 3. Database Query Performance:")

    times = []

    for i in range(20):
        start = time.time()
        try:
            conn = sqlite3.connect("mcp_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM agents")
            cursor.execute("SELECT COUNT(*) FROM activity_logs")
            cursor.execute("SELECT * FROM agents WHERE id = 'testing'")
            conn.close()
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
        except:
            pass

    if times:
        print(f"  Average: {statistics.mean(times):.2f}ms")
        print(f"  Median: {statistics.median(times):.2f}ms")
        print(f"  Min: {min(times):.2f}ms")
        print(f"  Max: {max(times):.2f}ms")

        if statistics.mean(times) < 10:
            print("  ✅ EXCELLENT performance")
        elif statistics.mean(times) < 50:
            print("  ✅ GOOD performance")
        else:
            print("  ⚠️ SLOW performance")

    return times

def calculate_throughput():
    """Calculate system throughput"""
    print("\n[PERF] 4. Throughput Analysis:")

    # Test MCP throughput
    url = "http://localhost:9999/jsonrpc"
    start = time.time()
    successful = 0

    for i in range(100):
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "heartbeat",
                    "arguments": {"agent": "throughput_test"}
                },
                "id": i
            }
            response = requests.post(url, json=payload, timeout=1)
            if response.status_code == 200:
                successful += 1
        except:
            pass

    duration = time.time() - start
    throughput = successful / duration

    print(f"  MCP Requests/sec: {throughput:.2f}")
    print(f"  Success rate: {successful}/100 ({successful}%)")

    if throughput > 50:
        print("  ✅ EXCELLENT throughput")
    elif throughput > 20:
        print("  ✅ GOOD throughput")
    else:
        print("  ⚠️ LOW throughput")

if __name__ == "__main__":
    print("==================================================")
    print("PHASE 4: PERFORMANCE BENCHMARKS")
    print("==================================================")

    mcp_times = benchmark_mcp_server()
    auth_times = benchmark_auth_api()
    db_times = benchmark_database()
    calculate_throughput()

    print("\n==================================================")
    print("PERFORMANCE SUMMARY")
    print("==================================================")

    if mcp_times:
        print(f"MCP Server: {statistics.mean(mcp_times):.2f}ms avg")
    if auth_times:
        print(f"Auth API: {statistics.mean(auth_times):.2f}ms avg")
    if db_times:
        print(f"Database: {statistics.mean(db_times):.2f}ms avg")

    print("\n✅ Performance Benchmarks Complete")