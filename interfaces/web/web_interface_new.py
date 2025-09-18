#!/usr/bin/env python3
"""
Interfaccia Web Semplificata - Task Input + Terminali Reali
"""

import streamlit as st
import time
import subprocess
from claude_orchestrator import ClaudeNativeOrchestrator

# Page configuration
st.set_page_config(
    page_title="🤖 Claude Multi-Agent Terminal Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class SimpleTerminalInterface:
    def __init__(self):
        self.orchestrator = ClaudeNativeOrchestrator()
        # ALL 9 Claude Code agents
        self.claude_agents = [
            "claude-prompt-validator",
            "claude-task-coordinator",
            "claude-backend-api",
            "claude-database",
            "claude-frontend-ui",
            "claude-instagram",
            "claude-queue-manager",
            "claude-testing",
            "claude-deployment"
        ]

    def send_task_to_agent(self, agent, task):
        """Send task to specific agent"""
        return self.orchestrator.send_task_to_claude(agent, task)

    def get_agent_output(self, agent):
        """Get recent output from agent"""
        return self.orchestrator.get_claude_response(agent, wait_seconds=0)

def main():
    interface = SimpleTerminalInterface()

    # Header
    st.markdown("""
    <div style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>🤖 Claude Multi-Agent Terminal Interface</h1>
        <p style='color: white; margin: 0; opacity: 0.9;'>Direct interaction with real Claude Code terminals</p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh sidebar option
    with st.sidebar:
        st.markdown("### 🎛️ Controls")
        auto_refresh = st.checkbox("🔄 Auto-refresh (3s)", value=True)
        if st.button("🔄 Manual Refresh"):
            st.rerun()

    # ==========================================
    # TASK INPUT SECTION - TOP
    # ==========================================
    st.markdown("## 📝 Task Input")

    col1, col2 = st.columns([4, 1])

    with col1:
        task_input = st.text_area(
            "Enter your task (will be sent to all Claude Code terminals):",
            placeholder="Example: Analyze the current backend API and report any issues...",
            height=120,
            key="main_task_input"
        )

    with col2:
        st.markdown("#### Actions")

        if st.button("🚀 Send to All Agents", type="primary", use_container_width=True):
            if task_input:
                success_count = 0

                with st.spinner("Sending to all agents..."):
                    for agent in interface.claude_agents:
                        success = interface.send_task_to_agent(agent, task_input)
                        if success:
                            success_count += 1

                st.success(f"✅ Task sent to {success_count}/{len(interface.claude_agents)} agents")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Please enter a task")

        if st.button("🔄 Refresh All", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # ==========================================
    # LIVE TERMINALS SECTION - BOTTOM
    # ==========================================
    st.markdown("## 🖥️ Live Claude Code Terminals")

    st.markdown("""
    **Real-time view of Claude Code agent terminals.** These are actual Claude Code instances running in tmux.
    """)

    # Display all terminals
    for agent in interface.claude_agents:
        with st.container():
            # Agent header
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"### 🤖 {agent.upper().replace('-', ' ')}")

            with col2:
                # Status indicator
                try:
                    output = interface.get_agent_output(agent)
                    is_claude_active = any('Claude' in line or 'Welcome' in line for line in output.split('\n'))
                    if is_claude_active:
                        st.success("✅ Claude Active")
                    else:
                        st.info("🔄 Starting...")
                except:
                    st.error("❌ Error")

            # Terminal display
            col_main, col_side = st.columns([4, 1])

            with col_main:
                try:
                    # Get real terminal output
                    output = interface.get_agent_output(agent)
                    terminal_lines = output.split('\n')

                    # Show recent output (last 30 lines for better visibility)
                    recent_output = '\n'.join(terminal_lines[-30:])

                    # Display terminal content
                    st.text_area(
                        f"Terminal Output - {agent}",
                        recent_output,
                        height=350,
                        key=f"terminal_{agent}",
                        disabled=True,
                        help="Real-time output from Claude Code terminal"
                    )

                except Exception as e:
                    st.error(f"❌ Could not access {agent}: {str(e)}")

            with col_side:
                st.markdown("##### Direct Actions")

                # Individual message input
                individual_task = st.text_input(
                    "Direct message:",
                    key=f"individual_{agent}",
                    placeholder="Message for this agent only...",
                    help="Send message to this specific agent only"
                )

                if st.button(f"💬 Send", key=f"send_{agent}", use_container_width=True):
                    if individual_task:
                        success = interface.send_task_to_agent(agent, individual_task)
                        if success:
                            st.success("✅ Sent!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed")

                if st.button(f"🔄 Refresh", key=f"refresh_{agent}", use_container_width=True):
                    st.rerun()

            st.markdown("---")

    # Footer with system status
    st.markdown("### 📊 System Status")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Agents", "9")
    with col2:
        st.metric("System", "🟢 Online")
    with col3:
        st.metric("Last Update", time.strftime("%H:%M:%S"))
    with col4:
        if st.button("🧪 Test All Agents"):
            test_msg = "Quick test: Please respond with your agent name and current status"
            for agent in interface.claude_agents:
                interface.send_task_to_agent(agent, test_msg)
            st.success("🧪 Test sent to all agents!")

    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(3)
        st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🤖 Claude Multi-Agent Terminal Interface |
        🔗 Real Claude Code Integration |
        📊 Live Terminal Monitoring
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()