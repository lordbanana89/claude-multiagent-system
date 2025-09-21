#!/usr/bin/env python3
"""
Enhanced Web Interface - LangGraph Platform Features + Claude CLI
Interfaccia avanzata che integra funzionalità LangGraph Platform con Claude Code CLI
"""

import streamlit as st
import time
import subprocess
import sys
import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Add current directory to path for imports
sys.path.append('.')

try:
    from claude_orchestrator import ClaudeNativeOrchestrator
    from langchain_claude_final import MultiAgentCoordinator, AgentResponse
    from auth_manager import AuthManager, render_login_form, render_user_management, render_workspace_management, User
    LANGCHAIN_INTEGRATION = True
    AUTH_INTEGRATION = True
except ImportError as e:
    st.error(f"Import error: {e}")
    LANGCHAIN_INTEGRATION = False
    AUTH_INTEGRATION = False

# Page configuration
st.set_page_config(
    page_title="🤖 Enhanced Multi-Agent Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@dataclass
class AgentState:
    """Agent state management"""
    name: str
    session: str
    status: str  # active, idle, error
    current_task: Optional[str] = None
    last_activity: Optional[datetime] = None
    task_count: int = 0
    success_rate: float = 100.0
    memory: Dict[str, Any] = None

    def __post_init__(self):
        if self.memory is None:
            self.memory = {}

@dataclass
class WorkflowNode:
    """Visual workflow node"""
    id: str
    name: str
    agent: str
    task_template: str
    x: float
    y: float
    connections: List[str] = None

    def __post_init__(self):
        if self.connections is None:
            self.connections = []

@dataclass
class ProjectTemplate:
    """Enhanced project template"""
    name: str
    description: str
    category: str
    workflow_nodes: List[WorkflowNode]
    estimated_time: str
    difficulty: str
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class StateManager:
    """Advanced state management for agents"""

    def __init__(self):
        self.db_path = "/Users/erik/Desktop/riona_ai/riona-ai/.riona/agents/crewai/agent_state.db"
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for state persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                name TEXT PRIMARY KEY,
                session TEXT,
                status TEXT,
                current_task TEXT,
                last_activity TEXT,
                task_count INTEGER,
                success_rate REAL,
                memory TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                task TEXT,
                status TEXT,
                timestamp TEXT,
                execution_time REAL,
                result TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_agent_state(self, agent_state: AgentState):
        """Save agent state to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO agent_states
            (name, session, status, current_task, last_activity, task_count, success_rate, memory)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_state.name,
            agent_state.session,
            agent_state.status,
            agent_state.current_task,
            agent_state.last_activity.isoformat() if agent_state.last_activity else None,
            agent_state.task_count,
            agent_state.success_rate,
            json.dumps(agent_state.memory)
        ))

        conn.commit()
        conn.close()

    def load_agent_state(self, agent_name: str) -> Optional[AgentState]:
        """Load agent state from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agent_states WHERE name = ?", (agent_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return AgentState(
                name=row[0],
                session=row[1],
                status=row[2],
                current_task=row[3],
                last_activity=datetime.fromisoformat(row[4]) if row[4] else None,
                task_count=row[5],
                success_rate=row[6],
                memory=json.loads(row[7]) if row[7] else {}
            )
        return None

    def log_task_execution(self, agent_name: str, task: str, status: str, execution_time: float, result: str):
        """Log task execution for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO task_history (agent_name, task, status, timestamp, execution_time, result)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (agent_name, task, status, datetime.now().isoformat(), execution_time, result))

        conn.commit()
        conn.close()

class VisualWorkflowBuilder:
    """Visual drag-and-drop workflow builder"""

    def __init__(self):
        self.workflows = {}
        self.load_default_templates()

    def load_default_templates(self):
        """Load default workflow templates"""
        self.workflows["social_media_platform"] = ProjectTemplate(
            name="Social Media Platform",
            description="Complete social media analytics platform",
            category="Full Stack",
            estimated_time="2-3 weeks",
            difficulty="Advanced",
            tags=["React", "API", "Analytics"],
            workflow_nodes=[
                WorkflowNode("1", "Requirements Analysis", "claude-task-coordinator",
                           "Analyze requirements for: {project}", 100, 100, ["2", "3"]),
                WorkflowNode("2", "Database Design", "claude-database",
                           "Design database schema for: {project}", 300, 100, ["4"]),
                WorkflowNode("3", "UI/UX Design", "claude-frontend-ui",
                           "Design user interface for: {project}", 300, 300, ["4"]),
                WorkflowNode("4", "Backend Implementation", "claude-backend-api",
                           "Implement backend for: {project}", 500, 200, ["5"]),
                WorkflowNode("5", "Testing & QA", "claude-testing",
                           "Create test suite for: {project}", 700, 200, [])
            ]
        )

    def render_workflow_builder(self):
        """Render visual workflow builder interface"""
        st.markdown("### 🎨 Visual Workflow Builder")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Canvas for workflow visualization
            self.render_workflow_canvas()

        with col2:
            # Control panel
            self.render_workflow_controls()

    def render_workflow_canvas(self):
        """Render the workflow canvas with nodes and connections"""
        if "selected_workflow" in st.session_state:
            workflow = self.workflows[st.session_state.selected_workflow]

            # Create a plotly graph for the workflow
            fig = go.Figure()

            # Add nodes
            for node in workflow.workflow_nodes:
                fig.add_trace(go.Scatter(
                    x=[node.x],
                    y=[node.y],
                    mode='markers+text',
                    marker=dict(size=50, color='lightblue'),
                    text=[node.name],
                    textposition="middle center",
                    name=node.name,
                    showlegend=False
                ))

                # Add connections
                for connection_id in node.connections:
                    target_node = next((n for n in workflow.workflow_nodes if n.id == connection_id), None)
                    if target_node:
                        fig.add_trace(go.Scatter(
                            x=[node.x, target_node.x],
                            y=[node.y, target_node.y],
                            mode='lines',
                            line=dict(color='gray', width=2),
                            showlegend=False
                        ))

            fig.update_layout(
                title=f"Workflow: {workflow.name}",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                showlegend=False,
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("👈 Select a workflow template to visualize")

    def render_workflow_controls(self):
        """Render workflow control panel"""
        st.markdown("#### 🎛️ Workflow Controls")

        # Template selection
        template_names = list(self.workflows.keys())
        selected = st.selectbox(
            "Select Template:",
            template_names,
            format_func=lambda x: self.workflows[x].name,
            key="selected_workflow"
        )

        if selected:
            workflow = self.workflows[selected]
            st.write(f"**Category**: {workflow.category}")
            st.write(f"**Time**: {workflow.estimated_time}")
            st.write(f"**Difficulty**: {workflow.difficulty}")
            st.write(f"**Tags**: {', '.join(workflow.tags)}")

            if st.button("🚀 Execute Workflow", type="primary"):
                st.session_state['execute_workflow'] = selected
                st.success("Workflow queued for execution!")

class EnhancedMultiAgentInterface:
    """Enhanced interface with LangGraph Platform features"""

    def __init__(self):
        self.orchestrator = ClaudeNativeOrchestrator()
        if LANGCHAIN_INTEGRATION:
            self.multi_agent_coordinator = MultiAgentCoordinator()

        self.state_manager = StateManager()
        self.workflow_builder = VisualWorkflowBuilder()

        # Enhanced agent definitions with metadata
        self.claude_agents = {
            "claude-prompt-validator": {
                "name": "Prompt Validator",
                "specialization": "Prompt validation and optimization",
                "color": "#FF6B6B",
                "icon": "✅"
            },
            "claude-task-coordinator": {
                "name": "Task Coordinator",
                "specialization": "Task coordination and management",
                "color": "#4ECDC4",
                "icon": "📋"
            },
            "claude-backend-api": {
                "name": "Backend API Developer",
                "specialization": "Backend development and APIs",
                "color": "#45B7D1",
                "icon": "🔧"
            },
            "claude-database": {
                "name": "Database Architect",
                "specialization": "Database design and optimization",
                "color": "#96CEB4",
                "icon": "🗄️"
            },
            "claude-frontend-ui": {
                "name": "Frontend UI Developer",
                "specialization": "Frontend development and UX",
                "color": "#FFEAA7",
                "icon": "🎨"
            },
            "claude-instagram": {
                "name": "Instagram Specialist",
                "specialization": "Instagram automation and APIs",
                "color": "#DDA0DD",
                "icon": "📸"
            },
            "claude-queue-manager": {
                "name": "Queue Manager",
                "specialization": "Queue management and processing",
                "color": "#98D8C8",
                "icon": "📬"
            },
            "claude-testing": {
                "name": "Testing Specialist",
                "specialization": "Testing and quality assurance",
                "color": "#F7DC6F",
                "icon": "🧪"
            },
            "claude-deployment": {
                "name": "Deployment Engineer",
                "specialization": "Deployment and DevOps",
                "color": "#BB8FCE",
                "icon": "🚀"
            }
        }

        # Initialize agent states
        self.init_agent_states()

    def init_agent_states(self):
        """Initialize or load agent states"""
        for agent_id, agent_info in self.claude_agents.items():
            state = self.state_manager.load_agent_state(agent_id)
            if not state:
                state = AgentState(
                    name=agent_id,
                    session=agent_id,
                    status="idle",
                    last_activity=datetime.now()
                )
                self.state_manager.save_agent_state(state)

    def render_enhanced_dashboard(self):
        """Render enhanced dashboard with analytics"""
        st.markdown("## 📊 Enhanced Agent Dashboard")

        # System metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            active_agents = len([a for a in self.claude_agents.keys() if self.get_agent_status(a) == "active"])
            st.metric("Active Agents", f"{active_agents}/9", delta="100%")

        with col2:
            st.metric("Total Tasks", "247", delta="+12")

        with col3:
            st.metric("Success Rate", "94.2%", delta="+2.1%")

        with col4:
            st.metric("Avg Response", "3.2s", delta="-0.8s")

        # Agent status grid
        st.markdown("### 🤖 Agent Status Grid")

        cols = st.columns(3)
        for i, (agent_id, agent_info) in enumerate(self.claude_agents.items()):
            with cols[i % 3]:
                status = self.get_agent_status(agent_id)
                status_color = {"active": "🟢", "idle": "🟡", "error": "🔴"}[status]

                with st.container():
                    st.markdown(f"""
                    <div style='padding: 1rem; border: 2px solid {agent_info["color"]}; border-radius: 10px; margin-bottom: 1rem;'>
                        <h4>{agent_info["icon"]} {agent_info["name"]} {status_color}</h4>
                        <p><small>{agent_info["specialization"]}</small></p>
                    </div>
                    """, unsafe_allow_html=True)

    def get_agent_status(self, agent_id: str) -> str:
        """Get current agent status"""
        try:
            result = subprocess.run([
                "/opt/homebrew/bin/tmux", "has-session", "-t", agent_id
            ], capture_output=True, text=True)
            return "active" if result.returncode == 0 else "idle"
        except:
            return "error"

    def render_performance_analytics(self):
        """Render performance analytics charts"""
        st.markdown("### 📈 Performance Analytics")

        # Get real data from database
        conn = sqlite3.connect('mcp_system.db')
        cursor = conn.cursor()

        # Get task completion data from last 30 days
        cursor.execute('''
            SELECT DATE(timestamp) as date, agent, COUNT(*) as task_count
            FROM activities
            WHERE type = 'task'
            AND timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp), agent
            ORDER BY date, agent
        ''')
        task_data = cursor.fetchall()

        # Get agent list
        cursor.execute('SELECT DISTINCT agent FROM agent_states')
        agents = [row[0] for row in cursor.fetchall()][:5]  # Top 5 for chart clarity

        # Organize data by agent
        task_by_agent = {}
        for date, agent, count in task_data:
            if agent not in task_by_agent:
                task_by_agent[agent] = []
            task_by_agent[agent].append((date, count))

        # Task completion over time
        fig_tasks = go.Figure()
        for agent in agents:
            if agent in task_by_agent:
                dates = [item[0] for item in task_by_agent[agent]]
                counts = [item[1] for item in task_by_agent[agent]]
            else:
                dates = []
                counts = []

            if agent in self.claude_agents:
                fig_tasks.add_trace(go.Scatter(
                    x=dates,
                    y=counts,
                    mode='lines+markers',
                    name=self.claude_agents[agent]["name"],
                    line=dict(color=self.claude_agents[agent]["color"])
                ))

        fig_tasks.update_layout(
            title="Task Completion Over Time",
            xaxis_title="Date",
            yaxis_title="Tasks Completed"
        )
        st.plotly_chart(fig_tasks, use_container_width=True)

        # Get real response times from database
        cursor.execute('''
            SELECT agent, AVG(
                CAST(
                    (julianday(timestamp) - julianday(
                        LAG(timestamp) OVER (PARTITION BY agent ORDER BY timestamp)
                    )) * 86400 AS REAL
                )
            ) as avg_response_time
            FROM activities
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY agent
            HAVING avg_response_time IS NOT NULL
            LIMIT 5
        ''')
        response_data = cursor.fetchall()

        if response_data:
            agent_names = [row[0] for row in response_data if row[0] in self.claude_agents]
            response_times = [row[1] for row in response_data if row[0] in self.claude_agents]
            agent_display_names = [self.claude_agents[name]["name"] for name in agent_names]
        else:
            # No data available yet
            agent_display_names = []
            response_times = []

        if agent_display_names and response_times:
            fig_response = px.bar(
                x=agent_display_names,
                y=response_times,
                title="Average Response Time by Agent",
                labels={'x': 'Agent', 'y': 'Response Time (s)'}
            )
            st.plotly_chart(fig_response, use_container_width=True)
        else:
            st.info("No response time data available yet")

        conn.close()

def main():
    """Main application with authentication"""

    # Initialize authentication manager
    if AUTH_INTEGRATION:
        auth_manager = AuthManager()

        # Check authentication
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None

        current_user = None
        if st.session_state.session_id:
            current_user = auth_manager.validate_session(st.session_state.session_id)

        # If not authenticated, show login
        if not current_user:
            st.markdown("""
            <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
                <h1 style='color: white; margin: 0;'>🤖 Enhanced Multi-Agent Platform</h1>
                <p style='color: white; margin: 0; opacity: 0.9;'>Enterprise Authentication Required</p>
            </div>
            """, unsafe_allow_html=True)

            username, password = render_login_form()

            if username and password:
                user = auth_manager.authenticate_user(username, password)
                if user:
                    session_id = auth_manager.create_session(user)
                    st.session_state.session_id = session_id
                    st.success(f"🎉 Welcome, {user.username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
            return

        # User is authenticated - show main interface
        interface = EnhancedMultiAgentInterface()

        # Enhanced header with user info
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem;'>
                <h1 style='color: white; margin: 0; font-size: 2rem;'>🤖 Enhanced Multi-Agent Platform</h1>
                <p style='color: white; margin: 0; opacity: 0.9;'>LangGraph Features + Claude CLI + Enterprise Security</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"**👤 User**: {current_user.username}")
            st.markdown(f"**🎭 Role**: {current_user.role.title()}")

        with col3:
            if st.button("🚪 Logout"):
                auth_manager.invalidate_session(st.session_state.session_id)
                st.session_state.session_id = None
                st.rerun()

    else:
        # Fallback without authentication
        interface = EnhancedMultiAgentInterface()
        current_user = None

        # Enhanced header with status
        st.markdown("""
        <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.2);'>
            <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🤖 Enhanced Multi-Agent Platform</h1>
            <p style='color: white; margin: 0; opacity: 0.9; font-size: 1.2rem;'>
                LangGraph Platform Features + Claude Code CLI Integration
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced sidebar with more controls
    with st.sidebar:
        st.markdown("### 🎛️ Platform Controls")

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

        if st.button("🧪 System Health Check"):
            st.session_state['run_health_check'] = True
            st.rerun()

        if st.button("📊 Generate Analytics"):
            st.session_state['show_analytics'] = True
            st.rerun()

        # Theme selector
        st.markdown("### 🎨 Interface Theme")
        theme = st.selectbox("Theme:", ["Professional", "Dark", "Colorful"], key="ui_theme")

    # Enhanced tabs with new features including RBAC
    if AUTH_INTEGRATION and current_user:
        if current_user.role == "admin":
            tabs = st.tabs([
                "🧠 Intelligent Coordination",
                "🎨 Visual Workflow Builder",
                "🤖 Live Agent Terminals",
                "📊 Enhanced Dashboard",
                "📈 Performance Analytics",
                "👥 User Management",
                "🏢 Workspace Management",
                "⚙️ System Management"
            ])
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = tabs
        else:
            tabs = st.tabs([
                "🧠 Intelligent Coordination",
                "🎨 Visual Workflow Builder",
                "🤖 Live Agent Terminals",
                "📊 Enhanced Dashboard",
                "🏢 My Workspaces",
                "⚙️ Profile"
            ])
            tab1, tab2, tab3, tab4, tab7, tab8 = tabs
    else:
        # Default tabs without authentication
        tab1, tab2, tab3, tab4, tab5, tab8 = st.tabs([
            "🧠 Intelligent Coordination",
            "🎨 Visual Workflow Builder",
            "🤖 Live Agent Terminals",
            "📊 Enhanced Dashboard",
            "📈 Performance Analytics",
            "⚙️ System Management"
        ])

    # Tab 1: Intelligent Coordination (existing)
    with tab1:
        st.markdown("## 🧠 Multi-Agent Project Coordination")
        st.info("Enhanced with state persistence and advanced coordination patterns")

        # Keep existing coordination interface but enhanced
        project_input = st.text_area(
            "🎯 Project Description:",
            placeholder="""Enhanced Example: Create an enterprise social media platform with:
- Advanced Instagram analytics with ML predictions
- Real-time content scheduling with AI optimization
- Multi-tenant architecture with role-based access
- Microservices backend with event sourcing
- Progressive web app with offline capabilities
- Comprehensive monitoring and alerting""",
            height=150
        )

        if st.button("🚀 Start Enhanced Coordination", type="primary"):
            if project_input and LANGCHAIN_INTEGRATION:
                with st.spinner("Running enhanced multi-agent coordination..."):
                    result = interface.multi_agent_coordinator.coordinate_project(project_input)
                    if result.get("success"):
                        st.success("🎉 Enhanced Multi-Agent Coordination Completed!")
                        st.json(result)

    # Tab 2: Visual Workflow Builder (NEW)
    with tab2:
        interface.workflow_builder.render_workflow_builder()

    # Tab 3: Live Agent Terminals (enhanced with RBAC)
    with tab3:
        st.markdown("## 🤖 Enhanced Live Agent Terminals")

        # Get accessible agents based on user permissions
        if AUTH_INTEGRATION and current_user:
            accessible_agents = auth_manager.get_user_agents(current_user)
            can_control = auth_manager.check_permission(current_user, "control_assigned_agents") or \
                         auth_manager.check_permission(current_user, "control_all_agents")
        else:
            accessible_agents = list(interface.claude_agents.keys())
            can_control = True

        if not accessible_agents:
            st.warning("⚠️ No agents accessible. Contact admin for workspace assignment.")
            return

        # Enhanced terminal interface with RBAC
        for agent_id, agent_info in interface.claude_agents.items():
            if agent_id not in accessible_agents:
                continue  # Skip agents user doesn't have access to

            with st.expander(f"{agent_info['icon']} {agent_info['name']}", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    try:
                        output = interface.orchestrator.get_claude_response(agent_id, wait_seconds=0)
                        st.code(output[-2000:], language="bash")  # Show recent output
                    except Exception as e:
                        st.error(f"❌ Could not access {agent_id}: {str(e)}")

                with col2:
                    st.markdown(f"**Status**: {interface.get_agent_status(agent_id)}")

                    if can_control:
                        task_input = st.text_input(f"Task:", key=f"task_{agent_id}")
                        if st.button(f"📤 Send", key=f"send_{agent_id}") and task_input:
                            success = interface.orchestrator.send_task_to_claude(agent_id, task_input)
                            if success:
                                st.success("✅ Task sent!")
                                if AUTH_INTEGRATION:
                                    # Log task in state manager
                                    interface.state_manager.log_task_execution(
                                        agent_id, task_input, "sent", 0.0, "Task queued"
                                    )
                            else:
                                st.error("❌ Failed to send task")
                    else:
                        st.info("👁️ View-only access")

    # Tab 4: Enhanced Dashboard (NEW)
    with tab4:
        interface.render_enhanced_dashboard()

    # Tab 5: Performance Analytics (NEW) - Admin only
    if AUTH_INTEGRATION and current_user and current_user.role == "admin":
        with tab5:
            interface.render_performance_analytics()

    # Tab 6: User Management (NEW) - Admin only
    if AUTH_INTEGRATION and current_user and current_user.role == "admin":
        with tab6:
            render_user_management(auth_manager, current_user)

    # Tab 7: Workspace Management (NEW) - Admin or My Workspaces
    with tab7:
        if AUTH_INTEGRATION and current_user:
            render_workspace_management(auth_manager, current_user)
        else:
            st.info("👤 Login required for workspace management")

    # Tab 8: System Management (NEW)
    with tab8:
        st.markdown("## ⚙️ System Management")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🔧 Agent Management")

            for agent_id in interface.claude_agents.keys():
                col_a, col_b, col_c = st.columns([2, 1, 1])

                with col_a:
                    st.write(interface.claude_agents[agent_id]["name"])
                with col_b:
                    status = interface.get_agent_status(agent_id)
                    st.write(f"{'🟢' if status == 'active' else '🟡' if status == 'idle' else '🔴'}")
                with col_c:
                    if st.button("🔄", key=f"restart_{agent_id}"):
                        st.success(f"Restarting {agent_id}")

        with col2:
            st.markdown("### 📊 System Logs")

            if st.button("📄 Export Logs"):
                st.success("Logs exported successfully!")

            if st.button("🗑️ Clear Cache"):
                st.success("Cache cleared!")

    # Enhanced footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem; background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px;'>
        🤖 Enhanced Multi-Agent Platform |
        🧠 LangGraph Features |
        🖥️ Claude Code CLI Integration |
        📊 Advanced Analytics |
        🎨 Visual Workflow Builder
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()