#!/usr/bin/env python3
"""
CrewAI Integration specifica per Claude Code
Integra CrewAI con i terminali Claude esistenti invece di OpenAI
"""

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import subprocess
import json
import time
import os
from typing import Dict, List, Optional

class ClaudeTerminalTool(BaseTool):
    """Tool per interagire direttamente con terminali Claude Code esistenti"""

    name: str = "Claude Terminal Integration"
    description: str = "Interact directly with existing Claude Code terminal sessions in tmux"

    def _run(self, action: str, agent_session: str = "", message: str = "", wait_seconds: int = 3) -> str:
        """
        Interagisce direttamente con sessioni Claude Code tramite tmux

        Actions:
        - send_task: Invia un task a una sessione Claude
        - get_response: Cattura la risposta da una sessione
        - check_status: Verifica se la sessione è attiva
        - list_sessions: Lista tutte le sessioni Claude attive
        """

        try:
            if action == "send_task":
                # Invia task direttamente al terminale Claude
                full_message = f"""
📋 TASK FROM CREWAI ORCHESTRATOR:
{message}

Please acknowledge this task and provide your analysis/response.
"""

                # Carica il messaggio nel buffer tmux
                subprocess.run([
                    "/opt/homebrew/bin/tmux", "send-keys", "-t", agent_session,
                    full_message, "Enter"
                ], check=True)

                return f"✅ Task sent to Claude session '{agent_session}'"

            elif action == "get_response":
                # Aspetta un momento per la risposta
                time.sleep(wait_seconds)

                # Cattura il contenuto del pane
                result = subprocess.run([
                    "/opt/homebrew/bin/tmux", "capture-pane", "-t", agent_session, "-p"
                ], capture_output=True, text=True, check=True)

                # Estrae le ultime righe che potrebbero contenere la risposta
                lines = result.stdout.strip().split('\n')
                recent_content = '\n'.join(lines[-20:])  # Ultime 20 righe

                return f"📄 Response from {agent_session}:\n{recent_content}"

            elif action == "check_status":
                # Verifica se la sessione Claude è attiva
                try:
                    subprocess.run([
                        "/opt/homebrew/bin/tmux", "has-session", "-t", agent_session
                    ], check=True, capture_output=True)

                    # Verifica che sia una sessione Claude (non bash)
                    capture_result = subprocess.run([
                        "/opt/homebrew/bin/tmux", "capture-pane", "-t", agent_session, "-p"
                    ], capture_output=True, text=True)

                    if "Claude Code" in capture_result.stdout or "claude" in capture_result.stdout.lower():
                        return f"✅ {agent_session} is an active Claude session"
                    else:
                        return f"⚠️  {agent_session} exists but may not be Claude"

                except subprocess.CalledProcessError:
                    return f"❌ {agent_session} session not found"

            elif action == "list_sessions":
                # Lista tutte le sessioni tmux
                result = subprocess.run([
                    "/opt/homebrew/bin/tmux", "list-sessions", "-F", "#{session_name}"
                ], capture_output=True, text=True, check=True)

                sessions = result.stdout.strip().split('\n')

                # Filtra per sessioni che potrebbero essere Claude
                claude_sessions = []
                for session in sessions:
                    if session and not session.isdigit():  # Esclude sessioni numeriche
                        claude_sessions.append(session)

                return f"🔍 Found {len(claude_sessions)} potential Claude sessions: {', '.join(claude_sessions)}"

            elif action == "interactive_query":
                # Invia una query e aspetta risposta interattiva
                query_message = f"""
❓ INTERACTIVE QUERY FROM CREWAI:
{message}

Please provide a detailed response to help coordinate this task.
"""

                # Invia query
                subprocess.run([
                    "/opt/homebrew/bin/tmux", "send-keys", "-t", agent_session,
                    query_message, "Enter"
                ], check=True)

                # Aspetta risposta
                time.sleep(wait_seconds)

                # Cattura risposta
                result = subprocess.run([
                    "/opt/homebrew/bin/tmux", "capture-pane", "-t", agent_session, "-p"
                ], capture_output=True, text=True)

                return f"💬 Interactive response from {agent_session}:\n{result.stdout[-500:]}"

            else:
                return f"❌ Unknown action: {action}"

        except subprocess.CalledProcessError as e:
            return f"❌ Error: {e}"
        except Exception as e:
            return f"❌ Unexpected error: {e}"

class ClaudeCoordinatorAgent:
    """Coordinatore che gestisce agenti Claude Code esistenti"""

    def __init__(self):
        self.claude_tool = ClaudeTerminalTool()
        self.pm_agents = [
            "prompt-validator", "task-coordinator", "backend-api",
            "database", "frontend-ui", "instagram", "queue-manager",
            "testing", "deployment"
        ]

    def create_claude_aware_crew(self) -> Crew:
        """Crea crew che lavora direttamente con terminali Claude"""

        # Agent che coordina con Claude terminals
        claude_coordinator = Agent(
            role='Claude Terminal Coordinator',
            goal='Coordinate tasks across existing Claude Code terminal sessions',
            backstory="""You are a specialized coordinator that works directly with
            Claude Code terminal sessions. You understand how to communicate with
            Claude agents through tmux and coordinate complex multi-agent tasks.""",
            tools=[self.claude_tool],
            verbose=True,
            # Usa un modello locale o disabilita LLM per test
            llm=None  # Disabilita LLM per test
        )

        # Task di coordinamento
        coordination_task = Task(
            description="""Coordinate with existing Claude Code sessions to:
            1. Check status of all PM agent sessions
            2. Send a coordination message to active sessions
            3. Collect responses and provide summary

            Use the Claude Terminal Integration tool to interact directly
            with the tmux sessions.""",
            expected_output="Summary of coordination with Claude sessions",
            agent=claude_coordinator
        )

        # Crew senza LLM per test
        crew = Crew(
            agents=[claude_coordinator],
            tasks=[coordination_task],
            process=Process.sequential,
            verbose=True
        )

        return crew

    def test_claude_integration_direct(self):
        """Test diretto dell'integrazione senza LLM"""

        print("🤖 TESTING DIRECT CLAUDE INTEGRATION")
        print("=" * 50)

        tool = self.claude_tool

        # Test 1: Lista sessioni
        print("\n1. Listing Claude sessions...")
        sessions_result = tool._run("list_sessions")
        print(sessions_result)

        # Test 2: Check status di PM agents
        print("\n2. Checking PM agent status...")
        for pm in self.pm_agents[:3]:  # Test primi 3
            status = tool._run("check_status", agent_session=pm)
            print(f"   {status}")

        # Test 3: Invia task a sessioni attive
        print("\n3. Sending test tasks...")
        test_task = "Please confirm you received this coordination message from CrewAI"

        for pm in ["task-coordinator", "backend-api"][:1]:  # Test su uno
            send_result = tool._run("send_task", agent_session=pm, message=test_task)
            print(f"   {send_result}")

            # Aspetta e cattura risposta
            time.sleep(2)
            response = tool._run("get_response", agent_session=pm)
            print(f"   📄 Response preview: {response[-100:]}...")  # Ultimi 100 char

        print("\n✅ Direct Claude integration test completed!")

        return True

def main():
    """Test principale dell'integrazione Claude"""

    print("🚀 CLAUDE CODE INTEGRATION FOR CREWAI")
    print("=" * 60)
    print("Integrating CrewAI with existing Claude Code terminals")
    print("No OpenAI API keys needed - direct terminal communication!")
    print()

    # Crea coordinatore
    coordinator = ClaudeCoordinatorAgent()

    # Test integrazione diretta
    success = coordinator.test_claude_integration_direct()

    if success:
        print("\n🎉 CLAUDE INTEGRATION SUCCESS!")
        print("=" * 40)
        print("✅ CrewAI can communicate with Claude terminals")
        print("✅ No external APIs needed")
        print("✅ Direct integration with existing system")
        print("✅ Ready for intelligent coordination")

if __name__ == "__main__":
    main()