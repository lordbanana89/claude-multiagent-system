#!/usr/bin/env python3
"""
LangChain + Claude Code CLI Integration - VERA SOLUZIONE
Basata su LangChain subprocess tools nativi trovati nella ricerca
"""

import os
import subprocess
import time
from typing import Dict, Any, List

# LangChain imports
try:
    from langchain.tools import BaseTool
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ LangChain import error: {e}")
    LANGCHAIN_AVAILABLE = False

class ClaudeCodeTool(BaseTool):
    """
    Custom LangChain tool che comunica con Claude Code CLI
    Basato sui pattern subprocess trovati nella documentazione LangChain
    """

    name: str = "claude_code_executor"
    description: str = """
    Execute tasks using Claude Code CLI.
    Send natural language prompts to Claude Code running in tmux terminal.
    Input should be a clear task description or question for Claude Code.
    """

    def __init__(self, tmux_session: str):
        super().__init__()
        self.tmux_session = tmux_session
        self.tmux_bin = "/opt/homebrew/bin/tmux"

    def _run(self, query: str) -> str:
        """Execute query using Claude Code CLI via tmux"""
        try:
            print(f"🤖 Executing via Claude Code ({self.tmux_session}): {query[:60]}...")

            # Send query to Claude Code terminal
            subprocess.run([
                self.tmux_bin, "send-keys", "-t", self.tmux_session,
                query, "Enter"
            ], check=True)

            # Wait for Claude Code to process
            time.sleep(5)

            # Capture response
            result = subprocess.run([
                self.tmux_bin, "capture-pane", "-t", self.tmux_session, "-p"
            ], capture_output=True, text=True, check=True)

            # Extract meaningful response
            response = self._extract_claude_response(result.stdout, query)
            print(f"📋 Claude Code response: {response[:100]}...")

            return response

        except Exception as e:
            error_msg = f"Error executing Claude Code task: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    def _extract_claude_response(self, terminal_output: str, original_query: str) -> str:
        """Extract Claude's response from terminal output"""
        lines = terminal_output.split('\n')

        # Find meaningful response lines
        response_lines = []
        found_query = False

        for line in lines:
            # Skip the query line we just sent
            if original_query[:30] in line:
                found_query = True
                continue

            # Collect meaningful lines after our query
            if found_query and line.strip():
                # Filter out tmux formatting
                clean_line = line.strip()
                if (clean_line and
                    not clean_line.startswith('─') and
                    not clean_line.startswith('│') and
                    '>' not in clean_line):
                    response_lines.append(clean_line)

        if response_lines:
            # Return last few meaningful lines
            return '\n'.join(response_lines[-3:])
        else:
            return f"Claude Code in {self.tmux_session} has received and processed your task. Check the terminal for detailed output."

class LangChainClaudeSystem:
    """
    Multi-agent system usando LangChain con Claude Code CLI integration
    """

    def __init__(self):
        self.claude_sessions = {
            "backend_api": "claude-backend-api",
            "frontend_ui": "claude-frontend-ui",
            "database": "claude-database",
            "testing": "claude-testing",
            "instagram": "claude-instagram",
            "queue_manager": "claude-queue-manager",
            "deployment": "claude-deployment"
        }

        # Use ChatOpenAI for coordination
        if LANGCHAIN_AVAILABLE:
            self.llm = ChatOpenAI(temperature=0.1, model="gpt-3.5-turbo")
        else:
            self.llm = None

    def create_claude_tools(self) -> List[Tool]:
        """Create LangChain tools for each Claude Code terminal"""
        tools = []

        for role, session in self.claude_sessions.items():
            tool = ClaudeCodeTool(tmux_session=session)
            tool.name = f"claude_{role}"
            tool.description = f"""
            Execute {role.replace('_', ' ')} related tasks using Claude Code CLI.
            Specialized in {role.replace('_', ' ')} development, analysis, and implementation.
            Send clear, specific tasks related to {role.replace('_', ' ')}.
            """
            tools.append(tool)

        return tools

    def create_coordinated_agent(self) -> AgentExecutor:
        """Create LangChain agent with Claude Code tools"""

        tools = self.create_claude_tools()

        # Create prompt template for multi-agent coordination
        prompt = PromptTemplate.from_template("""
        You are a Multi-Agent Project Coordinator with access to specialized Claude Code agents.

        Available Claude Code specialists:
        {tools}

        For any project or task:
        1. Analyze what needs to be done
        2. Identify which Claude Code specialists are needed
        3. Delegate specific tasks to appropriate specialists
        4. Coordinate their responses into a coherent plan

        Current task: {input}

        {agent_scratchpad}
        """)

        # Create ReAct agent
        agent = create_react_agent(self.llm, tools, prompt)

        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )

        return agent_executor

    def coordinate_project(self, project_description: str) -> Dict[str, Any]:
        """
        Coordinate a complete project using LangChain + Claude Code agents
        """

        print("🚀 LANGCHAIN + CLAUDE CODE MULTI-AGENT COORDINATION")
        print(f"📋 Project: {project_description}")
        print("=" * 70)

        try:
            # Create coordinated agent system
            agent_executor = self.create_coordinated_agent()

            # Execute project coordination
            print("⚡ Starting LangChain coordination with Claude Code agents...")

            result = agent_executor.invoke({
                "input": f"""
                Coordinate the complete development of this project: {project_description}

                Please:
                1. Break down the project into specialized tasks
                2. Assign tasks to appropriate Claude Code specialists
                3. Gather their responses and create a coordinated implementation plan
                4. Ensure all aspects (backend, frontend, database, testing) are covered
                """
            })

            return {
                "success": True,
                "result": result["output"],
                "project": project_description,
                "agents_used": len(self.claude_sessions),
                "coordination_method": "LangChain + Claude Code CLI"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "project": project_description
            }

def main():
    """Test LangChain + Claude Code integration"""

    print("🧪 TESTING LANGCHAIN + CLAUDE CODE INTEGRATION")
    print("=" * 60)
    print("Using LangChain subprocess tools with Claude Code CLI")
    print()

    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: OPENAI_API_KEY not set")
        print("💡 For full functionality, set: export OPENAI_API_KEY=your_key")
        print("🔄 Continuing with limited coordination capabilities...")

    # Initialize system
    system = LangChainClaudeSystem()

    # Test project
    test_project = """
    Create an Instagram analytics and automation platform with:
    - Real-time engagement tracking dashboard
    - Automated content scheduling
    - AI-powered content optimization
    - User management and authentication
    - Database for storing analytics data
    - API endpoints for mobile app integration
    """

    # Execute coordination
    result = system.coordinate_project(test_project)

    # Display results
    if result["success"]:
        print("🎉 SUCCESS: LangChain + Claude Code coordination completed!")
        print(f"📊 Project: {result['project'][:100]}...")
        print(f"🤖 Agents involved: {result['agents_used']}")
        print(f"🔧 Method: {result['coordination_method']}")
        print("\n📄 Coordination Result:")
        print("=" * 50)
        print(result["result"])
    else:
        print(f"❌ FAILED: {result['error_type']}")
        print(f"💬 Error: {result['error']}")
        print("\n🔍 This helps identify what needs to be configured.")

if __name__ == "__main__":
    main()