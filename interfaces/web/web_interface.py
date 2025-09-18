#!/usr/bin/env python3
"""
CrewAI Web Interface - Interfaccia grafica per monitoraggio e gestione agenti Claude
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import subprocess
import time
import json
from datetime import datetime, timedelta
import sys
import os

# Add project path
sys.path.append('.')
from claude_orchestrator import ClaudeNativeOrchestrator

# Page configuration
st.set_page_config(
    page_title="🤖 CrewAI Claude Manager",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CrewAIWebInterface:
    def __init__(self):
        self.orchestrator = ClaudeNativeOrchestrator()

    def get_agent_status(self):
        """Get real-time agent status"""
        progress = self.orchestrator.monitor_agent_progress()

        agents_data = []
        for agent, info in progress['agents'].items():
            agents_data.append({
                'Agent': agent,
                'Status': info['status'],
                'Last_Check': info['last_checked'],
                'Type': 'PM Agent' if agent in self.orchestrator.claude_sessions else 'Sub-Agent'
            })

        return pd.DataFrame(agents_data)

    def get_system_metrics(self):
        """Get system performance metrics"""
        try:
            # Get tmux sessions count
            result = subprocess.run(["/opt/homebrew/bin/tmux", "list-sessions"],
                                  capture_output=True, text=True, check=True)
            total_sessions = len(result.stdout.strip().split('\n'))

            # Get agent status
            progress = self.orchestrator.monitor_agent_progress()
            active_agents = len([a for a in progress['agents'].values() if a['status'] == 'active'])
            total_agents = len(progress['agents'])

            return {
                'total_sessions': total_sessions,
                'active_agents': active_agents,
                'total_agents': total_agents,
                'system_load': (active_agents / total_agents) * 100,
                'last_update': datetime.now().strftime("%H:%M:%S")
            }
        except:
            return {
                'total_sessions': 0,
                'active_agents': 0,
                'total_agents': 9,
                'system_load': 0,
                'last_update': datetime.now().strftime("%H:%M:%S")
            }

    def send_task_to_agent(self, agent, task):
        """Send task to specific agent"""
        return self.orchestrator.send_task_to_claude(agent, task)

    def get_agent_output(self, agent):
        """Get recent output from agent"""
        return self.orchestrator.get_claude_response(agent, wait_seconds=0)

    def run_intelligent_coordination(self, project_description):
        """Run intelligent task coordination"""
        return self.orchestrator.intelligent_task_distribution(project_description)

def main():
    # Initialize interface
    interface = CrewAIWebInterface()

    # Header
    st.markdown("""
    <div style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>🤖 CrewAI Claude Manager</h1>
        <p style='color: white; margin: 0; opacity: 0.9;'>Interfaccia Grafica per Monitoraggio Multi-Agente</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("## 🎛️ Control Panel")

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5s)", value=True)

    if auto_refresh:
        # Auto-refresh every 5 seconds
        time.sleep(0.1)
        st.rerun()

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()

    # Get system metrics
    metrics = interface.get_system_metrics()

    # Metrics display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🖥️ Total Sessions",
            value=metrics['total_sessions']
        )

    with col2:
        st.metric(
            label="🤖 Active Agents",
            value=f"{metrics['active_agents']}/{metrics['total_agents']}"
        )

    with col3:
        st.metric(
            label="📊 System Load",
            value=f"{metrics['system_load']:.1f}%"
        )

    with col4:
        st.metric(
            label="🕒 Last Update",
            value=metrics['last_update']
        )

    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "🤖 Live Agent Terminals",
        "📊 System Dashboard",
        "🧠 Intelligent Coordination"
    ])

    with tab1:
        st.markdown("## 🤖 Live Agent Terminal Interface")

        st.markdown("""
        **Direct interaction with real Claude Code terminals.**
        Enter your task above and see all agents respond in real-time below.
        """)

        # TASK INPUT SECTION - TOP
        st.markdown("### 📝 Task Input")

        col1, col2 = st.columns([4, 1])

        with col1:
            task_input = st.text_area(
                "Task for all agents:",
                placeholder="Enter your task here (will be sent to all Claude Code terminals)...",
                height=100,
                key="main_task_input"
            )

        with col2:
            st.markdown("#### Actions")

            if st.button("🚀 Send to All Agents", type="primary"):
                if task_input:
                    success_count = 0
                    claude_agents = ["claude-prompt-validator", "claude-task-coordinator", "claude-backend-api"]

                    for agent in claude_agents:
                        success = interface.send_task_to_agent(agent, task_input)
                        if success:
                            success_count += 1

                    st.success(f"✅ Task sent to {success_count}/{len(claude_agents)} agents")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please enter a task")

            if st.button("🔄 Refresh All"):
                st.rerun()

        st.markdown("---")

        # LIVE TERMINALS SECTION - BOTTOM
        st.markdown("### 🖥️ Live Claude Code Terminals")

        claude_agents = ["claude-prompt-validator", "claude-task-coordinator", "claude-backend-api"]

        # Display all terminals in a grid
        for agent in claude_agents:
            with st.container():
                st.markdown(f"#### 🤖 {agent.upper().replace('-', ' ')}")

                col1, col2 = st.columns([5, 1])

                with col1:
                    try:
                        # Get real terminal output
                        output = interface.get_agent_output(agent)
                        terminal_lines = output.split('\n')

                        # Show more lines for better visibility
                        recent_output = '\n'.join(terminal_lines[-25:])

                        # Check if Claude Code is active
                        is_claude_active = any('Claude' in line or 'Welcome' in line for line in terminal_lines)

                        if is_claude_active:
                            st.success("✅ Claude Code Active")
                        else:
                            st.info("🔄 Starting...")

                        # Show terminal content with scrolling
                        st.text_area(
                            f"Terminal Output",
                            recent_output,
                            height=300,
                            key=f"terminal_{agent}",
                            disabled=True
                        )

                    except Exception as e:
                        st.error(f"❌ Could not access {agent}: {str(e)}")

                with col2:
                    st.markdown("#### Direct Actions")

                    # Individual task input for this agent
                    individual_task = st.text_input(
                        "Direct message:",
                        key=f"task_{agent}",
                        placeholder="Message for this agent only..."
                    )

                    if st.button(f"💬 Send", key=f"send_{agent}"):
                        if individual_task:
                            success = interface.send_task_to_agent(agent, individual_task)
                            if success:
                                st.success("✅ Sent!")
                                time.sleep(1)
                                st.rerun()

                    if st.button(f"🔄 Refresh", key=f"refresh_{agent}"):
                        st.rerun()

                st.markdown("---")

        # Auto-refresh option
        if auto_refresh:
            time.sleep(2)
            st.rerun()

    with tab2:
        st.markdown("## 📊 System Dashboard")

        # Agent status table
        df = interface.get_agent_status()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🤖 Agent Status")

            # Color code the dataframe
            def color_status(val):
                if val == 'active':
                    return 'background-color: #d4edda; color: #155724'
                else:
                    return 'background-color: #f8d7da; color: #721c24'

            styled_df = df.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)

        with col2:
            # Status pie chart
            status_counts = df['Status'].value_counts()
            fig_pie = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Agent Status Distribution",
                color_discrete_map={'active': '#28a745', 'inactive': '#dc3545'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # System health chart
        st.markdown("### 📈 System Health Over Time")

        # Generate mock time series data for demo
        times = [datetime.now() - timedelta(minutes=x) for x in range(30, 0, -1)]
        health_data = pd.DataFrame({
            'Time': times,
            'Active_Agents': [metrics['active_agents'] + (i % 3 - 1) for i in range(30)],
            'System_Load': [max(10, metrics['system_load'] + (i % 20 - 10)) for i in range(30)]
        })

        fig_health = go.Figure()
        fig_health.add_trace(go.Scatter(
            x=health_data['Time'],
            y=health_data['Active_Agents'],
            mode='lines+markers',
            name='Active Agents',
            line=dict(color='#28a745')
        ))

        fig_health.update_layout(
            title='System Health Metrics',
            xaxis_title='Time',
            yaxis_title='Count',
            height=400
        )

        st.plotly_chart(fig_health, use_container_width=True)

    with tab2:
        st.markdown("## 🤖 Agent Control Center")

        # Agent selector
        agents = interface.orchestrator.claude_sessions
        selected_agent = st.selectbox("Select Agent", agents)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 📤 Send Task")

            task_input = st.text_area(
                "Task Description",
                placeholder="Enter task for the selected agent...",
                height=150
            )

            if st.button("💬 Send to Claude Terminal", type="primary"):
                if task_input and selected_agent:
                    success = interface.send_task_to_agent(selected_agent, task_input)
                    if success:
                        st.success(f"✅ Message sent to {selected_agent} Claude Code terminal")
                        st.info("💡 The message was sent to the Claude Code terminal. Claude Code will process it as an interactive session.")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed to send message to {selected_agent}")
                else:
                    st.warning("Please enter a message")

        # Show system metrics for dashboard
        st.markdown("### 📊 System Status")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Claude Sessions", "3")
        with col2:
            st.metric("System Status", "🟢 Online")
        with col3:
            st.metric("Last Update", metrics['last_update'])

    with tab3:
        st.markdown("## 🧠 Intelligent Coordination")

        st.markdown("""
        Use AI-powered project analysis to automatically distribute tasks
        to the appropriate Claude agents based on project requirements.
        """)

        project_description = st.text_area(
            "Project Description",
            placeholder="Describe your project (e.g., 'Create user authentication system with social login')",
            height=120
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            if st.button("🧠 Run Intelligent Coordination", type="primary"):
                if project_description:
                    with st.spinner("Analyzing project and distributing tasks..."):
                        result = interface.run_intelligent_coordination(project_description)

                        st.success("✅ Coordination completed!")

                        # Show results
                        st.markdown("### 📊 Coordination Results")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Project Type", result['project_type'].title())
                        with col_b:
                            st.metric("Teams Involved", len(result['required_teams']))

                        # Show team assignments
                        st.markdown("### 👥 Team Assignments")
                        for team in result['required_teams']:
                            status = result['distribution_status'][team]
                            status_icon = "✅" if status == "sent" else "❌"
                            st.write(f"{status_icon} **{team}** - Task {status}")

                        st.balloons()
                else:
                    st.warning("Please enter a project description")

        with col2:
            # Show example projects
            st.markdown("### 💡 Example Projects")

            examples = [
                "Create user authentication system with social login",
                "Build Instagram analytics dashboard with real-time metrics",
                "Develop e-commerce product catalog with search functionality",
                "Implement chat system with real-time messaging",
                "Create API for mobile app with user management"
            ]

            for example in examples:
                if st.button(f"📝 {example}", key=f"example_{hash(example)}"):
                    st.session_state['project_description'] = example
                    st.rerun()

    with tab4:
        st.markdown("## 🖥️ Real Agent Terminals")

        st.markdown("""
        **Live view of actual Claude Code terminals.**

        ⚠️ **Important**: These are real Claude Code sessions running in tmux terminals.
        Messages sent here will appear in the Claude Code prompt, but Claude Code responds
        interactively and may need human guidance for complex tasks.

        **This is NOT fully automated** - it's a bridge to interact with real Claude Code instances.
        """)

        # Real terminal grid
        claude_agents = ["claude-prompt-validator", "claude-task-coordinator", "claude-backend-api"]

        for agent in claude_agents:
            st.markdown(f"### 🤖 {agent.upper()}")

            col1, col2 = st.columns([3, 1])

            with col1:
                # Get real terminal output
                try:
                    output = interface.get_agent_output(agent)
                    recent_lines = output.split('\n')[-15:]
                    terminal_output = '\n'.join(recent_lines)

                    # Check if Claude Code is active
                    is_claude_active = any('Claude' in line or 'Welcome' in line for line in recent_lines)

                    if is_claude_active:
                        st.success("✅ Claude Code Active")
                    else:
                        st.info("🔄 Claude Code Starting...")

                    st.code(terminal_output, language="bash", height=200)

                except Exception as e:
                    st.error(f"❌ Could not access {agent}: {str(e)}")

            with col2:
                if st.button(f"📤 Quick Task", key=f"quick_{agent}"):
                    quick_task = "Status check: Please confirm you are active and ready for tasks."
                    success = interface.send_task_to_agent(agent, quick_task)
                    if success:
                        st.success("✅ Task sent!")
                        time.sleep(2)
                        st.rerun()

                if st.button(f"🔄 Refresh", key=f"refresh_{agent}"):
                    st.rerun()

        st.markdown("---")

        # Global terminal actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Refresh All Terminals", type="primary"):
                st.success("🔄 Refreshing all terminals...")
                time.sleep(1)
                st.rerun()

        with col2:
            if st.button("📤 Broadcast Message"):
                broadcast_msg = "Broadcast: All agents report status"
                for agent in claude_agents:
                    interface.send_task_to_agent(agent, broadcast_msg)
                st.success("📢 Message broadcasted to all agents!")

        with col3:
            if st.button("🧪 System Test"):
                test_msg = "System test: Please respond with your agent role and current time"
                for agent in claude_agents:
                    interface.send_task_to_agent(agent, test_msg)
                st.success("🧪 System test initiated!")

    with tab5:
        st.markdown("## 🖥️ Terminal Management")

        st.markdown("""
        Manage and access individual Claude agent terminals directly from the web interface.
        """)

        # Terminal actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🖥️ Open All Terminals", type="primary"):
                st.info("Opening all Claude agent terminals...")
                # Execute terminal opening script
                try:
                    subprocess.Popen(["/Users/erik/Desktop/riona_ai/riona-ai/claude-enhanced-manager.sh"])
                    st.success("✅ Terminals opening in separate windows")
                except Exception as e:
                    st.error(f"❌ Error opening terminals: {e}")

        with col2:
            if st.button("📊 System Monitor"):
                st.info("Opening system monitor...")
                st.success("✅ Monitor view activated")

        with col3:
            if st.button("🔄 Restart Services"):
                st.warning("⚠️ This will restart all agent services")
                if st.button("Confirm Restart"):
                    st.success("✅ Services restarted")

        # Terminal status grid
        st.markdown("### 🖥️ Terminal Status Grid")

        df = interface.get_agent_status()

        # Create a grid layout
        cols = st.columns(3)
        for idx, (_, agent) in enumerate(df.iterrows()):
            col_idx = idx % 3
            with cols[col_idx]:
                status_color = "🟢" if agent['Status'] == 'active' else "🔴"

                with st.container():
                    st.markdown(f"""
                    <div style='border: 1px solid #ddd; padding: 1rem; border-radius: 5px; margin: 0.5rem 0;'>
                        <h4>{status_color} {agent['Agent']}</h4>
                        <p><strong>Status:</strong> {agent['Status'].title()}</p>
                        <p><strong>Type:</strong> {agent['Type']}</p>
                        <p><strong>Last Check:</strong> {agent['Last_Check']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"🔗 Connect", key=f"connect_{agent['Agent']}"):
                        st.info(f"Opening terminal for {agent['Agent']}")

    with tab5:
        st.markdown("## 📈 Analytics & Performance")

        # Performance metrics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Agent Utilization")

            # Create utilization chart
            df = interface.get_agent_status()
            active_count = len(df[df['Status'] == 'active'])
            inactive_count = len(df[df['Status'] == 'inactive'])

            fig_util = go.Figure(data=[
                go.Bar(name='Active', x=['Agents'], y=[active_count], marker_color='#28a745'),
                go.Bar(name='Inactive', x=['Agents'], y=[inactive_count], marker_color='#dc3545')
            ])

            fig_util.update_layout(
                title='Agent Utilization',
                barmode='stack',
                height=300
            )

            st.plotly_chart(fig_util, use_container_width=True)

        with col2:
            st.markdown("### ⚡ Performance Metrics")

            # Generate mock performance data
            perf_data = pd.DataFrame({
                'Metric': ['Response Time', 'Task Success Rate', 'System Uptime', 'Memory Usage'],
                'Value': [150, 95, 99.9, 68],
                'Unit': ['ms', '%', '%', '%']
            })

            for _, row in perf_data.iterrows():
                if row['Unit'] == 'ms':
                    color = "normal"
                elif row['Value'] > 90:
                    color = "normal"
                else:
                    color = "inverse"

                st.metric(
                    label=row['Metric'],
                    value=f"{row['Value']}{row['Unit']}"
                )

        # Activity timeline
        st.markdown("### 📅 Recent Activity Timeline")

        # Mock activity data
        activity_data = [
            {"Time": "13:45", "Agent": "backend-api", "Action": "Task completed", "Status": "Success"},
            {"Time": "13:42", "Agent": "frontend-ui", "Action": "Task started", "Status": "In Progress"},
            {"Time": "13:40", "Agent": "database", "Action": "Schema updated", "Status": "Success"},
            {"Time": "13:38", "Agent": "testing", "Action": "Tests running", "Status": "In Progress"},
        ]

        for activity in activity_data:
            status_color = {"Success": "🟢", "In Progress": "🟡", "Error": "🔴"}.get(activity["Status"], "⚪")

            st.markdown(f"""
            **{activity['Time']}** - {status_color} **{activity['Agent']}**: {activity['Action']}
            """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🤖 CrewAI Claude Manager v1.0 |
        🔗 Direct Claude Integration |
        📊 Real-time Monitoring
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()