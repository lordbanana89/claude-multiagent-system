#!/usr/bin/env python3
"""
Complete Web Interface - Multi-Agent System Integration
Interfaccia completa che integra LangChain-pattern coordination con terminali Claude reali
"""

import streamlit as st
import time
import subprocess
import sys
import os
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.append('.')

try:
    from claude_orchestrator import ClaudeNativeOrchestrator
    from langchain_claude_final import MultiAgentCoordinator, AgentResponse
    LANGCHAIN_INTEGRATION = True
except ImportError as e:
    st.error(f"Import error: {e}")
    LANGCHAIN_INTEGRATION = False

# Page configuration
st.set_page_config(
    page_title="🤖 Complete Multi-Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CompleteMultiAgentInterface:
    """Complete interface with both manual control and intelligent coordination"""

    def __init__(self):
        self.orchestrator = ClaudeNativeOrchestrator()
        if LANGCHAIN_INTEGRATION:
            self.multi_agent_coordinator = MultiAgentCoordinator()

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

    def run_intelligent_coordination(self, project_description):
        """Run intelligent multi-agent coordination"""
        if LANGCHAIN_INTEGRATION:
            return self.multi_agent_coordinator.coordinate_project(project_description)
        else:
            return {"error": "LangChain integration not available"}

def main():
    interface = CompleteMultiAgentInterface()

    # Header
    st.markdown("""
    <div style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>🤖 Complete Multi-Agent System</h1>
        <p style='color: white; margin: 0; opacity: 0.9;'>Intelligent Coordination + Real Claude Code Terminals</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎛️ System Controls")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (3s)", value=False)

        # System status
        st.markdown("### 📊 System Status")
        if LANGCHAIN_INTEGRATION:
            st.success("✅ Multi-Agent Coordination: Active")
        else:
            st.warning("⚠️ Multi-Agent Coordination: Limited")

        st.info(f"🤖 Claude Agents: {len(interface.claude_agents)}")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🔄 Refresh All"):
            st.rerun()

        if st.button("🧪 System Test"):
            st.session_state['run_system_test'] = True
            st.rerun()

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 Intelligent Coordination",
        "🤖 Live Agent Terminals",
        "📊 System Dashboard",
        "📋 Project Templates"
    ])

    # ==========================================
    # TAB 1: INTELLIGENT COORDINATION
    # ==========================================
    with tab1:
        st.markdown("## 🧠 Multi-Agent Project Coordination")

        if not LANGCHAIN_INTEGRATION:
            st.error("⚠️ Multi-Agent Coordination requires LangChain integration. Using manual fallback.")

        st.markdown("""
        **Intelligent project coordination using LangChain-pattern multi-agent system.**

        The system will:
        1. 📋 **Analyze** your project requirements across specialists
        2. 🔧 **Plan** implementation using coordinated agents
        3. 🚀 **Integrate** all components into a complete strategy
        """)

        # Project input section
        col1, col2 = st.columns([3, 1])

        with col1:
            project_description = st.text_area(
                "🎯 Project Description:",
                placeholder="""Example: Create a social media analytics platform with:
- Instagram engagement tracking dashboard
- Automated content scheduling with AI
- User management and authentication
- Mobile API for iOS/Android apps
- Real-time notifications system""",
                height=150,
                key="project_coordination_input"
            )

        with col2:
            st.markdown("#### Coordination Options")

            coordination_mode = st.selectbox(
                "Mode:",
                ["Complete Project", "Analysis Only", "Implementation Only"],
                key="coordination_mode"
            )

            if st.button("🚀 Start Coordination", type="primary", use_container_width=True):
                if project_description and LANGCHAIN_INTEGRATION:
                    # Store in session state without overriding widget state
                    if 'coordination_project' not in st.session_state:
                        st.session_state['coordination_project'] = ""
                    if 'run_coordination' not in st.session_state:
                        st.session_state['run_coordination'] = False

                    st.session_state['coordination_project'] = project_description
                    st.session_state['run_coordination'] = True
                    st.rerun()
                elif not project_description:
                    st.warning("Please enter a project description")
                else:
                    st.error("Multi-agent coordination not available")

        # Show coordination results
        if st.session_state.get('run_coordination') and LANGCHAIN_INTEGRATION:
            st.markdown("---")
            st.markdown("### 🔄 Coordination in Progress...")

            with st.spinner("Running multi-agent coordination..."):
                project = st.session_state['coordination_project']

                # Run coordination
                result = interface.run_intelligent_coordination(project)

                if result.get("success"):
                    st.success("🎉 Multi-Agent Coordination Completed!")

                    # Display results
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.metric("Agents Involved", result.get('agents_involved', 0))
                    with col_b:
                        st.metric("Coordination Phases", result.get('coordination_phases', 0))
                    with col_c:
                        st.metric("Execution Time", f"{result.get('total_execution_time', 0):.1f}s")

                    # Show detailed results
                    st.markdown("#### 📊 Analysis Results")
                    for agent_type, agent_result in result.get('analysis_results', {}).items():
                        with st.expander(f"📋 {agent_result.agent}"):
                            st.write(f"**Task**: {agent_result.task}")
                            st.write(f"**Response**: {agent_result.response}")
                            st.write(f"**Execution Time**: {agent_result.execution_time:.2f}s")

                    st.markdown("#### 🔧 Implementation Results")
                    for agent_type, agent_result in result.get('implementation_results', {}).items():
                        with st.expander(f"🔧 {agent_result.agent}"):
                            st.write(f"**Task**: {agent_result.task}")
                            st.write(f"**Response**: {agent_result.response}")
                            st.write(f"**Execution Time**: {agent_result.execution_time:.2f}s")

                    # Integration strategy
                    integration = result.get('integration_result')
                    if integration:
                        st.markdown("#### 🚀 Integration Strategy")
                        st.write(f"**Response**: {integration.response}")

                    # Generate project summary
                    if st.button("📄 Generate Complete Summary"):
                        summary = interface.multi_agent_coordinator.generate_project_summary(result)
                        st.text_area("Complete Project Summary", summary, height=300)

                else:
                    st.error(f"❌ Coordination failed: {result.get('error', 'Unknown error')}")

            # Clear the coordination flag
            st.session_state['run_coordination'] = False

    # ==========================================
    # TAB 2: LIVE AGENT TERMINALS
    # ==========================================
    with tab2:
        st.markdown("## 🤖 Live Agent Terminal Interface")

        st.markdown("""
        **Direct interaction with real Claude Code terminals.**
        Send tasks and see real-time responses from each specialized agent.
        """)

        # Task input section
        col1, col2 = st.columns([4, 1])

        with col1:
            task_input = st.text_area(
                "Task for all agents:",
                placeholder="Enter your task here (will be sent to all Claude Code terminals)...",
                height=100,
                key="terminal_task_input"
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

        # Display all terminals
        st.markdown("### 🖥️ Live Claude Code Terminals")

        for agent in interface.claude_agents:
            with st.container():
                # Agent header
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"#### 🤖 {agent.upper().replace('-', ' ')}")

                with col2:
                    # Status indicator
                    try:
                        output = interface.get_agent_output(agent)
                        is_claude_active = any('Claude' in line or 'Welcome' in line for line in output.split('\n'))
                        if is_claude_active:
                            st.success("✅ Active")
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

                        # Show recent output
                        recent_output = '\n'.join(terminal_lines[-25:])

                        # Display terminal content
                        st.text_area(
                            f"Terminal Output - {agent}",
                            recent_output,
                            height=300,
                            key=f"terminal_display_{agent}",
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
                        key=f"individual_task_{agent}",
                        placeholder="Message for this agent only...",
                        help="Send message to this specific agent only"
                    )

                    if st.button(f"💬 Send", key=f"send_individual_{agent}", use_container_width=True):
                        if individual_task:
                            success = interface.send_task_to_agent(agent, individual_task)
                            if success:
                                st.success("✅ Sent!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Failed")

                    if st.button(f"🔄 Refresh", key=f"refresh_individual_{agent}", use_container_width=True):
                        st.rerun()

                st.markdown("---")

    # ==========================================
    # TAB 3: SYSTEM DASHBOARD
    # ==========================================
    with tab3:
        st.markdown("## 📊 System Dashboard")

        # System metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Active Agents", len(interface.claude_agents))
        with col2:
            status = "🟢 Online" if LANGCHAIN_INTEGRATION else "🟡 Limited"
            st.metric("System Status", status)
        with col3:
            st.metric("Coordination", "Available" if LANGCHAIN_INTEGRATION else "Limited")
        with col4:
            st.metric("Last Update", time.strftime("%H:%M:%S"))

        # System test
        if st.session_state.get('run_system_test'):
            st.markdown("### 🧪 System Test Results")

            with st.spinner("Running system test..."):
                test_msg = "System test: Please respond with your agent name and current status"

                results = {}
                for agent in interface.claude_agents[:3]:  # Test first 3
                    success = interface.send_task_to_agent(agent, test_msg)
                    results[agent] = "✅ Sent" if success else "❌ Failed"

                time.sleep(3)  # Wait for responses

                for agent, status in results.items():
                    st.write(f"{status} {agent}")

            st.session_state['run_system_test'] = False

    # ==========================================
    # TAB 4: PROJECT TEMPLATES
    # ==========================================
    with tab4:
        st.markdown("## 📋 Project Templates")

        st.markdown("**Quick start templates for common project types:**")

        templates = {
            "Social Media Platform": """Create a comprehensive social media analytics platform with:
- Instagram engagement tracking and analytics dashboard
- Automated content scheduling with AI optimization
- User management with role-based permissions
- Real-time notification system
- Mobile API for iOS/Android apps
- Database for storing user data and analytics
- Admin panel for platform management""",

            "E-commerce Backend": """Design a scalable e-commerce backend system with:
- Product catalog management with search functionality
- User authentication and profile management
- Shopping cart and checkout process
- Payment processing integration
- Order management and tracking
- Inventory management system
- Admin dashboard for business analytics""",

            "Task Management App": """Build a collaborative task management application with:
- User authentication and team management
- Project creation and task assignment
- Real-time collaboration features
- File upload and sharing capabilities
- Progress tracking and reporting
- Mobile-responsive design
- Integration with external tools (Slack, email)""",

            "API Gateway Service": """Implement a microservices API gateway with:
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and throttling
- API versioning and documentation
- Monitoring and logging
- Circuit breaker pattern
- Service discovery integration"""
        }

        for template_name, template_content in templates.items():
            with st.expander(f"📝 {template_name}"):
                st.text_area(
                    "Template Content:",
                    template_content,
                    height=150,
                    key=f"template_{template_name}",
                    disabled=True
                )

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button(f"🚀 Run Coordination", key=f"coord_{template_name}"):
                        # Initialize session state if needed
                        if 'coordination_project' not in st.session_state:
                            st.session_state['coordination_project'] = ""
                        if 'run_coordination' not in st.session_state:
                            st.session_state['run_coordination'] = False

                        st.session_state['coordination_project'] = template_content
                        st.session_state['run_coordination'] = True
                        st.success("Template loaded! Check the Intelligent Coordination tab.")

                with col_b:
                    if st.button(f"📤 Send to Terminals", key=f"term_{template_name}"):
                        st.success("Template loaded! Use the task in the Live Agent Terminals tab.")
                        # Don't modify widget-bound session state

    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(3)
        st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🤖 Complete Multi-Agent System |
        🧠 Intelligent Coordination |
        🖥️ Real Claude Code Integration |
        📊 Live Terminal Monitoring
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()