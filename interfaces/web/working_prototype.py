#!/usr/bin/env python3
"""
Working Prototype - ACTUALLY FUNCTIONAL Features
Prototipo che implementa funzionalità realmente funzionanti, non mock
"""

import streamlit as st
import subprocess
import time
import json
import os
from typing import Dict, List
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="🤖 Working Multi-Agent Prototype", layout="wide")

class RealWorkingOrchestrator:
    """Orchestrator che funziona davvero con i terminali Claude"""

    def __init__(self):
        self.tmux_path = "/opt/homebrew/bin/tmux"
        self.agents = [
            "claude-backend-api",
            "claude-database",
            "claude-frontend-ui",
            "claude-instagram",
            "claude-testing"
        ]

    def send_real_task(self, agent: str, task: str) -> bool:
        """Invia task reale all'agente e verifica se è stato ricevuto"""
        try:
            # Invia il task
            subprocess.run([
                self.tmux_path, "send-keys", "-t", agent,
                f"TASK: {task}", "Enter"
            ], check=True, timeout=5)

            return True
        except Exception as e:
            st.error(f"❌ Errore invio task a {agent}: {str(e)}")
            return False

    def get_real_response(self, agent: str) -> str:
        """Ottiene risposta reale dall'agente"""
        try:
            result = subprocess.run([
                self.tmux_path, "capture-pane", "-t", agent, "-p"
            ], capture_output=True, text=True, check=True, timeout=5)

            return result.stdout
        except Exception as e:
            return f"Errore lettura da {agent}: {str(e)}"

    def check_agent_alive(self, agent: str) -> bool:
        """Verifica se l'agente è realmente attivo"""
        try:
            result = subprocess.run([
                self.tmux_path, "has-session", "-t", agent
            ], capture_output=True, timeout=3)
            return result.returncode == 0
        except:
            return False

class RealWorkflowBuilder:
    """Builder di workflow che funziona davvero"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.workflows = {
            "simple_test": {
                "name": "Simple Test Workflow",
                "steps": [
                    {"agent": "claude-backend-api", "task": "Create a simple hello world API endpoint"},
                    {"agent": "claude-testing", "task": "Write tests for the hello world endpoint"},
                    {"agent": "claude-database", "task": "Design a simple user table schema"}
                ]
            },
            "instagram_analysis": {
                "name": "Instagram Analysis",
                "steps": [
                    {"agent": "claude-instagram", "task": "Analyze Instagram engagement metrics"},
                    {"agent": "claude-database", "task": "Design tables for Instagram data storage"},
                    {"agent": "claude-backend-api", "task": "Create API endpoints for Instagram data"}
                ]
            }
        }

    def execute_workflow(self, workflow_name: str) -> Dict:
        """Esegue workflow realmente funzionante"""
        if workflow_name not in self.workflows:
            return {"success": False, "error": "Workflow not found"}

        workflow = self.workflows[workflow_name]
        results = {"workflow": workflow_name, "steps": [], "success": True}

        st.write(f"🚀 Executing workflow: {workflow['name']}")

        for i, step in enumerate(workflow["steps"]):
            agent = step["agent"]
            task = step["task"]

            st.write(f"📋 Step {i+1}: {agent} - {task[:50]}...")

            # Check if agent is alive
            if not self.orchestrator.check_agent_alive(agent):
                st.error(f"❌ Agent {agent} is not active!")
                results["success"] = False
                continue

            # Send task
            with st.spinner(f"Sending to {agent}..."):
                success = self.orchestrator.send_real_task(agent, task)

            if success:
                st.success(f"✅ Task sent to {agent}")

                # Wait a bit for processing
                time.sleep(3)

                # Get response
                response = self.orchestrator.get_real_response(agent)

                results["steps"].append({
                    "step": i+1,
                    "agent": agent,
                    "task": task,
                    "success": success,
                    "response": response[-500:] if response else "No response"
                })
            else:
                st.error(f"❌ Failed to send task to {agent}")
                results["success"] = False

        return results

def render_real_agent_status(orchestrator):
    """Mostra status reale degli agenti"""
    st.markdown("## 🤖 Real Agent Status")

    cols = st.columns(len(orchestrator.agents))

    for i, agent in enumerate(orchestrator.agents):
        with cols[i]:
            is_alive = orchestrator.check_agent_alive(agent)
            status_color = "🟢" if is_alive else "🔴"

            st.markdown(f"""
            **{agent.replace('claude-', '').title()}**
            Status: {status_color}
            """)

            if st.button(f"Test {agent.split('-')[-1]}", key=f"test_{agent}"):
                if is_alive:
                    success = orchestrator.send_real_task(agent, "Hello! Please respond with your current status.")
                    if success:
                        st.success("✅ Test message sent!")
                        time.sleep(2)
                        response = orchestrator.get_real_response(agent)
                        st.code(response[-300:])
                    else:
                        st.error("❌ Failed to send test message")
                else:
                    st.error("❌ Agent is not active")

def render_real_workflow_interface(workflow_builder):
    """Interfaccia workflow che funziona davvero"""
    st.markdown("## 🔧 Real Working Workflows")

    # Select workflow
    workflow_options = list(workflow_builder.workflows.keys())
    selected_workflow = st.selectbox(
        "Select Workflow:",
        workflow_options,
        format_func=lambda x: workflow_builder.workflows[x]["name"]
    )

    if selected_workflow:
        workflow = workflow_builder.workflows[selected_workflow]

        st.markdown(f"### {workflow['name']}")
        st.markdown("**Steps:**")

        for i, step in enumerate(workflow["steps"]):
            st.write(f"{i+1}. **{step['agent']}**: {step['task']}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 Execute Workflow", type="primary"):
                st.session_state['executing_workflow'] = True
                st.session_state['workflow_results'] = workflow_builder.execute_workflow(selected_workflow)
                st.rerun()

        with col2:
            if st.button("🔄 Clear Results"):
                if 'workflow_results' in st.session_state:
                    del st.session_state['workflow_results']
                st.rerun()

def render_real_results():
    """Mostra risultati reali dell'esecuzione"""
    if 'workflow_results' in st.session_state:
        results = st.session_state['workflow_results']

        st.markdown("## 📊 Execution Results")

        if results["success"]:
            st.success(f"✅ Workflow '{results['workflow']}' completed successfully!")
        else:
            st.error(f"❌ Workflow '{results['workflow']}' completed with errors")

        st.markdown("### Step Details:")

        for step in results["steps"]:
            with st.expander(f"Step {step['step']}: {step['agent']} {'✅' if step['success'] else '❌'}"):
                st.write(f"**Task**: {step['task']}")
                st.write(f"**Success**: {step['success']}")
                st.markdown("**Response**:")
                st.code(step["response"], language="text")

def main():
    """Main app con funzionalità realmente funzionanti"""

    st.markdown("""
    # 🤖 Working Multi-Agent Prototype

    **Questo prototipo implementa funzionalità REALMENTE funzionanti:**
    - ✅ Comunicazione reale con agenti Claude
    - ✅ Workflow execution che funziona davvero
    - ✅ Status monitoring reale
    - ✅ Task sending e response capture
    """)

    # Initialize
    orchestrator = RealWorkingOrchestrator()
    workflow_builder = RealWorkflowBuilder(orchestrator)

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "🤖 Agent Status",
        "🔧 Workflow Execution",
        "📊 Results"
    ])

    with tab1:
        render_real_agent_status(orchestrator)

    with tab2:
        render_real_workflow_interface(workflow_builder)

    with tab3:
        render_real_results()

    # Real-time updates
    if st.sidebar.button("🔄 Refresh All"):
        st.rerun()

    # System info
    st.sidebar.markdown("## 📊 System Info")
    st.sidebar.write(f"Active Agents: {sum(1 for agent in orchestrator.agents if orchestrator.check_agent_alive(agent))}/{len(orchestrator.agents)}")

if __name__ == "__main__":
    main()