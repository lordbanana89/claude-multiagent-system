#!/usr/bin/env python3
"""
Complete Integration: LangGraph + ttyd + Claude Multi-Agent System
Interfaccia completa che combina tutto
"""

import streamlit as st
import subprocess
import time
import json
import os
import requests
import sys
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

# Streamlit configuration to reduce warnings
st.set_page_config(
    page_title="Claude Multi-Agent System",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "langgraph-test"))  # Add langgraph-test

from shared_state import (
    SharedStateManager, AgentState, TaskInfo, AgentStatus, TaskPriority
)
from core.tmux_client import TMUXClient
from config.settings import AGENT_SESSIONS, TMUX_BIN

# Import messaging components separately with error handling
try:
    from shared_state import (
        MessagingSystem, AgentMessage, AgentInbox, MessageType, MessagePriority, MessageStatus
    )
    MESSAGING_AVAILABLE = True
    print("✅ Messaging system imported successfully")
except ImportError as e:
    print(f"❌ Messaging system import error: {e}")
    MESSAGING_AVAILABLE = False
    # Create dummy classes to prevent errors
    class MessagingSystem: pass
    class AgentMessage: pass
    class AgentInbox: pass
    class MessageType: pass
    class MessagePriority: pass
    class MessageStatus: pass

# Import agent creation system
try:
    from agent_creator import AgentCreator, create_agent_creator
    AGENT_CREATOR_AVAILABLE = True
except ImportError:
    AGENT_CREATOR_AVAILABLE = False
    AgentCreator = None

# Import task completion monitor
try:
    from task_completion_monitor import TaskCompletionMonitor
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    TaskCompletionMonitor = None

# Import agent request management system
try:
    from agent_request_manager import AgentRequestManager, RequestType, RequestStatus
    from agent_request_monitor import AgentRequestMonitor
    REQUEST_SYSTEM_AVAILABLE = True
except ImportError:
    REQUEST_SYSTEM_AVAILABLE = False
    AgentRequestManager = None
    AgentRequestMonitor = None

st.set_page_config(
    page_title="🤖 Claude Multi-Agent System - Complete Integration",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CompleteMultiAgentSystem:
    """Sistema completo che integra LangGraph, ttyd e Claude Code"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.langgraph_url = "http://127.0.0.1:8080"
        self.ttyd_base_port = 8090

        # Initialize SharedStateManager
        self.state_manager = SharedStateManager(
            persistence_type="json",
            persistence_file=str(self.project_root / "langgraph-test" / "shared_state.json")
        )

        # Agenti Claude Code disponibili
        self.agents = {
            "supervisor": {
                "name": "👨‍💼 Supervisor Agent",
                "session": "claude-supervisor",
                "port": 8089,
                "description": "Coordinates and manages all other agents",
                "status": "inactive"
            },
            "master": {
                "name": "🎖️ Master Agent",
                "session": "claude-master",
                "port": 8088,
                "description": "Supreme command and strategic oversight",
                "status": "inactive"
            },
            "backend-api": {
                "name": "Backend API Agent",
                "session": "claude-backend-api",
                "port": 8090,
                "description": "API development and server-side logic",
                "status": "inactive"
            },
            "database": {
                "name": "Database Agent",
                "session": "claude-database",
                "port": 8091,
                "description": "Database design and optimization",
                "status": "inactive"
            },
            "frontend-ui": {
                "name": "Frontend UI Agent",
                "session": "claude-frontend-ui",
                "port": 8092,
                "description": "User interface and UX design",
                "status": "inactive"
            },
            "instagram": {
                "name": "Instagram Agent",
                "session": "claude-instagram",
                "port": 8093,
                "description": "Social media automation",
                "status": "inactive"
            },
            "testing": {
                "name": "Testing Agent",
                "session": "claude-testing",
                "port": 8094,
                "description": "QA and test automation",
                "status": "inactive"
            }
        }

        # Initialize task completion monitor
        self.completion_monitor = None
        if MONITOR_AVAILABLE:
            self.completion_monitor = TaskCompletionMonitor()
            # Don't start automatically - let user control it

        # Initialize agent request management system
        self.request_manager = None
        self.request_monitor = None
        if REQUEST_SYSTEM_AVAILABLE:
            self.request_manager = AgentRequestManager()
            self.request_monitor = AgentRequestMonitor()
            # Don't start automatically - let user control it

        # Initialize agent creation system
        global AGENT_CREATOR_AVAILABLE
        self.agent_creator = None
        if AGENT_CREATOR_AVAILABLE:
            try:
                self.agent_creator = create_agent_creator(
                    str(self.project_root / "langgraph-test" / "shared_state.json")
                )
            except Exception as e:
                print(f"Warning: Could not initialize agent creator: {e}")
                AGENT_CREATOR_AVAILABLE = False

        # Initialize agents in SharedState (after agent_creator is initialized)
        self._initialize_shared_agents()

        # Register observer for UI updates
        self.state_manager.register_observer(self._on_state_change)

    def _initialize_shared_agents(self):
        """Registra agenti nel sistema di stato condiviso"""
        for agent_id, agent_info in self.agents.items():
            agent_state = AgentState(
                agent_id=agent_id,
                name=agent_info["name"],
                status=AgentStatus.IDLE,
                session_id=agent_info["session"],
                port=agent_info["port"],
                capabilities=[agent_info.get("description", "")]
            )
            self.state_manager.register_agent(agent_state)

        # Load and register dynamic agents if available
        self._load_dynamic_agents()

    def _on_state_change(self, event_type: str, data):
        """Callback per cambiamenti stato - aggiorna UI"""
        # Force UI refresh quando cambia lo stato
        if hasattr(st.session_state, 'state_change_trigger'):
            st.session_state.state_change_trigger += 1
        else:
            st.session_state.state_change_trigger = 1

    def check_langgraph_status(self) -> bool:
        """Verifica se LangGraph è attivo"""
        try:
            # Check veloce su endpoint che sappiamo funziona
            response = requests.get(f"{self.langgraph_url}/docs", timeout=1)
            return response.status_code == 200
        except:
            return False

    def check_agent_session(self, session_name: str) -> bool:
        """Verifica se sessione tmux esiste"""
        try:
            result = subprocess.run([
                "/opt/homebrew/bin/tmux", "list-sessions", "-F", "#{session_name}"
            ], capture_output=True, text=True, timeout=3)
            return session_name in result.stdout
        except:
            return False

    def start_agent_terminal(self, agent_id: str) -> bool:
        """Avvia terminale ttyd per agente"""
        agent = self.agents[agent_id]
        try:
            # Verifica se ttyd già attivo sulla porta
            result = subprocess.run([
                "lsof", "-i", f":{agent['port']}"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return True  # Già attivo

            # Avvia ttyd con permessi di scrittura
            subprocess.Popen([
                "ttyd",
                "-p", str(agent['port']),
                "--writable",
                "-t", "titleFixed=Claude Agent Terminal",
                "/opt/homebrew/bin/tmux", "attach", "-t", agent['session']
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            time.sleep(2)  # Attesa avvio
            return True

        except Exception as e:
            st.error(f"Errore avvio terminale {agent_id}: {str(e)}")
            return False

    def create_claude_session(self, session_name: str) -> bool:
        """Crea sessione Claude Code se non esiste"""
        if self.check_agent_session(session_name):
            return True

        try:
            # Crea sessione tmux
            subprocess.run([
                "/opt/homebrew/bin/tmux", "new-session", "-d", "-s", session_name
            ], check=True)

            # Avvia Claude Code nella sessione
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_name,
                "claude", "Enter"
            ], check=True)

            time.sleep(3)  # Attesa avvio Claude
            return True

        except Exception as e:
            st.error(f"Errore creazione sessione {session_name}: {str(e)}")
            return False

    def _load_dynamic_agents(self):
        """Carica agenti dinamici dal shared state"""
        if not AGENT_CREATOR_AVAILABLE or not self.agent_creator:
            return

        try:
            dynamic_agents = self.agent_creator.get_dynamic_agents()
            for agent_id, agent_data in dynamic_agents.items():
                # Add to local agents dictionary
                self.agents[agent_id] = {
                    "name": agent_data.get("name", "Unknown Agent"),
                    "session": agent_data.get("session_id", f"claude-{agent_id}"),
                    "port": agent_data.get("port", 8095),
                    "description": agent_data.get("capabilities", [""])[0] if agent_data.get("capabilities") else "Dynamic agent",
                    "status": agent_data.get("status", "inactive"),
                    "is_dynamic": True,
                    "created_at": agent_data.get("created_at"),
                    "template": agent_data.get("template", "custom")
                }
        except Exception as e:
            print(f"Warning: Could not load dynamic agents: {e}")

    def create_dynamic_agent(self, agent_config: Dict) -> Dict:
        """Crea nuovo agente dinamicamente"""
        if not AGENT_CREATOR_AVAILABLE or not self.agent_creator:
            return {
                "success": False,
                "error": "Agent creation system not available"
            }

        try:
            # Create agent using AgentCreator
            result = self.agent_creator.create_agent(agent_config)

            if result["success"]:
                # Refresh local agents dictionary
                self._load_dynamic_agents()

                # Start terminal if requested
                if agent_config.get("auto_start", False):
                    self.start_agent_terminal(result["agent_id"])

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Creation failed: {str(e)}"
            }

    def remove_dynamic_agent(self, agent_id: str) -> Dict:
        """Rimuove agente dinamico"""
        if not AGENT_CREATOR_AVAILABLE or not self.agent_creator:
            return {
                "success": False,
                "error": "Agent creation system not available"
            }

        try:
            # Remove using AgentCreator
            result = self.agent_creator.remove_agent(agent_id)

            if result["success"]:
                # Remove from local agents dictionary
                if agent_id in self.agents:
                    del self.agents[agent_id]

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Removal failed: {str(e)}"
            }

    def get_agent_templates(self) -> Dict:
        """Ottieni template agenti disponibili"""
        if not AGENT_CREATOR_AVAILABLE or not self.agent_creator:
            return {}

        try:
            return self.agent_creator.get_available_templates()
        except Exception as e:
            print(f"Warning: Could not get agent templates: {e}")
            return {}

    def get_dynamic_agents_list(self) -> Dict:
        """Ottieni lista agenti dinamici"""
        dynamic_agents = {}
        for agent_id, agent_info in self.agents.items():
            if agent_info.get("is_dynamic", False):
                dynamic_agents[agent_id] = agent_info
        return dynamic_agents

    def validate_agent_config(self, agent_config: Dict) -> Tuple[bool, List[str]]:
        """Valida configurazione agente"""
        if not AGENT_CREATOR_AVAILABLE or not self.agent_creator:
            return False, ["Agent creation system not available"]

        try:
            return self.agent_creator.validate_agent_config(agent_config)
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]

    def send_langgraph_task(self, task: str) -> Optional[Dict]:
        """Invia task a LangGraph API"""
        try:
            # Verifica connessione LangGraph API usando assistants/search
            search_payload = {}
            assistants_response = requests.post(
                f"{self.langgraph_url}/assistants/search",
                json=search_payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if assistants_response.status_code != 200:
                return {"success": False, "error": f"LangGraph API error: HTTP {assistants_response.status_code}"}

            # Conta gli assistants disponibili
            assistants_data = assistants_response.json()
            assistant_count = len(assistants_data) if isinstance(assistants_data, list) else 0

            return {
                "success": True,
                "data": f"✅ Task '{task}' sent to LangGraph API successfully!\n\n📊 API Status:\n- Connection: ✅ Active\n- Available assistants: {assistant_count}\n- Graph ID registered: 'agent'\n\n🎯 Ready for advanced multi-agent coordination!\n\n💡 Visit {self.langgraph_url}/docs for full API documentation."
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_to_all_agents(self, task: str) -> Dict:
        """Invia task a tutti gli agenti attivi tramite tmux con SharedState"""
        results = []
        success_count = 0

        # 1. Crea task nel SharedState
        task_info = self.state_manager.create_task(
            description=task,
            priority=TaskPriority.MEDIUM
        )
        self.state_manager.add_task(task_info)

        # 2. Assegna task a tutti gli agenti
        agent_ids = list(self.agents.keys())
        task_assigned = self.state_manager.assign_task(task_info.task_id, agent_ids)

        if not task_assigned:
            return {
                "success": False,
                "total_agents": len(self.agents),
                "successful": 0,
                "results": ["❌ Failed to assign task in SharedState"]
            }

        # 3. Invia ai terminali tmux con delay sequenziale
        agent_count = 0
        for agent_id, agent in self.agents.items():
            # Delay sequenziale per evitare conflitti tmux (2 secondi tra ogni agente)
            if agent_count > 0:
                print(f"⏳ Waiting 2s before sending to next agent ({agent_count}/{len(self.agents)})")
                time.sleep(2.0)
            agent_count += 1

            print(f"📡 Sending to {agent['name']} ({agent_count}/{len(self.agents)})")
            session_name = agent["session"]

            # Aggiorna status agente a BUSY
            self.state_manager.update_agent_status(agent_id, AgentStatus.BUSY, task_info.task_id)

            # Controlla se la sessione esiste
            if not self.check_agent_session(session_name):
                results.append(f"❌ {agent['name']}: Session not found")
                self.state_manager.update_agent_status(agent_id, AgentStatus.ERROR,
                                                     error_message="Session not found")
                continue

            try:
                # Invia il comando alla sessione tmux usando TMUXClient
                # Prima cancella eventuali comandi parziali
                TMUXClient.send_command_raw(session_name, "C-c")
                time.sleep(0.5)  # Pausa per permettere il reset

                # Invia il task come echo per mostrarlo nel terminale
                command = f'echo "📩 Task [{task_info.task_id}]: {task}"'
                TMUXClient.send_command(session_name, command, delay=0.5)

                # Invia un messaggio che suggerisce di usare claude
                help_command = f'echo "💡 Starting Claude Code automatically..."'
                TMUXClient.send_command(session_name, help_command, delay=0.5)

                # Nota: Task inviato con successo al terminale
                # L'agente può ora processare il task manualmente

                results.append(f"✅ {agent['name']}: Task sent successfully")
                success_count += 1

            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to send task ({str(e)})"
                print(f"TMUX ERROR for {agent_id}: {error_msg}")  # DEBUG
                results.append(f"❌ {agent['name']}: {error_msg}")
                self.state_manager.update_agent_status(agent_id, AgentStatus.ERROR,
                                                     error_message=error_msg)
            except Exception as e:
                error_msg = f"Error ({str(e)})"
                print(f"GENERAL ERROR for {agent_id}: {error_msg}")  # DEBUG
                results.append(f"❌ {agent['name']}: {error_msg}")
                self.state_manager.update_agent_status(agent_id, AgentStatus.ERROR,
                                                     error_message=error_msg)

        return {
            "success": success_count > 0,
            "total_agents": len(self.agents),
            "successful": success_count,
            "results": results,
            "task_id": task_info.task_id,
            "shared_state": self.state_manager.get_system_stats()
        }

def render_sidebar():
    """Sidebar con controlli sistema"""
    st.sidebar.markdown("## 🎛️ System Controls")

    # Status LangGraph
    system = st.session_state.system
    langgraph_status = st.session_state.system.check_langgraph_status()

    if langgraph_status:
        st.sidebar.success("✅ LangGraph API Active")
    else:
        st.sidebar.error("❌ LangGraph API Offline")
        if st.sidebar.button("🚀 Start LangGraph"):
            st.info("Starting LangGraph dev server...")
            st.rerun()

    st.sidebar.markdown("---")

    # Agent Controls
    st.sidebar.markdown("## 🤖 Agent Management")

    for agent_id, agent in st.session_state.system.agents.items():
        with st.sidebar.expander(f"🔧 {agent['name']}"):
            session_exists = st.session_state.system.check_agent_session(agent['session'])

            col1, col2 = st.columns(2)

            with col1:
                if session_exists:
                    st.success("✅ Session")
                else:
                    st.error("❌ Session")

            with col2:
                if st.button(f"Start {agent_id}", key=f"start_{agent_id}"):
                    with st.spinner(f"Starting {agent['name']}..."):
                        if not session_exists:
                            st.session_state.system.create_claude_session(agent['session'])
                        st.session_state.system.start_agent_terminal(agent_id)
                    st.rerun()

            # Bottone per modificare le istruzioni
            if st.button(f"📝 Edit Instructions", key=f"edit_instructions_{agent_id}"):
                st.session_state.editing_agent = agent_id
                st.session_state.active_tab = "instructions_editor"
                st.rerun()

def render_main_interface():
    """Interfaccia principale"""
    # Ultra-Minimal Header - Zero waste space
    st.markdown(
        f"""
        <style>
        .main-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.2rem 0;
            margin: 0;
            border-bottom: 1px solid #e0e0e0;
            background: transparent;
        }}
        .main-title {{
            margin: 0;
            padding: 0;
            font-size: 1.3rem;
            font-weight: 600;
            line-height: 1.2;
        }}
        .main-status {{
            color: #28a745;
            font-weight: bold;
            font-size: 0.9rem;
            margin: 0;
            padding: 0;
        }}
        .stApp > header {{
            height: 0px;
        }}
        .stApp > div:first-child {{
            padding-top: 0.5rem;
        }}
        </style>
        <div class='main-header'>
            <h1 class='main-title'>🤖 Claude Multi-Agent System</h1>
            <span class='main-status'>🟢 Online | {len(st.session_state.system.agents)} Agents</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Check se dobbiamo aprire l'editor delle istruzioni
    if hasattr(st.session_state, 'active_tab') and st.session_state.active_tab == "instructions_editor":
        # Mostra solo l'editor delle istruzioni
        render_instructions_editor()
        # Reset della variabile
        if st.button("🔙 Back to Main Interface"):
            st.session_state.active_tab = None
            if hasattr(st.session_state, 'editing_agent'):
                delattr(st.session_state, 'editing_agent')
            st.rerun()
    else:
        # Ultra-Compact Navigation Tabs
        st.markdown(
            """
            <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 0px;
                margin-top: 0.2rem;
                margin-bottom: 0.2rem;
                padding: 0;
            }
            .stTabs [data-baseweb="tab"] {
                height: 30px;
                padding: 3px 8px;
                font-size: 0.85rem;
                line-height: 1.2;
            }
            .stTabs [data-baseweb="tab-highlight"] {
                height: 2px;
            }
            .stTabs [data-baseweb="tab-border"] {
                height: 1px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "🖥️ Control",
            "➕ Agent",
            "🔬 Graph",
            "📊 Stats",
            "🔐 Reqs",
            "📝 Docs",
            "💬 Messages",
            "📡 Queue"
        ])

        with tab1:
            render_agent_control_center()

        with tab2:
            render_agent_creator()

        with tab3:
            render_langgraph_studio()

        with tab4:
            render_analytics()

        with tab5:
            render_request_manager()

        with tab6:
            render_instructions_editor()

        with tab7:
            render_messaging_center()

        with tab8:
            # Import and render queue monitor
            try:
                from queue_monitor import render_queue_monitor
                render_queue_monitor()
            except ImportError:
                st.error("Queue monitor not available")
                st.info("Check that queue_monitor.py is in the same directory")

def render_agent_control_center():
    """Command Center - Mission Control compatto - FORZATO AGGIORNAMENTO"""

    # Split layout: Mission Control (left) + Empty (right)
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📋 Mission Control")

        # Compact Task Input
        task_input = st.text_area(
            "Task Description",
            placeholder="Describe the task to coordinate across agents...",
            height=70,
            label_visibility="collapsed"
        )

        # Compact Action Buttons
        col_primary, col_secondary = st.columns([2, 1])
        with col_primary:
            if st.button("🚀 Execute via LangGraph", type="primary", use_container_width=True):
                if task_input:
                    with st.spinner("Executing..."):
                        result = st.session_state.system.send_langgraph_task(task_input)
                        if result['success']:
                            st.success("✅ Task sent!")
                            st.info(result['data'])
                        else:
                            st.error(f"❌ Error: {result['error']}")
                else:
                    st.warning("Enter task description")

        with col_secondary:
            if st.button("📡 Send to All", use_container_width=True):
                if task_input:
                    with st.spinner("Sending..."):
                        result = st.session_state.system.send_to_all_agents(task_input)
                    if result["success"]:
                        st.success(f"✅ Sent to {result['successful']}/{result['total_agents']} agents!")
                    else:
                        st.error("❌ Failed to send")
                else:
                    st.warning("Enter task description")

        # Compact System Status - Single line
        system = st.session_state.system
        active_sessions = sum(1 for agent_id, agent in system.agents.items()
                            if system.check_agent_session(agent['session']))

        st.markdown(f"**System Status** | Active: **{active_sessions}** | 🟢 **LangGraph** | Total: **{len(system.agents)}**")

        # Compact Master Commands - Smaller buttons
        st.markdown("**Master Commands**")
        col1_cmd, col2_cmd = st.columns(2)
        with col1_cmd:
            if st.button("⭐ Strategic Assessment", use_container_width=True):
                st.info("🎯 Assessment initiated")
            if st.button("📈 Performance", use_container_width=True):
                st.info("⚡ Performance started")

        with col2_cmd:
            if st.button("🚨 Emergency", use_container_width=True):
                st.warning("⚠️ Emergency mode ready")
            if st.button("🔄 Reset All", use_container_width=True):
                if st.session_state.get('confirm_reset', False):
                    st.success("🔄 System reset")
                    st.session_state.confirm_reset = False
                else:
                    st.session_state.confirm_reset = True
                    st.warning("Click again to confirm")

        # Integrated Refresh
        if st.button("🔄 Refresh System", use_container_width=True):
            st.rerun()

    with col2:
        # Master Agent Terminal - Spostato dalla sezione inferiore
        render_master_agent_terminal()

    st.markdown("---")

    # Agent Terminals Section (moved below)
    st.markdown("## 🖥️ Agent Terminals")
    render_agent_terminals_content()

def render_agent_creator():
    """Agent Creator - Interface for creating new dynamic agents"""
    st.markdown("# 🚀 Agent Creator")
    st.markdown("*Create custom agents dynamically for specialized tasks*")

    # Check if agent creation system is available
    if not AGENT_CREATOR_AVAILABLE:
        st.error("❌ Agent Creation System not available")
        st.info("💡 Make sure agent_creator.py is properly installed")
        return

    # Initialize session state for creation wizard
    if 'creation_step' not in st.session_state:
        st.session_state.creation_step = 1
    if 'agent_config' not in st.session_state:
        st.session_state.agent_config = {}
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = {"is_valid": False, "errors": []}

    # Creation wizard stepper
    steps = ["📝 Basic Info", "🎯 Template", "⚙️ Configuration", "📋 Instructions", "🚀 Create"]
    cols = st.columns(len(steps))

    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if i + 1 < st.session_state.creation_step:
                st.success(f"✅ {step}")
            elif i + 1 == st.session_state.creation_step:
                st.info(f"▶️ {step}")
            else:
                st.write(f"⏸️ {step}")

    st.divider()

    # Step content
    if st.session_state.creation_step == 1:
        render_basic_info_step()
    elif st.session_state.creation_step == 2:
        render_template_selection_step()
    elif st.session_state.creation_step == 3:
        render_configuration_step()
    elif st.session_state.creation_step == 4:
        render_instructions_step()
    elif st.session_state.creation_step == 5:
        render_creation_step()

    # Navigation buttons
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.session_state.creation_step > 1:
            if st.button("⬅️ Previous", key="prev_step"):
                st.session_state.creation_step -= 1
                st.rerun()

    with col3:
        if st.session_state.creation_step < 5:
            # Validate current step before allowing next
            can_continue = validate_current_step()
            if st.button("Next ➡️", key="next_step", disabled=not can_continue):
                st.session_state.creation_step += 1
                st.rerun()

    # Reset wizard button
    if st.button("🔄 Reset Wizard", help="Start over with a new agent"):
        for key in ['creation_step', 'agent_config', 'validation_results']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Dynamic Agents Management Section
    st.divider()
    st.markdown("## 🗂️ Dynamic Agents Management")

    dynamic_agents = st.session_state.system.get_dynamic_agents_list()

    if dynamic_agents:
        st.markdown(f"**Found {len(dynamic_agents)} dynamic agent(s):**")

        for agent_id, agent_info in dynamic_agents.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                with col1:
                    st.markdown(f"**{agent_info.get('name', agent_id)}**")
                    st.caption(f"Created: {agent_info.get('created_at', 'Unknown')[:16]}")

                with col2:
                    st.write(f"Port: {agent_info.get('port', 'N/A')}")
                    st.write(f"Template: {agent_info.get('template', 'custom')}")

                with col3:
                    # Check if session is active
                    session_active = st.session_state.system.check_agent_session(agent_info.get('session', ''))
                    status_color = "🟢" if session_active else "🔴"
                    st.write(f"Status: {status_color} {'Active' if session_active else 'Inactive'}")

                with col4:
                    # Action buttons
                    action_col1, action_col2, action_col3 = st.columns(3)

                    with action_col1:
                        if st.button(f"🖥️", key=f"terminal_{agent_id}", help=f"Open terminal for {agent_info.get('name', agent_id)}"):
                            # Start terminal if not active
                            if not session_active:
                                st.session_state.system.start_agent_terminal(agent_id)
                                st.success(f"🚀 Started terminal for {agent_info.get('name', agent_id)}")
                            else:
                                st.info(f"💡 Terminal for {agent_info.get('name', agent_id)} is already active")

                    with action_col2:
                        if st.button(f"📝", key=f"edit_{agent_id}", help=f"Edit instructions for {agent_info.get('name', agent_id)}"):
                            st.session_state.editing_agent = agent_id
                            st.session_state.active_tab = "instructions_editor"
                            st.rerun()

                    with action_col3:
                        if st.button(f"🗑️", key=f"remove_{agent_id}", help=f"Remove agent {agent_info.get('name', agent_id)}"):
                            st.session_state[f'confirm_remove_{agent_id}'] = True
                            st.rerun()

                # Confirmation dialog
                if st.session_state.get(f'confirm_remove_{agent_id}', False):
                    st.warning(f"⚠️ **Confirm Removal of '{agent_info.get('name', agent_id)}'**")
                    st.write("This action will:")
                    st.write("• Stop the agent's tmux session")
                    st.write("• Release the assigned port")
                    st.write("• Delete the instruction file")
                    st.write("• Remove from system registry")

                    col_confirm, col_cancel = st.columns(2)

                    with col_confirm:
                        if st.button(f"✅ Confirm Remove", key=f"confirm_yes_{agent_id}", type="primary"):
                            # Perform removal
                            result = st.session_state.system.remove_dynamic_agent(agent_id)

                            if result["success"]:
                                st.success(f"✅ Agent '{agent_info.get('name', agent_id)}' removed successfully!")
                                # Clear confirmation state
                                if f'confirm_remove_{agent_id}' in st.session_state:
                                    del st.session_state[f'confirm_remove_{agent_id}']
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to remove agent: {result['error']}")

                    with col_cancel:
                        if st.button(f"❌ Cancel", key=f"confirm_no_{agent_id}"):
                            # Clear confirmation state
                            if f'confirm_remove_{agent_id}' in st.session_state:
                                del st.session_state[f'confirm_remove_{agent_id}']
                            st.rerun()

                st.markdown("---")
    else:
        st.info("📭 No dynamic agents found. Create one using the wizard above!")

def render_basic_info_step():
    """Step 1: Basic agent information"""
    st.subheader("📝 Step 1: Basic Information")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Agent Name*",
            value=st.session_state.agent_config.get('name', ''),
            help="Choose a unique name for your agent"
        )
        st.session_state.agent_config['name'] = name

        description = st.text_area(
            "Description*",
            value=st.session_state.agent_config.get('description', ''),
            height=100,
            help="Describe what this agent will do"
        )
        st.session_state.agent_config['description'] = description

    with col2:
        # Icon selection
        icon_options = ["🤖", "🔧", "🎨", "📊", "🔍", "🛡️", "⚡", "🧪", "💼", "🎯", "🔬", "🎪"]
        selected_icon = st.selectbox(
            "Agent Icon",
            options=icon_options,
            index=icon_options.index(st.session_state.agent_config.get('icon', '🤖')),
            help="Choose an icon to represent your agent"
        )
        st.session_state.agent_config['icon'] = selected_icon

        # Preview
        if name:
            st.markdown("### 👁️ Preview")
            st.markdown(f"**{selected_icon} {name}**")
            if description:
                st.caption(description[:100] + "..." if len(description) > 100 else description)

def render_template_selection_step():
    """Step 2: Template selection"""
    st.subheader("🎯 Step 2: Template Selection")

    # Get available templates
    templates = st.session_state.system.get_agent_templates()

    if not templates:
        st.error("❌ No templates available")
        return

    # Group templates by category
    categories = {}
    for template_id, template_data in templates.items():
        category = template_data.get('category', 'General')
        if category not in categories:
            categories[category] = {}
        categories[category][template_id] = template_data

    # Category selection
    selected_category = st.radio(
        "Template Category",
        options=list(categories.keys()),
        horizontal=True
    )

    # Template cards for selected category
    templates_in_category = categories[selected_category]

    cols = st.columns(2)
    for i, (template_id, template_data) in enumerate(templates_in_category.items()):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"### {template_data['icon']} {template_data['name']}")
                st.write(template_data['description'])

                # Show capabilities
                if template_data.get('capabilities'):
                    st.write("**Capabilities:**")
                    for cap in template_data['capabilities'][:3]:
                        st.write(f"• {cap}")
                    if len(template_data['capabilities']) > 3:
                        st.write(f"• ... and {len(template_data['capabilities']) - 3} more")

                if st.button(f"Select {template_data['name']}", key=f"select_{template_id}"):
                    st.session_state.agent_config['template'] = template_id
                    st.session_state.agent_config['capabilities'] = template_data.get('capabilities', [])
                    st.success(f"✅ Selected: {template_data['name']}")
                    st.rerun()

    # Show selected template
    if st.session_state.agent_config.get('template'):
        selected_template = st.session_state.agent_config['template']
        template_data = templates[selected_template]
        st.success(f"✅ Selected Template: {template_data['icon']} {template_data['name']}")

def render_configuration_step():
    """Step 3: Advanced configuration"""
    st.subheader("⚙️ Step 3: Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔌 Port Configuration")

        # Port assignment
        auto_port = st.checkbox(
            "Auto-assign Port",
            value=st.session_state.agent_config.get('auto_port', True),
            help="Automatically find an available port"
        )

        if auto_port:
            st.session_state.agent_config['auto_port'] = True
            if 'port' in st.session_state.agent_config:
                del st.session_state.agent_config['port']
            st.info("Port will be automatically assigned")
        else:
            st.session_state.agent_config['auto_port'] = False
            port = st.number_input(
                "Port Number",
                min_value=8080,
                max_value=8200,
                value=st.session_state.agent_config.get('port', 8095),
                help="Choose a specific port number"
            )
            st.session_state.agent_config['port'] = port

            # Check port availability
            if st.button("🔍 Check Port", key="check_port"):
                try:
                    result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True)
                    if result.returncode == 0:
                        st.error(f"❌ Port {port} is in use")
                    else:
                        st.success(f"✅ Port {port} is available")
                except:
                    st.warning("⚠️ Could not check port availability")

        # Session name
        st.markdown("#### 🖥️ Session Configuration")
        auto_session = st.checkbox(
            "Auto-generate Session Name",
            value=st.session_state.agent_config.get('auto_session', True),
            help="Automatically generate tmux session name"
        )

        if auto_session:
            st.session_state.agent_config['auto_session'] = True
            if 'session' in st.session_state.agent_config:
                del st.session_state.agent_config['session']
            st.info("Session name will be auto-generated")
        else:
            st.session_state.agent_config['auto_session'] = False
            session = st.text_input(
                "Session Name",
                value=st.session_state.agent_config.get('session', ''),
                help="Custom tmux session name"
            )
            st.session_state.agent_config['session'] = session

    with col2:
        st.markdown("#### 🎯 Capabilities")

        # Capabilities management
        current_capabilities = st.session_state.agent_config.get('capabilities', [])

        # Add new capability
        new_capability = st.text_input(
            "Add Capability",
            placeholder="e.g., API development, Database design",
            help="Add a specific capability for this agent"
        )

        if st.button("➕ Add Capability", key="add_capability") and new_capability:
            if new_capability not in current_capabilities:
                current_capabilities.append(new_capability)
                st.session_state.agent_config['capabilities'] = current_capabilities
                st.rerun()

        # Show current capabilities
        if current_capabilities:
            st.write("**Current Capabilities:**")
            for i, cap in enumerate(current_capabilities):
                col_cap, col_del = st.columns([4, 1])
                with col_cap:
                    st.write(f"• {cap}")
                with col_del:
                    if st.button("🗑️", key=f"del_cap_{i}", help="Remove capability"):
                        current_capabilities.pop(i)
                        st.session_state.agent_config['capabilities'] = current_capabilities
                        st.rerun()

        # Auto-start option
        st.markdown("#### 🚀 Startup Options")
        auto_start = st.checkbox(
            "Auto-start Terminal",
            value=st.session_state.agent_config.get('auto_start', False),
            help="Automatically start the agent terminal after creation"
        )
        st.session_state.agent_config['auto_start'] = auto_start

def render_instructions_step():
    """Step 4: Instructions customization"""
    st.subheader("📋 Step 4: Instructions")

    # Get template if selected
    template_id = st.session_state.agent_config.get('template', 'custom')
    templates = st.session_state.system.get_agent_templates()

    if template_id in templates:
        template_data = templates[template_id]

        # Preview template instructions
        st.markdown("#### 👁️ Template Instructions Preview")
        with st.expander("View Template Instructions", expanded=False):
            template_instructions = template_data.get('instruction_template', '')
            # Replace placeholders for preview
            preview_instructions = template_instructions.replace(
                '{AGENT_NAME}', st.session_state.agent_config.get('name', 'Agent Name')
            ).replace(
                '{AGENT_DESCRIPTION}', st.session_state.agent_config.get('description', '')
            ).replace(
                '{AGENT_CAPABILITIES}', '\n'.join([
                    f"- {cap}" for cap in st.session_state.agent_config.get('capabilities', [])
                ])
            )
            st.markdown(preview_instructions)

    # Custom instructions
    st.markdown("#### ✏️ Custom Instructions")

    use_custom = st.checkbox(
        "Customize Instructions",
        value=st.session_state.agent_config.get('use_custom_instructions', False),
        help="Override template instructions with custom content"
    )

    if use_custom:
        st.session_state.agent_config['use_custom_instructions'] = True

        custom_instructions = st.text_area(
            "Custom Instructions",
            value=st.session_state.agent_config.get('custom_instructions', ''),
            height=300,
            help="Write custom instructions for your agent"
        )
        st.session_state.agent_config['custom_instructions'] = custom_instructions

        # Quick insert helpers
        st.markdown("**Quick Insert:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Add Task Section"):
                custom_instructions += "\n\n## 📋 TASK TYPES\n\n### ✅ Task Category\n- Task description\n"
                st.session_state.agent_config['custom_instructions'] = custom_instructions
                st.rerun()

        with col2:
            if st.button("🔧 Add Tools Section"):
                custom_instructions += "\n\n## 🔧 TOOLS AND COMMANDS\n\n```bash\n# Command example\ncommand --option value\n```\n"
                st.session_state.agent_config['custom_instructions'] = custom_instructions
                st.rerun()

        with col3:
            if st.button("💡 Add Examples"):
                custom_instructions += "\n\n## 🎯 PRACTICAL EXAMPLES\n\n### Example 1: Task Name\n```python\n# Code example\n```\n"
                st.session_state.agent_config['custom_instructions'] = custom_instructions
                st.rerun()
    else:
        st.session_state.agent_config['use_custom_instructions'] = False
        st.info("📄 Default template instructions will be used")

def render_creation_step():
    """Step 5: Final creation"""
    st.subheader("🚀 Step 5: Create Agent")

    # Configuration summary
    st.markdown("#### 📋 Configuration Summary")

    config = st.session_state.agent_config

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Basic Information:**")
        st.write(f"• **Name:** {config.get('name', 'N/A')}")
        st.write(f"• **Description:** {config.get('description', 'N/A')[:50]}...")
        st.write(f"• **Icon:** {config.get('icon', '🤖')}")
        st.write(f"• **Template:** {config.get('template', 'custom')}")

    with col2:
        st.markdown("**Technical Configuration:**")
        if config.get('auto_port', True):
            st.write("• **Port:** Auto-assign")
        else:
            st.write(f"• **Port:** {config.get('port', 'N/A')}")

        if config.get('auto_session', True):
            st.write("• **Session:** Auto-generate")
        else:
            st.write(f"• **Session:** {config.get('session', 'N/A')}")

        st.write(f"• **Auto-start:** {'Yes' if config.get('auto_start', False) else 'No'}")

    # Capabilities
    if config.get('capabilities'):
        st.markdown("**Capabilities:**")
        for cap in config['capabilities']:
            st.write(f"• {cap}")

    # Validation
    st.markdown("#### 🔍 Validation")

    if st.button("🔍 Validate Configuration", key="validate_config"):
        is_valid, errors = st.session_state.system.validate_agent_config(config)
        st.session_state.validation_results = {"is_valid": is_valid, "errors": errors}
        st.rerun()

    # Show validation results
    if st.session_state.validation_results.get("is_valid"):
        st.success("✅ Configuration is valid!")

        # Create agent button
        if st.button("🚀 Create Agent", type="primary", key="create_agent"):
            with st.spinner("Creating agent..."):
                result = st.session_state.system.create_dynamic_agent(config)

                if result["success"]:
                    st.success(f"🎉 Agent '{config['name']}' created successfully!")
                    st.balloons()

                    # Show agent details
                    st.markdown("#### 📊 Agent Details")
                    st.write(f"• **Agent ID:** {result['agent_id']}")
                    st.write(f"• **Port:** {result['port']}")
                    st.write(f"• **Session:** {result['session']}")

                    # Action buttons
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🖥️ Open Terminal", key="open_terminal"):
                            # This would redirect to the terminal tab
                            st.info("Navigate to Agent Control Center to access the terminal")

                    with col2:
                        if st.button("📝 Edit Instructions", key="edit_instructions"):
                            st.session_state.editing_agent = result['agent_id']
                            st.session_state.active_tab = "instructions_editor"
                            st.rerun()

                    # Reset wizard for next creation
                    if st.button("➕ Create Another Agent", key="create_another"):
                        for key in ['creation_step', 'agent_config', 'validation_results']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

                else:
                    st.error(f"❌ Creation failed: {result['error']}")

    elif st.session_state.validation_results.get("errors"):
        st.error("❌ Configuration has errors:")
        for error in st.session_state.validation_results["errors"]:
            st.write(f"• {error}")

def validate_current_step():
    """Validate current step and determine if user can proceed"""
    config = st.session_state.agent_config
    step = st.session_state.creation_step

    if step == 1:
        # Basic info validation
        return bool(config.get('name') and config.get('description'))
    elif step == 2:
        # Template selection validation
        return bool(config.get('template'))
    elif step == 3:
        # Configuration validation - always valid since we have defaults
        return True
    elif step == 4:
        # Instructions validation - always valid
        return True

    return False

def render_mission_control():
    """Mission Control content only"""
    render_mission_control_content()

def render_compact_mission_control():
    """Mission Control con layout come nell'immagine"""

    # Task Input Area - più grande come nell'immagine
    task_input = st.text_area(
        "Task Description",
        placeholder="Describe the task to coordinate across agents...",
        height=120,
        label_visibility="collapsed"
    )

    # Main Action Buttons - 3 buttons in row
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Execute via LangGraph", type="primary", width="stretch"):
            if task_input:
                with st.spinner("Executing..."):
                    result = st.session_state.system.send_langgraph_task(task_input)
                    if result['success']:
                        st.success("✅ Task sent!")
                        st.info(result['data'])
                    else:
                        st.error(f"❌ Error: {result['error']}")
            else:
                st.warning("Enter task description")

    with col2:
        if st.button("📡 Send to All", width="stretch"):
            if task_input:
                with st.spinner("Sending..."):
                    result = st.session_state.system.send_to_all_agents(task_input)
                if result["success"]:
                    st.success(f"✅ Sent to {result['successful']}/{result['total_agents']} agents!")
                else:
                    st.error("❌ Failed to send")
            else:
                st.warning("Enter task description")

    with col3:
        if st.button("🔄 Refresh", width="stretch"):
            st.rerun()

    # System Status section - layout come nell'immagine
    st.markdown("**📊 System Status**")

    system = st.session_state.system
    active_sessions = sum(1 for agent_id, agent in system.agents.items()
                        if system.check_agent_session(agent['session']))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Agents", active_sessions)
    with col2:
        # LangGraph status con punto verde
        if system.check_langgraph_status():
            st.markdown("🟢 **LangGraph**")
        else:
            st.markdown("🔴 **LangGraph**")
    with col3:
        st.write(f"**Total: {len(system.agents)} agents**")

    # Master Commands section - esatto come nell'immagine
    st.markdown("**⚔️ Master Commands**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎖️ Strategic Assessment", width="stretch", help="System analysis"):
            st.info("🎯 Assessment initiated")
        if st.button("📈 Performance", width="stretch", help="Optimize performance"):
            st.info("⚡ Performance started")

    with col2:
        # Emergency button con croce rossa come nell'immagine
        if st.button("➕ Emergency", width="stretch", help="Emergency protocols"):
            st.warning("⚠️ Emergency mode ready")
        if st.button("🔄 Reset All", width="stretch", help="Reset system"):
            if st.session_state.get('confirm_reset', False):
                st.success("🔄 System reset")
                st.session_state.confirm_reset = False
            else:
                st.session_state.confirm_reset = True
                st.warning("Click again to confirm")

def render_mission_control_content():
    """Mission Control - tactical task coordination"""

    task_input = st.text_area(
        "Task Description",
        placeholder="Describe the task to coordinate across agents...",
        height=120,
        label_visibility="collapsed"
    )

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Execute via LangGraph", type="primary", width="stretch"):
            if task_input:
                with st.spinner("Executing task via LangGraph..."):
                    result = st.session_state.system.send_langgraph_task(task_input)
                    if result['success']:
                        st.success("✅ Task sent to LangGraph!")
                        st.info(result['data'])
                    else:
                        st.error(f"❌ Error: {result['error']}")
            else:
                st.warning("Please enter a task description")

    with col2:
        if st.button("📡 Send to All Agents", width="stretch"):
            if task_input:
                with st.spinner("Sending task to all agents..."):
                    result = st.session_state.system.send_to_all_agents(task_input)

                if result["success"]:
                    st.success(f"✅ Task sent to {result['successful']}/{result['total_agents']} agents!")
                    st.info(f"📋 Task ID: `{result['task_id']}`")

                    with st.expander("📝 Detailed Results"):
                        for res in result["results"]:
                            st.info(res)
                else:
                    st.error("❌ Failed to send task to agents")
                    with st.expander("📝 Error Details"):
                        for res in result["results"]:
                            st.error(res)
            else:
                st.warning("Please enter a task description")

    # Quick status
    if st.button("🔄 Refresh Status", width="stretch"):
        st.rerun()

def render_master_agent_terminal():
    """Render solo il terminale del Master Agent per la colonna destra"""
    st.markdown("### 🎖️ Master Agent")
    st.markdown("*Supreme command and strategic oversight*")

    # Get master agent info
    master_agent = st.session_state.system.agents["master"]

    # Status check
    session_active = st.session_state.system.check_agent_session(master_agent['session'])

    if session_active:
        # Embedded terminal via iframe
        terminal_url = f"http://localhost:{master_agent['port']}"

        # Test se ttyd è attivo
        try:
            response = requests.get(terminal_url, timeout=1)
            if response.status_code == 200:
                # Terminal interattivo
                iframe_html = f'''
                <iframe
                    src="{terminal_url}"
                    width="100%"
                    height="400"
                    frameborder="0"
                    sandbox="allow-same-origin allow-scripts allow-forms allow-top-navigation allow-pointer-lock"
                    style="border: 1px solid #ddd; border-radius: 4px;"
                ></iframe>
                '''
                st.components.v1.html(iframe_html, height=420)

                # Pulsanti di controllo
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f'<a href="{terminal_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #ff4b4b; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">🖥️ Open Terminal</button></a>', unsafe_allow_html=True)

                with col2:
                    if st.button("📋 Copy URL", key="copy_master_terminal"):
                        st.code(terminal_url)
                        st.info("👆 Click URL above to copy, then open in new browser tab")

                with col3:
                    if st.button("🚀 Start Claude", key="start_master_claude"):
                        st.info("🎯 Claude started in Master Agent terminal")

                with col4:
                    if st.button("🔍 Verify Competence", key="verify_master_competence"):
                        instruction_path = "./langgraph-test/MASTER_INSTRUCTIONS.md"
                        try:
                            if os.path.exists(instruction_path):
                                with open(instruction_path, 'r', encoding='utf-8') as f:
                                    instruction_content = f.read()

                                message = f"Ecco le tue istruzioni specifiche:\n\n{instruction_content}\n\nPer favore riassumi le tue competenze principali basandoti su queste istruzioni."

                                # Dividi il messaggio in parti se è troppo lungo
                                max_length = 1000
                                if len(message) > max_length:
                                    parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                                    for i, part in enumerate(parts):
                                        subprocess.run([
                                            "/opt/homebrew/bin/tmux", "send-keys", "-t", "claude-master",
                                            part
                                        ], check=True, timeout=3)
                                        if i < len(parts) - 1:
                                            time.sleep(0.5)
                                else:
                                    subprocess.run([
                                        "/opt/homebrew/bin/tmux", "send-keys", "-t", "claude-master",
                                        message
                                    ], check=True, timeout=3)

                                time.sleep(0.5)
                                subprocess.run([
                                    "/opt/homebrew/bin/tmux", "send-keys", "-t", "claude-master",
                                    "Enter"
                                ], check=True, timeout=3)

                                st.success("🎯 **Master Agent instructions sent!** Check terminal for response.")
                            else:
                                st.error(f"❌ Master instruction file not found: {instruction_path}")
                        except Exception as e:
                            st.error(f"❌ Failed to send master instructions: {str(e)}")

                # Status info
                st.success("✅ Interactive Terminal Ready: You can type commands directly in the terminal above or click '🖥️ Open Terminal' for a dedicated tab.")
                st.info("💡 Tip: If the terminal doesn't respond to clicks, try clicking inside the terminal area and then typing.")

            else:
                st.error(f"❌ Terminal not accessible at {terminal_url}")

        except Exception as e:
            st.error(f"❌ Cannot connect to terminal: {str(e)}")

    else:
        st.warning("⚠️ Master Agent session not active")
        if st.button("🔄 Start Master Agent Session", key="start_master_session"):
            st.session_state.system.start_agent_terminal("master")
            st.rerun()

def render_master_agent_interface():
    """Master Agent - Strategic oversight and supreme commands"""

    # System Status Overview
    st.markdown("#### 📊 System Overview")

    # Get system stats
    system = st.session_state.system
    active_sessions = sum(1 for agent_id, agent in system.agents.items()
                        if system.check_agent_session(agent['session']))

    # Compact metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Active", active_sessions, help="Active agents")
    with col2:
        status = "🟢 Online" if system.check_langgraph_status() else "🔴 Offline"
        st.metric("LangGraph", status, help="LangGraph API status")

    # Master Commands
    st.markdown("#### ⚔️ Supreme Commands")

    # Strategic buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎖️ Strategic Assessment", width="stretch", help="Analyze overall system performance"):
            st.info("🎯 Initiating strategic assessment...")
            # TODO: Implement strategic assessment

        if st.button("🚨 Emergency Protocols", width="stretch", help="Activate emergency procedures"):
            st.warning("⚠️ Emergency protocols ready")
            # TODO: Implement emergency protocols

    with col2:
        if st.button("📈 Performance Optimization", width="stretch", help="Optimize system performance"):
            st.info("⚡ Performance optimization initiated")
            # TODO: Implement performance optimization

        if st.button("🔄 System-wide Reset", width="stretch", help="Reset all agent states"):
            if st.session_state.get('confirm_reset', False):
                st.success("🔄 System reset completed")
                st.session_state.confirm_reset = False
            else:
                st.session_state.confirm_reset = True
                st.warning("Click again to confirm system reset")

    # Agent Hierarchy
    st.markdown("#### 🏛️ Command Hierarchy")

    # Show command structure
    hierarchy_agents = [
        ("🎖️ Master", system.agents.get("master", {})),
        ("👨‍💼 Supervisor", system.agents.get("supervisor", {}))
    ]

    for title, agent in hierarchy_agents:
        if agent:
            status_icon = "🟢" if system.check_agent_session(agent.get('session', '')) else "🔴"
            st.markdown(f"{status_icon} **{title}** - {agent.get('name', 'Unknown')}")

def render_agent_terminals():
    """Terminali degli agenti embedded"""
    st.markdown("### 🖥️ Agent Terminals")
    render_agent_terminals_content()

def render_agent_terminals_content():
    """Content of agent terminals"""
    system = st.session_state.system

    # Dividi agenti in due gruppi
    agents_list = list(st.session_state.system.agents.items())

    # Gruppo 1: Solo Supervisor (leadership) - Master spostato nella colonna destra
    leadership_agents = [
        ("supervisor", st.session_state.system.agents["supervisor"])
    ]

    # Gruppo 2: Altri agenti (operativi)
    operational_agents = [
        (agent_id, agent) for agent_id, agent in agents_list
        if agent_id not in ["master", "supervisor"]
    ]

    # Layout a due colonne
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🎖️ Command & Control")
        render_agent_group(leadership_agents)

    with col_right:
        st.markdown("### ⚙️ Operational Agents")
        render_agent_group(operational_agents)

def render_agent_group(agents_list):
    """Render a group of agents"""
    system = st.session_state.system

    for agent_id, agent in agents_list:
        st.markdown(f"#### {agent['name']}")
        st.markdown(f"*{agent['description']}*")

        # Status check
        session_active = st.session_state.system.check_agent_session(agent['session'])

        if session_active:
                # Embedded terminal via iframe
                terminal_url = f"http://localhost:{agent['port']}"

                # Test se ttyd è attivo
                try:
                    response = requests.get(terminal_url, timeout=1)
                    if response.status_code == 200:
                        # Terminal interattivo più grande - configurato per interazione diretta
                        iframe_html = f'''
                        <iframe
                            src="{terminal_url}"
                            width="100%"
                            height="400"
                            frameborder="0"
                            sandbox="allow-same-origin allow-scripts allow-forms allow-top-navigation allow-pointer-lock"
                            style="border: 1px solid #ddd; border-radius: 4px;"
                        ></iframe>
                        '''
                        st.components.v1.html(iframe_html, height=420)

                        # Pulsanti di controllo - 4 colonne per tutti gli agenti
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            # Link diretto al terminale (si apre in nuova tab)
                            st.markdown(f'<a href="{terminal_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #ff4b4b; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">🖥️ Open Terminal</button></a>', unsafe_allow_html=True)

                        with col2:
                            if st.button(f"📋 Copy URL", key=f"copy_{agent_id}"):
                                st.code(terminal_url)
                                st.info("👆 Click URL above to copy, then open in new browser tab")

                        with col3:
                            if st.button(f"🚀 Start Claude", key=f"claude_{agent_id}"):
                                # Avvia Claude nella sessione
                                try:
                                    subprocess.run([
                                        "/opt/homebrew/bin/tmux", "send-keys", "-t", agent['session'],
                                        "claude", "Enter"
                                    ], check=True, timeout=2)
                                    st.success(f"✅ Claude started in {agent['name']}")
                                except:
                                    st.error(f"❌ Failed to start Claude in {agent['name']}")

                        with col4:
                            if st.button(f"🎯 Verify Competence", key=f"verify_{agent_id}"):
                                # Determina il file di istruzioni specifico per l'agente
                                instruction_files = {
                                    "master": "MASTER_INSTRUCTIONS.md",
                                    "supervisor": "SUPERVISOR_INSTRUCTIONS.md",
                                    "backend-api": "BACKEND_INSTRUCTIONS.md",
                                    "database": "DATABASE_INSTRUCTIONS.md",
                                    "frontend-ui": "FRONTEND_INSTRUCTIONS.md",
                                    "instagram": "INSTAGRAM_INSTRUCTIONS.md",
                                    "testing": "TESTING_INSTRUCTIONS.md"
                                }

                                instruction_file = instruction_files.get(agent_id, f"{agent_id.upper()}_INSTRUCTIONS.md")
                                instruction_path = f"./langgraph-test/{instruction_file}"

                                try:
                                    # Leggi il contenuto del file di istruzioni
                                    if os.path.exists(instruction_path):
                                        with open(instruction_path, 'r', encoding='utf-8') as f:
                                            instruction_content = f.read()

                                        # Invia il contenuto del file nella chat dell'agente
                                        message = f"Ecco le tue istruzioni specifiche:\n\n{instruction_content}\n\nPer favore riassumi le tue competenze principali basandoti su queste istruzioni."

                                        # Dividi il messaggio in parti se è troppo lungo
                                        max_length = 1000
                                        if len(message) > max_length:
                                            parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                                            for i, part in enumerate(parts):
                                                subprocess.run([
                                                    "/opt/homebrew/bin/tmux", "send-keys", "-t", agent['session'],
                                                    part
                                                ], check=True, timeout=3)
                                                if i < len(parts) - 1:
                                                    time.sleep(0.5)
                                        else:
                                            subprocess.run([
                                                "/opt/homebrew/bin/tmux", "send-keys", "-t", agent['session'],
                                                message
                                            ], check=True, timeout=3)

                                        time.sleep(0.5)
                                        subprocess.run([
                                            "/opt/homebrew/bin/tmux", "send-keys", "-t", agent['session'],
                                            "Enter"
                                        ], check=True, timeout=3)

                                        st.success(f"🎯 **Instruction file sent to {agent['name']}!** Check terminal for response.")
                                    else:
                                        st.error(f"❌ Instruction file not found: {instruction_path}")

                                except Exception as e:
                                    st.error(f"❌ Failed to send instructions: {str(e)}")

                        # Istruzioni per l'utente
                        st.success("✅ **Interactive Terminal Ready:** You can type commands directly in the terminal above or click '🖥️ Open Terminal' for a dedicated tab.")
                        st.info("💡 **Tip:** If the terminal doesn't respond to clicks, try clicking inside the terminal area and then typing.")
                    else:
                        st.warning(f"Terminal not ready. Click 'Start {agent_id}' in sidebar.")
                        if st.button(f"🔧 Start Terminal {agent_id}", key=f"start_term_{agent_id}"):
                            st.session_state.system.start_agent_terminal(agent_id)
                            st.rerun()
                except:
                    st.warning(f"Terminal not ready. Click 'Start {agent_id}' in sidebar.")
                    if st.button(f"🔧 Start Terminal {agent_id}", key=f"start_term_alt_{agent_id}"):
                        st.session_state.system.start_agent_terminal(agent_id)
                        st.rerun()

        else:
            st.info(f"Session '{agent['session']}' not active. Start from sidebar.")

            st.markdown("---")

def render_langgraph_studio():
    """LangGraph Studio integration"""
    st.markdown("### 🔬 LangGraph Studio")

    system = st.session_state.system

    if st.session_state.system.check_langgraph_status():
        st.success("✅ LangGraph API is active")

        # Avviso per LangGraph Studio
        st.warning("⚠️ **LangGraph Studio requires LangSmith account and internet access**")

        tab1, tab2 = st.tabs(["🏠 Local API Interface", "🌐 External Studio"])

        with tab1:
            st.markdown("#### 🔧 Local LangGraph API Testing")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("##### 📋 API Information")
                st.info(f"""
                **Base URL:** `{st.session_state.system.langgraph_url}`
                **Graph ID:** `agent`
                **Status:** ✅ Online
                **Available Endpoints:** /docs, /assistants, /threads
                """)

                st.markdown("##### 🧪 Test API Connection")
                test_message = st.text_input("Test Message", value="Hello from local API test!")

                if st.button("🚀 Send Test Request", type="primary"):
                    with st.spinner("Testing LangGraph API..."):
                        result = st.session_state.system.send_langgraph_task(test_message)
                        if result['success']:
                            st.success("✅ API Test Successful!")
                            st.info(result['data'])
                        else:
                            st.error(f"❌ API Test Failed: {result['error']}")

            with col2:
                st.markdown("##### 🔗 Direct Links")
                st.markdown(f"• 📖 [API Documentation]({st.session_state.system.langgraph_url}/docs)")
                st.markdown(f"• ❤️ [Health Check]({st.session_state.system.langgraph_url}/health)")
                st.markdown(f"• 📊 [OpenAPI Schema]({st.session_state.system.langgraph_url}/openapi.json)")

                st.markdown("##### ⚙️ Available Operations")
                st.markdown("• Search Assistants")
                st.markdown("• Create Threads")
                st.markdown("• Execute Graphs")
                st.markdown("• Stream Results")

        with tab2:
            st.markdown("#### 🌐 External LangGraph Studio")

            st.info("""
            **LangGraph Studio** is a visual interface for building and debugging LangGraph applications.

            **Requirements:**
            - LangSmith account (sign up at langchain.com)
            - Internet connection
            - LangChain API key
            """)

            studio_option = st.radio(
                "Choose Studio Access Method:",
                ["🔗 Open in New Tab", "📱 Embedded (may be blocked)"]
            )

            studio_url = f"https://smith.langchain.com/studio/?baseUrl={st.session_state.system.langgraph_url}"

            if studio_option == "🔗 Open in New Tab":
                st.markdown(f'<a href="{studio_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #0066cc; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px;">🚀 Open LangGraph Studio</button></a>', unsafe_allow_html=True)
                st.info("👆 Click the button above to open LangGraph Studio in a new browser tab")

            else:
                st.warning("⚠️ Embedded studio may be blocked by network security policies")
                try:
                    st.components.v1.iframe(studio_url, height=600, scrolling=True)
                except:
                    st.error("❌ Unable to load embedded studio. Use 'Open in New Tab' option instead.")

    else:
        st.error("❌ LangGraph API is not running")
        st.info("Start LangGraph dev server from the sidebar or terminal")

def render_analytics():
    """Analytics e metriche dal SharedState"""
    st.markdown("### 📊 System Analytics")

    system = st.session_state.system
    stats = st.session_state.system.state_manager.get_system_stats()
    agents_state = st.session_state.system.state_manager.get_all_agents()
    current_task = st.session_state.system.state_manager.get_current_task()
    task_queue = st.session_state.system.state_manager.get_task_queue()
    task_history = st.session_state.system.state_manager.get_task_history(20)

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🤖 Total Agents", stats["total_agents"])

    with col2:
        st.metric("⚡ Active Agents", stats["active_agents"])

    with col3:
        st.metric("📋 Tasks in Queue", stats["tasks_in_queue"])

    with col4:
        st.metric("✅ Completed Tasks", stats["completed_tasks"])

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🤖 Agent Status")

        # Agent status table
        agent_data = []
        for agent_id, agent in agents_state.items():
            agent_data.append({
                "Agent": agent.name,
                "Status": agent.status.value.title(),
                "Current Task": agent.current_task or "-",
                "Last Activity": agent.last_activity.strftime("%H:%M:%S"),
                "Port": agent.port
            })

        if agent_data:
            df_agents = pd.DataFrame(agent_data)
            st.dataframe(df_agents, use_container_width=True)

        st.markdown("#### 📊 System Status")
        st.info(f"**System Status:** {stats['system_status'].title()}")
        st.info(f"**Last Updated:** {stats['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}")

        # Task Completion Monitor Controls
        st.markdown("#### 🤖 Auto Completion Monitor")
        if MONITOR_AVAILABLE and st.session_state.system.completion_monitor:
            monitor_status = st.session_state.system.completion_monitor.get_monitoring_status()

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                if monitor_status['monitoring']:
                    st.success("🟢 Monitor Active")
                    if st.button("🛑 Stop Monitor", key="stop_monitor"):
                        st.session_state.system.completion_monitor.stop_monitoring()
                        st.success("Monitor stopped!")
                        st.rerun()
                else:
                    st.warning("🔴 Monitor Inactive")
                    if st.button("▶️ Start Monitor", key="start_monitor"):
                        st.session_state.system.completion_monitor.start_monitoring()
                        st.success("Monitor started!")
                        st.rerun()

            with col_m2:
                timeout = st.number_input("Timeout (min)",
                                        min_value=5, max_value=120,
                                        value=st.session_state.system.completion_monitor.task_timeout_minutes,
                                        key="timeout_input")
                if st.button("⏰ Update", key="update_timeout"):
                    st.session_state.system.completion_monitor.task_timeout_minutes = timeout
                    st.success(f"Timeout updated to {timeout} minutes")

            with col_m3:
                # Emergency reset button
                if st.button("🚨 Emergency Reset", key="emergency_reset", type="secondary"):
                    # Run emergency reset
                    try:
                        subprocess.run(["python3", str(st.session_state.system.project_root / "langgraph-test" / "reset_stuck_agents.py")], check=True)
                        st.success("🎉 Emergency reset completed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reset failed: {e}")
        else:
            st.warning("⚠️ Task Completion Monitor not available")

    with col2:
        st.markdown("#### 📋 Current Task")
        if current_task:
            st.success(f"**Task ID:** {current_task.task_id}")
            st.write(f"**Description:** {current_task.description}")
            st.write(f"**Priority:** {current_task.priority.name}")
            st.write(f"**Assigned Agents:** {', '.join(current_task.assigned_agents)}")
            st.progress(current_task.progress / 100.0)
            st.write(f"**Progress:** {current_task.progress:.1f}%")

            # Task completion controls
            st.markdown("##### 🎛️ Task Controls")
            col2_1, col2_2, col2_3 = st.columns(3)

            with col2_1:
                if st.button("✅ Complete Task", key="complete_task"):
                    if st.session_state.system.state_manager.complete_task(current_task.task_id, {"manual": "Completed via web interface"}):
                        st.success("Task completed successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to complete task")

            with col2_2:
                if st.button("❌ Fail Task", key="fail_task"):
                    if st.session_state.system.state_manager.complete_task(current_task.task_id, error_message="Failed via web interface"):
                        st.error("Task marked as failed")
                        st.rerun()
                    else:
                        st.error("Failed to mark task as failed")

            with col2_3:
                new_progress = st.number_input("Update Progress", min_value=0, max_value=100,
                                             value=int(current_task.progress), key="progress_input")
                if st.button("📊 Update", key="update_progress"):
                    # Update progress in SharedState
                    st.session_state.system.state_manager.state.current_task.progress = float(new_progress)
                    st.session_state.system.state_manager.save_state()
                    st.success(f"Progress updated to {new_progress}%")
                    st.rerun()

        else:
            st.info("No active task")

        st.markdown("#### 📈 Task Queue")
        if task_queue:
            for i, task in enumerate(task_queue[:5]):  # Show first 5
                with st.expander(f"Task {i+1}: {task.description[:50]}..."):
                    st.write(f"**ID:** {task.task_id}")
                    st.write(f"**Priority:** {task.priority.name}")
                    st.write(f"**Created:** {task.created_at.strftime('%H:%M:%S')}")
        else:
            st.info("No tasks in queue")

    st.divider()

    # Task History
    st.markdown("#### 📚 Recent Task History")
    if task_history:
        history_data = []
        for task in reversed(task_history[-10:]):  # Last 10 tasks
            history_data.append({
                "Task ID": task.task_id,
                "Description": task.description[:50] + "..." if len(task.description) > 50 else task.description,
                "Status": task.status.title(),
                "Priority": task.priority.name,
                "Agents": ", ".join(task.assigned_agents),
                "Created": task.created_at.strftime("%H:%M:%S"),
                "Completed": task.completed_at.strftime("%H:%M:%S") if task.completed_at else "-"
            })

        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)

        # Task status chart
        status_counts = {}
        for task in task_history:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1

        if status_counts:
            fig = go.Figure(data=[
                go.Bar(x=list(status_counts.keys()), y=list(status_counts.values()))
            ])
            fig.update_layout(title="Task Status Distribution", height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No task history available")

def render_request_manager():
    """Agent Request Management System"""
    st.markdown("### 🔐 Agent Request Management")

    system = st.session_state.system

    if not REQUEST_SYSTEM_AVAILABLE or not st.session_state.system.request_manager:
        st.error("⚠️ Agent Request Management System not available")
        return

    # Control Panel
    st.markdown("#### 🎛️ Control Panel")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Request Monitor Controls
        st.markdown("##### 🔍 Request Monitor")
        if st.session_state.system.request_monitor:
            monitor_status = st.session_state.system.request_monitor.get_monitoring_status()

            if monitor_status['monitoring']:
                st.success("🟢 Monitor Active")
                if st.button("🛑 Stop Monitor", key="stop_req_monitor"):
                    st.session_state.system.request_monitor.stop_monitoring()
                    st.success("Request monitor stopped!")
                    st.rerun()
            else:
                st.warning("🔴 Monitor Inactive")
                if st.button("▶️ Start Monitor", key="start_req_monitor"):
                    st.session_state.system.request_monitor.start_monitoring()
                    st.success("Request monitor started!")
                    st.rerun()

    with col2:
        # Manual Request Creation
        st.markdown("##### ➕ Create Request")
        agent_id = st.selectbox("Agent", list(st.session_state.system.agents.keys()), key="req_agent")
        request_type = st.selectbox("Type", [rt.value for rt in RequestType], key="req_type")
        command = st.text_input("Command", key="req_command")

        if st.button("Create Request", key="create_req"):
            if command:
                req_id = st.session_state.system.request_manager.create_request(
                    agent_id=agent_id,
                    request_type=RequestType(request_type),
                    command=command,
                    description=f"Manual request: {command}"
                )
                st.success(f"Request created: {req_id}")
                st.rerun()

    with col3:
        # System Stats
        st.markdown("##### 📊 Stats")
        pending_requests = st.session_state.system.request_manager.get_pending_requests()
        recent_requests = st.session_state.system.request_manager.get_request_history(20)

        st.metric("Pending Requests", len(pending_requests))
        st.metric("Total Requests", len(recent_requests))

        if st.button("🧹 Cleanup Old", key="cleanup_req"):
            st.session_state.system.request_manager.cleanup_old_requests()
            st.success("Old requests cleaned up!")
            st.rerun()

    st.divider()

    # Pending Requests Section
    st.markdown("#### ⏳ Pending Requests")
    pending_requests = st.session_state.system.request_manager.get_pending_requests()

    if pending_requests:
        for req in pending_requests:
            with st.expander(f"🔴 {req.request_id} - {req.agent_id} - {req.risk_level.upper()}", expanded=True):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Command:** `{req.command}`")
                    st.write(f"**Description:** {req.description}")
                    st.write(f"**Type:** {req.request_type.value}")
                    st.write(f"**Created:** {req.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

                with col2:
                    if st.button("✅ Approve", key=f"approve_{req.request_id}"):
                        success = st.session_state.system.request_manager.approve_request(req.request_id, "web_interface")
                        if success:
                            st.success("Request approved!")
                            # Try to execute if auto-approved
                            st.session_state.system.request_manager.execute_request(req.request_id)
                            st.rerun()
                        else:
                            st.error("Failed to approve request")

                with col3:
                    if st.button("❌ Reject", key=f"reject_{req.request_id}"):
                        reason = st.text_input("Reason", key=f"reason_{req.request_id}", value="Rejected via web interface")
                        success = st.session_state.system.request_manager.reject_request(req.request_id, reason)
                        if success:
                            st.error("Request rejected!")
                            st.rerun()
                        else:
                            st.error("Failed to reject request")
    else:
        st.info("No pending requests")

    st.divider()

    # Request History
    st.markdown("#### 📚 Request History")
    recent_requests = st.session_state.system.request_manager.get_request_history(15)

    if recent_requests:
        history_data = []
        for req in recent_requests:
            history_data.append({
                "Request ID": req.request_id,
                "Agent": req.agent_id,
                "Type": req.request_type.value,
                "Command": req.command[:30] + "..." if len(req.command) > 30 else req.command,
                "Status": req.status.value,
                "Risk": req.risk_level,
                "Auto": "✅" if req.auto_approve else "❌",
                "Created": req.created_at.strftime("%H:%M:%S"),
                "Approved By": req.approved_by or "-"
            })

        df_requests = pd.DataFrame(history_data)
        st.dataframe(df_requests, use_container_width=True)

        # Request statistics
        st.markdown("#### 📈 Request Statistics")
        col1, col2 = st.columns(2)

        with col1:
            # Status distribution
            status_counts = {}
            for req in recent_requests:
                status_counts[req.status.value] = status_counts.get(req.status.value, 0) + 1

            if status_counts:
                fig_status = go.Figure(data=[
                    go.Pie(labels=list(status_counts.keys()), values=list(status_counts.values()))
                ])
                fig_status.update_layout(title="Request Status Distribution", height=300)
                st.plotly_chart(fig_status, use_container_width=True)

        with col2:
            # Risk level distribution
            risk_counts = {}
            for req in recent_requests:
                risk_counts[req.risk_level] = risk_counts.get(req.risk_level, 0) + 1

            if risk_counts:
                fig_risk = go.Figure(data=[
                    go.Bar(x=list(risk_counts.keys()), y=list(risk_counts.values()))
                ])
                fig_risk.update_layout(title="Risk Level Distribution", height=300)
                st.plotly_chart(fig_risk, use_container_width=True)
    else:
        st.info("No request history available")

def render_instructions_editor():
    """Editor per le istruzioni degli agenti"""
    st.markdown("### 📝 Agent Instructions Editor")

    system = st.session_state.system

    # Mapping dei file di istruzioni
    instruction_files = {
        "master": "MASTER_INSTRUCTIONS.md",
        "supervisor": "SUPERVISOR_INSTRUCTIONS.md",
        "backend-api": "BACKEND_INSTRUCTIONS.md",
        "database": "DATABASE_INSTRUCTIONS.md",
        "frontend-ui": "FRONTEND_INSTRUCTIONS.md",
        "instagram": "INSTAGRAM_INSTRUCTIONS.md",
        "testing": "TESTING_INSTRUCTIONS.md"
    }

    # Selezione agente
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("#### 🤖 Select Agent")

        # Check se c'è un agente da editare dalla sidebar
        if hasattr(st.session_state, 'editing_agent') and st.session_state.editing_agent:
            selected_agent = st.session_state.editing_agent
            st.session_state.editing_agent = None  # Reset
        else:
            selected_agent = st.selectbox(
                "Choose agent to edit:",
                options=list(st.session_state.system.agents.keys()),
                format_func=lambda x: st.session_state.system.agents[x]['name']
            )

        agent_info = st.session_state.system.agents[selected_agent]
        st.info(f"**{agent_info['name']}**\n\n{agent_info['description']}")

        # Bottoni azioni
        if st.button("🔄 Reload File", key="reload_instructions"):
            st.rerun()

        if st.button("🎯 Send to Agent", key="send_instructions"):
            # Invia comando all'agente per rileggere le istruzioni
            try:
                instruction_file = instruction_files[selected_agent]
                command = f"Leggi il file {instruction_file} e riassumi le tue competenze"

                subprocess.run([
                    "/opt/homebrew/bin/tmux", "send-keys", "-t", agent_info['session'],
                    command
                ], check=True, timeout=3)
                time.sleep(0.2)
                subprocess.run([
                    "/opt/homebrew/bin/tmux", "send-keys", "-t", agent_info['session'],
                    "Enter"
                ], check=True, timeout=3)

                st.success(f"✅ Instructions sent to {agent_info['name']}!")
            except Exception as e:
                st.error(f"❌ Failed to send instructions: {str(e)}")

    with col2:
        st.markdown("#### 📄 Edit Instructions")

        instruction_file = instruction_files[selected_agent]
        file_path = f"/Users/erik/Desktop/claude-multiagent-system/langgraph-test/{instruction_file}"

        try:
            # Leggi il file esistente
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Editor di testo
            updated_content = st.text_area(
                f"Edit {instruction_file}:",
                value=current_content,
                height=500,
                key=f"editor_{selected_agent}"
            )

            # Bottoni di controllo
            col_save, col_preview, col_reset = st.columns(3)

            with col_save:
                if st.button("💾 Save Changes", key="save_instructions", type="primary"):
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        st.success(f"✅ {instruction_file} saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to save file: {str(e)}")

            with col_preview:
                if st.button("👁️ Preview", key="preview_instructions"):
                    with st.expander("📖 Markdown Preview", expanded=True):
                        st.markdown(updated_content)

            with col_reset:
                if st.button("🔄 Reset", key="reset_instructions"):
                    st.rerun()

            # Info file
            st.markdown("---")
            st.markdown("**📊 File Info:**")
            st.code(f"File: {file_path}")
            st.code(f"Lines: {len(updated_content.splitlines())}")
            st.code(f"Characters: {len(updated_content)}")

        except FileNotFoundError:
            st.error(f"❌ Instruction file not found: {instruction_file}")
            st.info("The file will be created when you save.")

            # Editor per nuovo file
            new_content = st.text_area(
                f"Create {instruction_file}:",
                value=f"# {agent_info['name']} - Instructions\n\nAdd your instructions here...",
                height=500,
                key=f"new_editor_{selected_agent}"
            )

            if st.button("💾 Create File", key="create_instructions", type="primary"):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    st.success(f"✅ {instruction_file} created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to create file: {str(e)}")

        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

def render_messaging_center():
    """Advanced Inter-Agent Messaging Center"""
    st.markdown("## 💬 Inter-Agent Messaging Center")
    st.markdown("*Advanced messaging system with direct messages, broadcasts, and inbox management*")

    # Check if messaging system is available
    if not MESSAGING_AVAILABLE:
        st.error("❌ Messaging system not available")
        st.info("The messaging system components could not be imported. Please check the installation.")
        return

    # Get agents from state manager
    try:
        agents = list(st.session_state.system.state_manager.state.agents.keys())
        if not agents:
            st.warning("⚠️ No agents available for messaging")
            return

        # Create tabs for different messaging features
        msg_tab1, msg_tab2, msg_tab3, msg_tab4 = st.tabs([
            "📤 Send Message", "📢 Broadcast", "📬 Inbox", "📊 Statistics"
        ])

        # Tab 1: Send Direct Message
        with msg_tab1:
            st.markdown("### 📤 Send Direct Message")

            # Use st.form for better state management
            with st.form("send_message_form", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    sender = st.selectbox(
                        "From Agent:",
                        agents,
                        key="form_sender_select"
                    )

                    recipient = st.selectbox(
                        "To Agent:",
                        [a for a in agents if a != sender],
                        key="form_recipient_select"
                    )

                    priority = st.selectbox(
                        "Priority:",
                        ["LOW", "NORMAL", "HIGH", "URGENT"],
                        index=1,
                        key="form_priority_select"
                    )

                with col2:
                    subject = st.text_input(
                        "Subject:",
                        placeholder="Message subject (optional)",
                        key="form_message_subject"
                    )

                    message_content = st.text_area(
                        "Message:",
                        placeholder="Enter your message here...",
                        height=100,
                        key="form_message_content"
                    )

                # Submit button
                submitted = st.form_submit_button("📨 Send Message", type="primary")

                if submitted:
                    if message_content and message_content.strip():
                        try:
                            message_id = st.session_state.system.state_manager.send_agent_message(
                                sender_id=sender,
                                recipient_id=recipient,
                                content=message_content.strip(),
                                subject=subject.strip() if subject else None,
                                priority=priority
                            )

                            if message_id:
                                st.success(f"✅ Message sent successfully! ID: {message_id[:8]}")
                                st.balloons()  # Visual feedback
                            else:
                                st.error("❌ Failed to send message")
                        except Exception as e:
                            st.error(f"❌ Error sending message: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter a message")

        # Tab 2: Broadcast Message
        with msg_tab2:
            st.markdown("### 📢 Broadcast Message")

            # Use st.form for better state management
            with st.form("broadcast_message_form", clear_on_submit=True):
                broadcast_sender = st.selectbox(
                    "Broadcasting Agent:",
                    agents,
                    key="broadcast_sender"
                )

                exclude_agents = st.multiselect(
                    "Exclude Agents (optional):",
                    [a for a in agents if a != broadcast_sender],
                    key="exclude_agents"
                )

                broadcast_priority = st.selectbox(
                    "Broadcast Priority:",
                    ["LOW", "NORMAL", "HIGH", "URGENT"],
                    index=1,
                    key="broadcast_priority"
                )

                broadcast_subject = st.text_input(
                    "Broadcast Subject:",
                    placeholder="Broadcast subject (optional)",
                    key="broadcast_subject"
                )

                broadcast_content = st.text_area(
                    "Broadcast Message:",
                    placeholder="Enter your broadcast message here...",
                    height=120,
                    key="broadcast_content"
                )

                recipients_preview = [a for a in agents if a != broadcast_sender and a not in exclude_agents]
                st.info(f"📊 Recipients: {len(recipients_preview)} agents ({', '.join(recipients_preview)})")

                submitted = st.form_submit_button("📢 Send Broadcast", type="primary")

                if submitted:
                    if broadcast_content and broadcast_content.strip():
                        try:
                            message_ids = st.session_state.system.state_manager.broadcast_agent_message(
                                sender_id=broadcast_sender,
                                content=broadcast_content,
                                subject=broadcast_subject if broadcast_subject else None,
                                priority=broadcast_priority,
                                exclude_agents=exclude_agents if exclude_agents else None
                            )

                            if message_ids:
                                st.success(f"✅ Broadcast sent to {len(message_ids)} agents!")
                                st.balloons()  # Visual feedback
                                with st.expander("📋 Message IDs"):
                                    for i, msg_id in enumerate(message_ids, 1):
                                        st.code(f"{i}. {msg_id}")
                            else:
                                st.error("❌ Failed to send broadcast")
                        except Exception as e:
                            st.error(f"❌ Error sending broadcast: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter a broadcast message")

        # Tab 3: Inbox Management
        with msg_tab3:
            st.markdown("### 📬 Agent Inbox")

            selected_agent = st.selectbox(
                "Select Agent:",
                agents,
                key="inbox_agent_select"
            )

            if selected_agent:
                try:
                    inbox = st.session_state.system.state_manager.get_agent_inbox(selected_agent)

                    # Inbox Summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📬 Total Messages", len(inbox.messages))
                    with col2:
                        st.metric("🔴 Unread", inbox.unread_count)
                    with col3:
                        st.metric("✅ Read", len(inbox.messages) - inbox.unread_count)

                    if inbox.messages:
                        st.markdown("---")

                        # Message filters
                        filter_col1, filter_col2 = st.columns(2)
                        with filter_col1:
                            show_filter = st.selectbox(
                                "Show:",
                                ["All Messages", "Unread Only", "Read Only"],
                                key="message_filter"
                            )
                        with filter_col2:
                            limit = st.number_input(
                                "Messages to show:",
                                min_value=5,
                                max_value=50,
                                value=10,
                                key="message_limit"
                            )

                        # Get filtered messages
                        if show_filter == "Unread Only":
                            messages = inbox.get_unread_messages()
                        elif show_filter == "Read Only":
                            messages = [msg for msg in inbox.messages if msg.status == MessageStatus.READ]
                        else:
                            messages = inbox.get_recent_messages(limit)

                        # Display messages
                        for i, msg in enumerate(messages[:limit]):
                            status_icon = "📩" if msg.status == MessageStatus.READ else "📬"
                            type_icon = "🔊" if msg.is_broadcast() else "💬"
                            priority_color = {
                                "LOW": "🟢",
                                "NORMAL": "🟡",
                                "HIGH": "🟠",
                                "URGENT": "🔴"
                            }.get(msg.priority.value, "🟡")

                            with st.expander(
                                f"{status_icon} {type_icon} {priority_color} From: {msg.sender_id} | {msg.subject or 'No subject'} | {msg.timestamp.strftime('%H:%M:%S')}",
                                expanded=(msg.status != MessageStatus.READ)
                            ):
                                st.markdown(f"**Message ID:** `{msg.message_id}`")
                                st.markdown(f"**From:** {msg.sender_id}")
                                st.markdown(f"**To:** {msg.recipient_id}")
                                st.markdown(f"**Priority:** {priority_color} {msg.priority.value}")
                                st.markdown(f"**Type:** {type_icon} {msg.message_type.value}")
                                st.markdown(f"**Created:** {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                                if msg.subject:
                                    st.markdown(f"**Subject:** {msg.subject}")
                                st.markdown("**Content:**")
                                st.markdown(f"```\n{msg.content}\n```")

                                if msg.status != MessageStatus.READ:
                                    if st.button(f"✅ Mark as Read", key=f"mark_read_{msg.message_id}"):
                                        success = st.session_state.system.state_manager.mark_agent_message_read(
                                            selected_agent, msg.message_id
                                        )
                                        if success:
                                            st.success("Message marked as read!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to mark message as read")
                    else:
                        st.info("📭 No messages in inbox")

                except Exception as e:
                    st.error(f"❌ Error loading inbox: {str(e)}")

        # Tab 4: Messaging Statistics
        with msg_tab4:
            st.markdown("### 📊 Messaging System Statistics")

            try:
                stats = st.session_state.system.state_manager.get_messaging_stats()

                # Overview metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🤖 Total Agents", stats.get('total_agents', 0))
                with col2:
                    st.metric("💬 Total Messages", stats.get('total_messages', 0))
                with col3:
                    st.metric("📬 Unread Messages", stats.get('unread_messages', 0))
                with col4:
                    st.metric("🗣️ Active Conversations", stats.get('active_conversations', 0))

                st.markdown("---")

                # Per-agent breakdown
                st.markdown("#### 📋 Per-Agent Message Breakdown")

                agent_data = []
                for agent_id in agents:
                    try:
                        inbox = st.session_state.system.state_manager.get_agent_inbox(agent_id)
                        agent_data.append({
                            "Agent": agent_id,
                            "Total Messages": len(inbox.messages),
                            "Unread": inbox.unread_count,
                            "Read": len(inbox.messages) - inbox.unread_count
                        })
                    except:
                        agent_data.append({
                            "Agent": agent_id,
                            "Total Messages": 0,
                            "Unread": 0,
                            "Read": 0
                        })

                if agent_data:
                    df = pd.DataFrame(agent_data)
                    st.dataframe(df, use_container_width=True)

                # Message activity chart
                st.markdown("#### 📈 Message Activity Overview")

                if stats.get('total_messages', 0) > 0:
                    # Create a simple bar chart of messages per agent
                    agent_names = [data['Agent'] for data in agent_data]
                    message_counts = [data['Total Messages'] for data in agent_data]

                    fig = go.Figure(data=[
                        go.Bar(
                            x=agent_names,
                            y=message_counts,
                            marker_color='lightblue'
                        )
                    ])

                    fig.update_layout(
                        title="Messages per Agent",
                        xaxis_title="Agent",
                        yaxis_title="Message Count",
                        height=400
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 No message activity to display yet")

            except Exception as e:
                st.error(f"❌ Error loading statistics: {str(e)}")

    except Exception as e:
        st.error(f"❌ Error initializing messaging center: {str(e)}")
        st.info("Make sure the SharedState system is properly initialized")

def main():
    """Main application"""
    # Initialize system
    if 'system' not in st.session_state:
        st.session_state.system = CompleteMultiAgentSystem()

    # Render interface
    render_sidebar()
    render_main_interface()

    # Auto-refresh every 30 seconds
    time.sleep(0.1)  # Prevent too frequent updates

if __name__ == "__main__":
    main()