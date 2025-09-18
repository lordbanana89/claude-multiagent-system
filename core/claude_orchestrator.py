#!/usr/bin/env python3
"""
Claude-native CrewAI Orchestrator
Orchestratore che usa direttamente i terminali Claude esistenti
"""

import os
import sys
import time
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from centralized config
from config.settings import (
    PROJECT_ROOT,
    AGENT_SESSIONS,
    TMUX_BIN
)
from core.tmux_client import TMUXClient

# Load environment
from dotenv import load_dotenv
load_dotenv('.env.crewai')

class ClaudeNativeOrchestrator:
    """Orchestratore che lavora nativamente con Claude Code senza API esterne"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        # Get agent IDs from config
        self.agent_ids = list(AGENT_SESSIONS.keys())

        # Get TMUX sessions from config
        self.tmux_sessions = list(AGENT_SESSIONS.values())

    def send_task_to_claude(self, session_name: str, task: str, context: str = "") -> bool:
        """Invia task direttamente a sessione Claude"""
        try:
            # Map legacy names to actual TMUX sessions
            session_mapping = {
                "prompt-validator": "supervisor",
                "task-coordinator": "supervisor",
                "backend-api": "backend-api",
                "database": "database",
                "frontend-ui": "frontend-ui",
                "testing": "testing"
            }

            # Get the correct agent ID
            agent_id = session_mapping.get(session_name, session_name)

            # Get the actual TMUX session from AGENT_SESSIONS
            tmux_session = AGENT_SESSIONS.get(agent_id)
            if not tmux_session:
                print(f"⚠️ Unknown agent: {session_name} -> {agent_id}")
                return False

            full_message = f"""
🤖 CREWAI ORCHESTRATOR → {agent_id.upper()}

TASK: {task}

{context}

Please process this task and provide your response.
The orchestrator will check for your completion.

─────────────────────────────────────────
"""

            # Use TMUXClient with proper delay to send to correct TMUX session
            success = TMUXClient.send_command(tmux_session, full_message)

            if success:
                print(f"✅ Task sent to {agent_id} (session: {tmux_session})")
            else:
                print(f"❌ Failed to send task to {agent_id}")

            return success

        except Exception as e:
            print(f"❌ Error sending task to {session_name}: {e}")
            return False

    def get_claude_response(self, agent_id: str, wait_seconds: int = 3) -> str:
        """Cattura risposta da sessione Claude"""
        try:
            time.sleep(wait_seconds)

            # Get actual TMUX session name from agent_id
            tmux_session = AGENT_SESSIONS.get(agent_id)
            if not tmux_session:
                return f"Error: Unknown agent {agent_id}"

            # Use TMUXClient to capture pane with correct session name
            output = TMUXClient.capture_pane(tmux_session)
            return output if output else ""

        except subprocess.CalledProcessError as e:
            return f"Error capturing from {agent_id}: {e}"

    def coordinate_full_stack_feature(self, feature_description: str) -> Dict:
        """Coordina sviluppo full-stack usando agenti Claude nativi"""

        print(f"🚀 COORDINATING FULL-STACK FEATURE: {feature_description}")
        print("=" * 70)

        results = {
            "feature": feature_description,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "coordination_steps": [],
            "agent_responses": {}
        }

        # Step 1: Task analysis con prompt-validator
        print("\n📋 STEP 1: Task Validation and Analysis")
        validation_task = f"""
Analyze this full-stack feature request:
"{feature_description}"

Provide:
1. Feature breakdown
2. Complexity assessment
3. Required teams and skills
4. Potential challenges
"""

        if self.send_task_to_claude("prompt-validator", validation_task):
            results["coordination_steps"].append("✅ Task validation sent")
            time.sleep(3)  # Wait for analysis

        # Step 2: Project coordination
        print("\n🎯 STEP 2: Project Coordination")
        coordination_task = f"""
Coordinate the development of: "{feature_description}"

Based on the validation analysis, please:
1. Create development plan
2. Identify team coordination needs
3. Set priorities and milestones
4. Coordinate with backend, frontend, and database teams
"""

        if self.send_task_to_claude("task-coordinator", coordination_task):
            results["coordination_steps"].append("✅ Project coordination initiated")

        # Step 3: Backend development
        print("\n🔧 STEP 3: Backend Development")
        backend_task = f"""
Implement backend components for: "{feature_description}"

Please handle:
1. API endpoint design
2. Business logic implementation
3. Database integration
4. Security considerations
"""

        if self.send_task_to_claude("backend-api", backend_task):
            results["coordination_steps"].append("✅ Backend development started")

        # Step 4: Database design
        print("\n🗃️  STEP 4: Database Design")
        db_task = f"""
Design database schema for: "{feature_description}"

Please provide:
1. Table structure
2. Relationships
3. Indexes and optimization
4. Migration plan
"""

        if self.send_task_to_claude("database", db_task):
            results["coordination_steps"].append("✅ Database design initiated")

        # Step 5: Frontend development
        print("\n🎨 STEP 5: Frontend Development")
        frontend_task = f"""
Create frontend interface for: "{feature_description}"

Please develop:
1. UI components
2. State management
3. API integration
4. User experience flow
"""

        if self.send_task_to_claude("frontend-ui", frontend_task):
            results["coordination_steps"].append("✅ Frontend development started")

        # Step 6: Testing coordination
        print("\n🧪 STEP 6: Testing Strategy")
        testing_task = f"""
Create comprehensive testing for: "{feature_description}"

Please prepare:
1. Unit tests
2. Integration tests
3. E2E testing scenarios
4. Performance testing
"""

        if self.send_task_to_claude("testing", testing_task):
            results["coordination_steps"].append("✅ Testing strategy implemented")

        print(f"\n🎉 COORDINATION COMPLETED!")
        print("All agents have received their tasks and are working.")
        print("Check individual agent sessions for progress updates.")

        results["status"] = "coordinated"
        results["active_agents"] = len([s for s in results["coordination_steps"] if "✅" in s])

        return results

    def monitor_agent_progress(self) -> Dict:
        """Monitora progresso di tutti gli agenti"""

        print("📊 MONITORING AGENT PROGRESS")
        print("=" * 40)

        progress = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agents": {}
        }

        # Iterate through agent IDs, not tmux sessions
        for agent_id, tmux_session in AGENT_SESSIONS.items():
            try:
                # Check if session is active using TMUXClient
                if TMUXClient.session_exists(tmux_session):
                    # Get recent activity using agent_id
                    output = self.get_claude_response(agent_id, wait_seconds=0)
                    recent_lines = output.split('\n')[-5:]
                    recent_activity = '\n'.join(recent_lines)

                    progress["agents"][agent_id] = {
                        "status": "active",
                        "tmux_session": tmux_session,
                        "recent_activity": recent_activity,
                        "last_checked": time.strftime("%H:%M:%S")
                    }

                    print(f"✅ {agent_id} ({tmux_session}): Active")
                else:
                    progress["agents"][agent_id] = {
                        "status": "inactive",
                        "tmux_session": tmux_session,
                        "last_checked": time.strftime("%H:%M:%S")
                    }
                    print(f"❌ {agent_id} ({tmux_session}): Inactive")

            except Exception as e:
                progress["agents"][agent_id] = {
                    "status": "error",
                    "error": str(e),
                    "last_checked": time.strftime("%H:%M:%S")
                }
                print(f"⚠️ {agent_id}: Error - {e}")

        return progress

    def intelligent_task_distribution(self, project_description: str) -> Dict:
        """Distribuzione intelligente basata su analisi del progetto"""

        print(f"🧠 INTELLIGENT TASK DISTRIBUTION")
        print(f"Project: {project_description}")
        print("=" * 50)

        # Analisi automatica del tipo di progetto
        project_type = "unknown"
        required_teams = []

        # Simple keyword analysis (in real scenario, this would be more sophisticated)
        keywords_lower = project_description.lower()

        if any(word in keywords_lower for word in ["api", "backend", "server", "database"]):
            required_teams.extend(["backend-api", "database"])
            if "frontend" in keywords_lower or "ui" in keywords_lower or "interface" in keywords_lower:
                project_type = "full-stack"
                required_teams.append("frontend-ui")
            else:
                project_type = "backend"

        elif any(word in keywords_lower for word in ["frontend", "ui", "interface", "component"]):
            project_type = "frontend"
            required_teams.append("frontend-ui")

        elif any(word in keywords_lower for word in ["instagram", "social", "posts"]):
            required_teams.extend(["instagram", "queue-manager"])
            project_type = "social-media"

        # Always include coordination and testing
        required_teams.extend(["task-coordinator", "testing"])
        required_teams = list(set(required_teams))  # Remove duplicates

        print(f"📊 Analysis Results:")
        print(f"   Project Type: {project_type}")
        print(f"   Required Teams: {', '.join(required_teams)}")

        # Distribute tasks to identified teams
        distribution_results = {
            "project": project_description,
            "project_type": project_type,
            "required_teams": required_teams,
            "distribution_status": {}
        }

        for team in required_teams:
            task = f"""
INTELLIGENT TASK ASSIGNMENT - {team.upper()}

Project: {project_description}
Project Type: {project_type}
Your Role: Handle {team} aspects of this project

Please analyze your part and begin implementation.
Coordinate with other teams as needed.
"""

            success = self.send_task_to_claude(team, task)
            distribution_results["distribution_status"][team] = "sent" if success else "failed"

        return distribution_results

def main():
    """Test completo dell'orchestratore Claude-native"""

    print("🚀 CLAUDE-NATIVE CREWAI ORCHESTRATOR")
    print("=" * 60)
    print("Direct integration with Claude Code terminals")
    print("No OpenAI API needed - pure Claude coordination!")
    print()

    orchestrator = ClaudeNativeOrchestrator()

    # Test 1: Simple coordination
    print("🧪 TEST 1: System Status Check")
    progress = orchestrator.monitor_agent_progress()
    active_agents = len([a for a in progress["agents"].values() if a["status"] == "active"])
    print(f"📊 {active_agents}/{len(orchestrator.agent_ids)} agents active")

    # Test 2: Intelligent distribution
    print("\n🧪 TEST 2: Intelligent Task Distribution")
    test_project = "Create a user profile management system with Instagram integration and analytics dashboard"

    distribution = orchestrator.intelligent_task_distribution(test_project)
    print(f"✅ Task distributed to {len(distribution['required_teams'])} teams")

    # Wait a moment to see responses
    print("\n⏳ Waiting 5 seconds for agent responses...")
    time.sleep(5)

    # Test 3: Check some responses
    print("\n🧪 TEST 3: Agent Response Check")
    for team in ["task-coordinator", "backend-api"][:1]:  # Check one team
        if team in distribution["required_teams"]:
            print(f"\n📄 Response from {team}:")
            response = orchestrator.get_claude_response(team)
            # Show last few lines
            last_lines = response.split('\n')[-8:]
            for line in last_lines[-3:]:  # Last 3 lines
                if line.strip():
                    print(f"   {line[:80]}...")

    print("\n🎉 CLAUDE-NATIVE ORCHESTRATION COMPLETED!")
    print("Check your Claude agent terminals to see the coordination in action.")

if __name__ == "__main__":
    main()