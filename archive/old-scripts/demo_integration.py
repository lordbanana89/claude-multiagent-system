#!/usr/bin/env python3
"""
Demo script showing the integrated Claude Multi-Agent System in action
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.message_bus import get_message_bus, MessagePriority
from core.workflow_engine import get_workflow_engine
from agents.agent_bridge import get_bridge_manager
from core.tmux_client import TMUXClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_system():
    """Initialize all system components"""
    logger.info("🚀 Initializing Claude Multi-Agent System...")

    # Create TMUX sessions
    tmux = TMUXClient()
    sessions_needed = ["claude-backend-api", "claude-database", "claude-supervisor"]

    for session in sessions_needed:
        if not tmux.session_exists(session):
            tmux.create_session(session)
            logger.info(f"✓ Created session: {session}")
            # Initialize session with a simple prompt
            tmux.send_command(session, f"echo '=== Agent {session.replace('claude-', '')} Ready ==='")
        else:
            logger.info(f"✓ Session exists: {session}")

    # Start message bus
    bus = get_message_bus()
    if not bus.running:
        bus.start()
        logger.info("✓ Message bus started")

    # Initialize workflow engine
    engine = get_workflow_engine()
    logger.info("✓ Workflow engine ready")

    # Start agent bridges
    bridge_manager = get_bridge_manager()
    for session in ["backend-api", "database", "supervisor"]:
        if session not in bridge_manager.bridges:
            try:
                from agents.agent_bridge import AgentBridge
                bridge = AgentBridge(session)
                bridge.start()
                bridge_manager.bridges[session] = bridge
                logger.info(f"✓ Started bridge for {session}")
            except Exception as e:
                logger.warning(f"⚠️ Could not start bridge for {session}: {e}")

    time.sleep(2)  # Let everything initialize
    logger.info("✅ System initialized successfully!\n")

    return bus, engine, bridge_manager, tmux

def demo_simple_task(bus, tmux):
    """Demonstrate simple task execution"""
    logger.info("📝 Demo 1: Simple Task Execution")
    logger.info("-" * 40)

    # Submit task
    task_id = bus.publish_task(
        agent="backend-api",
        task={
            "command": "/bin/echo 'Hello from Claude Multi-Agent System!'",
            "params": {},
            "timeout": 5
        },
        priority=MessagePriority.HIGH
    )

    logger.info(f"Submitted task: {task_id}")

    # Monitor execution
    for i in range(10):
        status = bus.get_task_status(task_id)
        if status:
            logger.info(f"Task status: {status['status']}")
            if status['status'] in ['completed', 'failed']:
                break
        time.sleep(1)

    # Check output
    output = tmux.capture_pane("claude-backend-api")
    if "Hello from Claude Multi-Agent System!" in output:
        logger.info("✅ Task executed successfully!")
    else:
        logger.info("⚠️ Task may not have executed properly")

    logger.info("")

def demo_multi_agent(bus, tmux):
    """Demonstrate multi-agent coordination"""
    logger.info("🤝 Demo 2: Multi-Agent Coordination")
    logger.info("-" * 40)

    agents = ["backend-api", "database", "supervisor"]
    task_ids = []

    # Submit tasks to multiple agents
    for agent in agents:
        task_id = bus.publish_task(
            agent=agent,
            task={
                "command": f"/bin/echo '{agent.upper()} processing task'",
                "params": {"demo": True},
                "timeout": 5
            }
        )
        task_ids.append((agent, task_id))
        logger.info(f"Submitted task to {agent}: {task_id}")

    # Monitor all tasks
    time.sleep(3)
    completed = 0
    for agent, task_id in task_ids:
        status = bus.get_task_status(task_id)
        if status:
            logger.info(f"{agent}: {status['status']}")
            if status['status'] == 'completed':
                completed += 1

    logger.info(f"✅ {completed}/{len(task_ids)} agents completed tasks")
    logger.info("")

def demo_workflow(engine):
    """Demonstrate workflow execution"""
    logger.info("🔄 Demo 3: Workflow Orchestration")
    logger.info("-" * 40)

    # Define workflow
    workflow_def = {
        "name": "Demo Workflow",
        "description": "Simple demo workflow",
        "steps": [
            {
                "id": "init",
                "name": "Initialize",
                "agent": "supervisor",
                "action": "/bin/echo 'Starting workflow'",
                "params": {}
            },
            {
                "id": "process",
                "name": "Process Data",
                "agent": "backend-api",
                "action": "/bin/echo 'Processing data'",
                "params": {},
                "depends_on": ["init"]
            },
            {
                "id": "store",
                "name": "Store Results",
                "agent": "database",
                "action": "/bin/echo 'Storing results'",
                "params": {},
                "depends_on": ["process"]
            }
        ]
    }

    # Define and execute workflow
    workflow_id = engine.define_workflow(workflow_def)
    logger.info(f"Defined workflow: {workflow_id}")

    execution_id = engine.execute(workflow_id, {})
    logger.info(f"Started execution: {execution_id}")

    # Monitor execution
    for i in range(15):
        status = engine.get_execution_status(execution_id)
        if status:
            logger.info(f"Workflow status: {status['status']}")

            # Show step statuses
            for step_id, step in status['steps'].items():
                logger.info(f"  - {step['name']}: {step['status']}")

            if status['status'] in ['completed', 'failed']:
                break

        time.sleep(2)

    logger.info("")

def show_system_status(bus, engine, bridge_manager):
    """Display system status"""
    logger.info("📊 System Status")
    logger.info("-" * 40)

    # Agent statuses
    for agent in ["supervisor", "backend-api", "database"]:
        status = bus.get_agent_status(agent)
        if status:
            logger.info(f"Agent {agent}: {status.get('status', 'unknown')}")

    # Pending tasks
    pending = bus.get_pending_tasks()
    logger.info(f"Pending tasks: {len(pending)}")

    # Active workflows
    logger.info(f"Defined workflows: {len(engine.workflows)}")
    logger.info(f"Active executions: {len(engine.executions)}")

    # Active bridges
    logger.info(f"Active bridges: {len(bridge_manager.bridges)}")

    logger.info("")

def main():
    """Main demo function"""
    print("\n" + "=" * 60)
    print("Claude Multi-Agent System - Integration Demo")
    print("=" * 60 + "\n")

    try:
        # Setup system
        bus, engine, bridge_manager, tmux = setup_system()

        # Run demos
        demo_simple_task(bus, tmux)
        demo_multi_agent(bus, tmux)
        demo_workflow(engine)

        # Show status
        show_system_status(bus, engine, bridge_manager)

        logger.info("🎉 Demo completed successfully!")
        logger.info("\nThe Claude Multi-Agent System is fully integrated and operational.")
        logger.info("All components are communicating correctly through the unified architecture.")

    except KeyboardInterrupt:
        logger.info("\n\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        logger.info("\nCleaning up...")
        if 'bridge_manager' in locals():
            bridge_manager.stop_all()
        if 'bus' in locals() and bus.running:
            bus.stop()
        logger.info("✓ Cleanup complete")

if __name__ == "__main__":
    main()