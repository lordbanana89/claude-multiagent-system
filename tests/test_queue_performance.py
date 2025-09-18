#!/usr/bin/env python3
"""
Performance test for Dramatiq queue - Tests with 1000+ messages
"""

import sys
import time
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_throughput():
    """Test message throughput"""
    from task_queue import send_agent_command, QueueClient

    print("Testing message throughput...")
    client = QueueClient()

    # Agents to target
    agents = ["supervisor", "backend-api", "database", "frontend-ui", "testing"]

    # Send messages and measure time
    start_time = time.time()
    message_ids = []

    num_messages = 1000
    print(f"Sending {num_messages} messages...")

    for i in range(num_messages):
        agent = agents[i % len(agents)]
        command = f"echo 'Performance test message {i}'"
        msg_id = send_agent_command(agent, command, task_id=f"perf_{i}")
        message_ids.append(msg_id)

        if (i + 1) % 100 == 0:
            print(f"  Sent {i + 1} messages...")

    end_time = time.time()
    duration = end_time - start_time

    throughput = num_messages / duration
    print(f"\n✅ Sent {num_messages} messages in {duration:.2f} seconds")
    print(f"📊 Throughput: {throughput:.2f} messages/second")

    return throughput, message_ids


def test_parallel_sending():
    """Test parallel message sending"""
    from task_queue import QueueClient

    print("\nTesting parallel message sending...")
    client = QueueClient()

    # Create parallel tasks
    tasks = []
    for i in range(100):
        agent = ["supervisor", "backend-api", "database"][i % 3]
        command = f"echo 'Parallel test {i}'"
        tasks.append((agent, command))

    start_time = time.time()

    # Send in parallel
    message_ids = client.create_parallel_tasks(tasks)

    end_time = time.time()
    duration = end_time - start_time

    print(f"✅ Sent {len(tasks)} parallel tasks in {duration:.2f} seconds")
    print(f"📊 Parallel throughput: {len(tasks) / duration:.2f} tasks/second")

    return len(tasks) / duration


def test_task_chains():
    """Test task chain performance"""
    from task_queue import QueueClient

    print("\nTesting task chain creation...")
    client = QueueClient()

    chain_ids = []
    num_chains = 50

    start_time = time.time()

    for i in range(num_chains):
        # Create a 5-step chain
        steps = []
        for j in range(5):
            steps.append({
                "agent_id": ["supervisor", "backend-api", "frontend-ui"][j % 3],
                "command": f"echo 'Chain {i} Step {j}'",
                "description": f"Chain {i} Step {j}",
                "delay": 0
            })

        chain_id = client.create_task_chain(steps)
        chain_ids.append(chain_id)

    end_time = time.time()
    duration = end_time - start_time

    print(f"✅ Created {num_chains} task chains in {duration:.2f} seconds")
    print(f"📊 Chain creation rate: {num_chains / duration:.2f} chains/second")

    return num_chains / duration


def test_concurrent_clients():
    """Test multiple concurrent clients"""
    from task_queue import QueueClient

    print("\nTesting concurrent clients...")

    def send_batch(client_id, num_messages):
        """Send messages from a single client"""
        client = QueueClient()
        msg_ids = []

        for i in range(num_messages):
            msg_id = client.send_command(
                "supervisor",
                f"echo 'Client {client_id} Message {i}'",
                task_id=f"concurrent_{client_id}_{i}"
            )
            msg_ids.append(msg_id)

        return msg_ids

    num_clients = 10
    messages_per_client = 100

    start_time = time.time()

    # Use thread pool for concurrent clients
    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        futures = []
        for client_id in range(num_clients):
            future = executor.submit(send_batch, client_id, messages_per_client)
            futures.append(future)

        # Wait for all to complete
        results = [f.result() for f in futures]

    end_time = time.time()
    duration = end_time - start_time

    total_messages = num_clients * messages_per_client
    print(f"✅ {num_clients} clients sent {total_messages} messages in {duration:.2f} seconds")
    print(f"📊 Concurrent throughput: {total_messages / duration:.2f} messages/second")

    return total_messages / duration


def test_message_sizes():
    """Test with different message sizes"""
    from task_queue import send_agent_command

    print("\nTesting different message sizes...")

    sizes = [10, 100, 1000, 10000]  # Characters
    times = []

    for size in sizes:
        # Create message of specified size
        message = "x" * size
        command = f"echo '{message}'"

        start_time = time.time()

        # Send 100 messages of this size
        for i in range(100):
            send_agent_command("supervisor", command, f"size_test_{size}_{i}")

        end_time = time.time()
        duration = end_time - start_time
        times.append(duration)

        throughput = 100 / duration
        print(f"  {size} chars: {throughput:.2f} msg/s ({duration:.2f}s for 100 messages)")

    return sizes, times


def stress_test():
    """Run comprehensive stress test"""
    from task_queue import QueueClient, check_actors_health
    from task_queue.broker import check_broker_health

    print("\n" + "=" * 60)
    print("STARTING COMPREHENSIVE STRESS TEST")
    print("=" * 60)

    # Check initial health
    broker_health = check_broker_health()
    actors_health = check_actors_health()

    print(f"\nInitial Status:")
    print(f"  Broker: {broker_health['status']}")
    print(f"  Actors: {len(actors_health['actors'])} registered")
    print(f"  Redis: {broker_health.get('redis_version', 'Unknown')}")

    # Run all tests
    results = {}

    try:
        # 1. Throughput test
        throughput, msg_ids = test_throughput()
        results['throughput'] = throughput

        # 2. Parallel test
        parallel_rate = test_parallel_sending()
        results['parallel'] = parallel_rate

        # 3. Chain test
        chain_rate = test_task_chains()
        results['chains'] = chain_rate

        # 4. Concurrent clients
        concurrent_rate = test_concurrent_clients()
        results['concurrent'] = concurrent_rate

        # 5. Message sizes
        sizes, times = test_message_sizes()
        results['sizes'] = (sizes, times)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

    # Final statistics
    print("\n" + "=" * 60)
    print("STRESS TEST SUMMARY")
    print("=" * 60)

    print(f"\n📊 Performance Metrics:")
    print(f"  Sequential throughput: {results['throughput']:.2f} msg/s")
    print(f"  Parallel throughput: {results['parallel']:.2f} tasks/s")
    print(f"  Chain creation: {results['chains']:.2f} chains/s")
    print(f"  Concurrent clients: {results['concurrent']:.2f} msg/s")

    # Check if performance is acceptable
    if results['throughput'] > 100:
        print(f"\n✅ EXCELLENT: {results['throughput']:.0f}+ messages/second achieved!")
        return True
    elif results['throughput'] > 50:
        print(f"\n✅ GOOD: {results['throughput']:.0f}+ messages/second achieved")
        return True
    else:
        print(f"\n⚠️ SLOW: Only {results['throughput']:.0f} messages/second")
        return False


def main():
    """Run performance tests"""
    print("=" * 60)
    print("DRAMATIQ QUEUE PERFORMANCE TEST")
    print("=" * 60)
    print("\nThis test will:")
    print("  1. Send 1000+ sequential messages")
    print("  2. Test parallel message sending")
    print("  3. Create task chains")
    print("  4. Test concurrent clients")
    print("  5. Test different message sizes")
    print("\n⚠️ Make sure Redis is running and the worker is started!")

    # Run without interaction when not in TTY
    import os
    if os.isatty(0):
        input("\nPress Enter to start performance test...")
    else:
        print("\nStarting performance test...")

    success = stress_test()

    if success:
        print("\n🎉 Performance test PASSED!")
        print("The queue system can handle production workloads.")
        return 0
    else:
        print("\n⚠️ Performance test completed with warnings")
        return 1


if __name__ == "__main__":
    sys.exit(main())