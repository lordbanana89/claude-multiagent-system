"""
Queue Monitor - Streamlit component for monitoring Dramatiq queue
"""

import streamlit as st
import time
import json
from typing import Dict, List, Any
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def render_queue_monitor():
    """Render queue monitoring interface"""
    st.markdown("## 📊 Queue Monitor")

    try:
        from task_queue import QueueClient, check_actors_health
        from task_queue.broker import check_broker_health

        # Initialize queue client
        if 'queue_client' not in st.session_state:
            st.session_state.queue_client = QueueClient()

        client = st.session_state.queue_client

        # Health status
        col1, col2, col3 = st.columns(3)

        # Broker health
        broker_health = check_broker_health()
        with col1:
            if broker_health['status'] == 'healthy':
                st.success("🟢 Broker: Healthy")
            elif broker_health['status'] == 'degraded':
                st.warning("🟡 Broker: Degraded")
            else:
                st.error("🔴 Broker: Unhealthy")

            if broker_health.get('redis_version'):
                st.caption(f"Redis {broker_health['redis_version']}")

        # Actors health
        actors_health = check_actors_health()
        with col2:
            st.metric(
                "Registered Actors",
                len(actors_health['actors']),
                delta=None
            )
            st.caption(f"{actors_health['active_sessions']}/{actors_health['agents_available']} sessions active")

        # Queue stats
        stats = client.get_stats()
        with col3:
            st.metric(
                "Total Messages",
                stats['total_messages_sent'],
                delta=None
            )
            st.caption("Since startup")

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Live Stats", "📜 Message History", "🎯 Send Task", "⚙️ Configuration"
        ])

        with tab1:
            st.markdown("### 📈 Live Queue Statistics")

            # Messages by actor
            if stats.get('messages_by_actor'):
                st.markdown("#### Messages by Actor")
                actor_data = pd.DataFrame(
                    list(stats['messages_by_actor'].items()),
                    columns=['Actor', 'Count']
                ).sort_values('Count', ascending=False)

                # Bar chart
                fig = go.Figure(data=[
                    go.Bar(
                        x=actor_data['Actor'],
                        y=actor_data['Count'],
                        marker_color='indianred'
                    )
                ])
                fig.update_layout(
                    title="Message Distribution by Actor",
                    xaxis_title="Actor",
                    yaxis_title="Message Count",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)

            # Redis metrics
            if broker_health.get('used_memory_human'):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Redis Memory", broker_health['used_memory_human'])
                with col2:
                    st.metric("Connected Clients", broker_health.get('connected_clients', 0))
                with col3:
                    st.metric("Redis URL", broker_health['redis_url'])

        with tab2:
            st.markdown("### 📜 Recent Message History")

            # Get recent messages
            history = client.get_history(limit=20)

            if history:
                # Convert to dataframe
                history_data = []
                for msg in history:
                    history_data.append({
                        'Time': time.strftime('%H:%M:%S', time.localtime(msg.timestamp)),
                        'Actor': msg.actor_name,
                        'Status': msg.status,
                        'Args': str(msg.args[:100]) if len(str(msg.args)) > 100 else str(msg.args)
                    })

                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True, height=400)

                # Clear history button
                if st.button("🗑️ Clear History"):
                    client.clear_history()
                    st.success("History cleared")
                    st.rerun()
            else:
                st.info("No messages in history yet")

        with tab3:
            st.markdown("### 🎯 Send Test Task")

            # Task type selection
            task_type = st.selectbox(
                "Task Type",
                ["Send Command", "Broadcast", "Notification", "Task Chain"]
            )

            if task_type == "Send Command":
                col1, col2 = st.columns(2)
                with col1:
                    agent_id = st.selectbox(
                        "Target Agent",
                        ["supervisor", "backend-api", "database", "frontend-ui", "testing"]
                    )
                with col2:
                    command = st.text_input("Command", value="echo 'Test from Queue Monitor'")

                if st.button("📤 Send Command"):
                    from task_queue import send_agent_command
                    msg_id = send_agent_command(agent_id, command)
                    st.success(f"Command sent! Message ID: {msg_id[:8]}...")

            elif task_type == "Broadcast":
                message = st.text_input("Broadcast Message", value="System broadcast test")
                exclude = st.multiselect(
                    "Exclude Agents",
                    ["supervisor", "backend-api", "database", "frontend-ui", "testing"]
                )

                if st.button("📢 Send Broadcast"):
                    from task_queue import broadcast_to_all
                    msg_id = broadcast_to_all(message, exclude)
                    st.success(f"Broadcast sent! Message ID: {msg_id[:8]}...")

            elif task_type == "Notification":
                col1, col2 = st.columns(2)
                with col1:
                    agent_id = st.selectbox(
                        "Target Agent",
                        ["supervisor", "backend-api", "database", "frontend-ui", "testing"],
                        key="notif_agent"
                    )
                    title = st.text_input("Title", value="Test Notification")
                with col2:
                    notif_type = st.selectbox("Type", ["info", "warning", "error", "success"])
                    message = st.text_input("Message", value="This is a test notification")

                if st.button("🔔 Send Notification"):
                    from task_queue import quick_notify
                    msg_id = quick_notify(agent_id, title, message, notif_type)
                    st.success(f"Notification sent! Message ID: {msg_id[:8]}...")

            elif task_type == "Task Chain":
                st.markdown("#### Define Task Chain Steps")

                # Number of steps
                num_steps = st.number_input("Number of Steps", min_value=1, max_value=10, value=3)

                steps = []
                for i in range(num_steps):
                    with st.expander(f"Step {i+1}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            agent = st.selectbox(
                                "Agent",
                                ["supervisor", "backend-api", "database", "frontend-ui", "testing"],
                                key=f"chain_agent_{i}"
                            )
                            command = st.text_input(
                                "Command",
                                value=f"echo 'Step {i+1}'",
                                key=f"chain_cmd_{i}"
                            )
                        with col2:
                            desc = st.text_input(
                                "Description",
                                value=f"Step {i+1} description",
                                key=f"chain_desc_{i}"
                            )
                            delay = st.number_input(
                                "Delay (seconds)",
                                min_value=0,
                                max_value=10,
                                value=1,
                                key=f"chain_delay_{i}"
                            )

                        steps.append({
                            "agent_id": agent,
                            "command": command,
                            "description": desc,
                            "delay": delay
                        })

                if st.button("🔗 Execute Chain"):
                    msg_id = client.create_task_chain(steps)
                    st.success(f"Task chain created! Message ID: {msg_id[:8]}...")

        with tab4:
            st.markdown("### ⚙️ Queue Configuration")

            # Display current configuration
            st.markdown("#### Current Settings")

            col1, col2 = st.columns(2)
            with col1:
                st.info(f"""
                **Broker Type:** {broker_health['broker_type']}
                **Redis URL:** {broker_health['redis_url']}
                **Status:** {broker_health['status']}
                """)

            with col2:
                if broker_health.get('errors'):
                    st.error("**Errors:**\n" + "\n".join(broker_health['errors']))
                else:
                    st.success("No errors detected")

            # Worker status
            st.markdown("#### Worker Status")
            st.info("""
            To start the Dramatiq worker:
            ```bash
            python -m dramatiq task_queue.worker
            ```

            Or with Overmind:
            ```bash
            overmind start  # Includes dramatiq process
            ```
            """)

            # Test connection button
            if st.button("🔄 Test Connection"):
                try:
                    from task_queue import broker
                    st.success(f"✅ Connected to {type(broker).__name__}")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")

        # Auto-refresh option
        if st.checkbox("Auto-refresh (5 seconds)", value=False):
            time.sleep(5)
            st.rerun()

    except ImportError as e:
        st.error(f"Queue system not available: {e}")
        st.info("Make sure task_queue package is properly installed")
    except Exception as e:
        st.error(f"Error loading queue monitor: {e}")


if __name__ == "__main__":
    # Standalone testing
    st.set_page_config(
        page_title="Queue Monitor",
        page_icon="📊",
        layout="wide"
    )
    render_queue_monitor()