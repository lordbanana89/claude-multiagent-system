#!/usr/bin/env python3
"""
CrewAI Integration for Riona AI Multi-Agent System
Integrates CrewAI framework with existing tmux-based agent architecture
"""

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import subprocess
import json
import os
from typing import Dict, List, Optional
import time

class TmuxIntegrationTool(BaseTool):
    """Tool for integrating with tmux sessions and existing agent architecture"""

    name: str = "Tmux Agent Integration"
    description: str = "Interact with tmux sessions and existing Claude Code agents in the Riona AI system"

    def _run(self, agent_name: str, command: str, wait_for_response: bool = True) -> str:
        """Send command to tmux session and optionally wait for response"""
        try:
            # Send command to tmux session
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", agent_name, command
            ], check=True, capture_output=True)

            # Wait for command to be processed, then send Enter
            import time
            time.sleep(0.1)  # Short delay to let command be processed
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", agent_name, "Enter"
            ], check=True, capture_output=True)

            if wait_for_response:
                time.sleep(2)  # Wait for processing
                # Capture pane content
                capture_command = [
                    "/opt/homebrew/bin/tmux", "capture-pane", "-t", agent_name, "-p"
                ]
                result = subprocess.run(capture_command, capture_output=True, text=True)
                return result.stdout

            return f"Command sent to {agent_name} session"

        except subprocess.CalledProcessError as e:
            return f"Error communicating with {agent_name}: {e}"

class AuthorizationTool(BaseTool):
    """Tool for managing authorization requests in the hierarchical system"""

    name: str = "Authorization Manager"
    description: str = "Create and manage authorization requests in the hierarchical agent system"

    def _run(self, sub_agent: str, pm_agent: str, task_description: str) -> str:
        """Create authorization request"""
        try:
            auth_script = "/Users/erik/Desktop/riona_ai/riona-ai/.riona/agents/authorization/authorization-system.sh"
            command = [auth_script, "create", sub_agent, pm_agent, task_description]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Authorization error: {e.stderr}"

class RionaAIAgentCreator:
    """Creates CrewAI agents that integrate with existing Riona AI architecture"""

    def __init__(self):
        self.project_root = "/Users/erik/Desktop/riona_ai/riona-ai"
        self.agents_dir = f"{self.project_root}/.riona/agents"
        self.tmux_tool = TmuxIntegrationTool()
        self.auth_tool = AuthorizationTool()

    def create_task_coordinator_crew(self) -> Crew:
        """Create enhanced Task Coordinator crew with CrewAI"""

        # Task Coordinator PM Agent
        task_coordinator = Agent(
            role='Task Coordinator & Project Manager',
            goal='Coordinate and distribute tasks across specialized agent teams in the Riona AI system',
            backstory="""You are the central Task Coordinator for the Riona AI Instagram automation platform.
            You manage a hierarchical system of 9 PM agents, each leading specialized teams.
            Your role is to analyze incoming tasks, determine which teams are needed, and coordinate
            the execution while maintaining the authorization chain.""",
            tools=[self.tmux_tool, self.auth_tool],
            verbose=True,
            max_iter=5
        )

        # Project Planner Sub-Agent
        project_planner = Agent(
            role='Project Planning Specialist',
            goal='Break down complex projects into manageable tasks and create execution timelines',
            backstory="""You specialize in project breakdown, timeline estimation, and dependency mapping.
            You work closely with the Task Coordinator to analyze project requirements and create
            detailed implementation plans for the development teams.""",
            tools=[self.tmux_tool],
            verbose=True
        )

        # Resource Allocator Sub-Agent
        resource_allocator = Agent(
            role='Resource Allocation Specialist',
            goal='Optimize resource allocation across agent teams and manage capacity planning',
            backstory="""You manage resource allocation across the 9 PM teams and their sub-agents.
            You ensure optimal workload distribution and identify potential bottlenecks before they occur.""",
            tools=[self.tmux_tool],
            verbose=True
        )

        # Define tasks for the crew
        coordinate_task = Task(
            description="""Analyze incoming project request and determine which agent teams are required.
            Create a coordination plan that includes:
            1. Team assignments and responsibilities
            2. Task dependencies and execution order
            3. Authorization requirements for sub-agents
            4. Timeline and milestone planning

            Work with project planner and resource allocator to ensure comprehensive planning.""",
            expected_output="Detailed coordination plan with team assignments and execution timeline",
            agent=task_coordinator
        )

        planning_task = Task(
            description="""Create detailed project breakdown with tasks, subtasks, and dependencies.
            Include realistic time estimates and identify critical path items.""",
            expected_output="Comprehensive project breakdown with timeline and dependencies",
            agent=project_planner
        )

        allocation_task = Task(
            description="""Analyze team capacities and create resource allocation plan.
            Identify potential conflicts and suggest optimization strategies.""",
            expected_output="Resource allocation plan with capacity analysis",
            agent=resource_allocator
        )

        # Create the crew
        crew = Crew(
            agents=[task_coordinator, project_planner, resource_allocator],
            tasks=[coordinate_task, planning_task, allocation_task],
            process=Process.sequential,
            verbose=2
        )

        return crew

    def create_backend_api_crew(self) -> Crew:
        """Create Backend API development crew"""

        # Backend API PM
        backend_pm = Agent(
            role='Backend API Project Manager',
            goal='Coordinate backend development across specialized team members',
            backstory="""You manage a team of backend specialists including API architects,
            endpoint developers, middleware specialists, auth/security experts, and performance optimizers.""",
            tools=[self.tmux_tool, self.auth_tool],
            verbose=True
        )

        # API Architect
        api_architect = Agent(
            role='API Architecture Specialist',
            goal='Design and architect RESTful APIs and microservices patterns',
            backstory="""You specialize in API design, OpenAPI specifications, and microservices architecture.
            You create the foundation for scalable backend systems.""",
            tools=[self.tmux_tool],
            verbose=True
        )

        # Endpoint Developer
        endpoint_developer = Agent(
            role='Endpoint Development Specialist',
            goal='Implement REST API endpoints with proper validation and error handling',
            backstory="""You implement the API endpoints designed by the architect, ensuring
            proper validation, error handling, and integration with the database layer.""",
            tools=[self.tmux_tool],
            verbose=True
        )

        # Define backend tasks
        architecture_task = Task(
            description="""Design API architecture for the requested feature including:
            1. Endpoint structure and naming conventions
            2. Request/response schemas
            3. Authentication and authorization patterns
            4. Database integration points""",
            expected_output="Complete API architecture specification",
            agent=api_architect
        )

        implementation_task = Task(
            description="""Implement the API endpoints based on the architecture specification.
            Include proper validation, error handling, and documentation.""",
            expected_output="Implemented API endpoints with tests",
            agent=endpoint_developer
        )

        # Create backend crew
        backend_crew = Crew(
            agents=[backend_pm, api_architect, endpoint_developer],
            tasks=[architecture_task, implementation_task],
            process=Process.sequential,
            verbose=2
        )

        return backend_crew

    def create_frontend_ui_crew(self) -> Crew:
        """Create Frontend UI development crew"""

        # Frontend UI PM
        frontend_pm = Agent(
            role='Frontend UI Project Manager',
            goal='Coordinate frontend development across UI specialists',
            backstory="""You manage a team of frontend specialists including UI architects,
            component developers, state managers, styling specialists, and accessibility experts.""",
            tools=[self.tmux_tool, self.auth_tool],
            verbose=True
        )

        # UI Architect
        ui_architect = Agent(
            role='UI Architecture Specialist',
            goal='Design scalable frontend architecture and component hierarchies',
            backstory="""You specialize in React architecture, component design patterns,
            and creating maintainable frontend structures.""",
            tools=[self.tmux_tool],
            verbose=True
        )

        # Component Developer
        component_developer = Agent(
            role='Component Development Specialist',
            goal='Implement reusable React components with TypeScript',
            backstory="""You implement the UI components designed by the architect,
            ensuring proper TypeScript typing and reusability.""",
            tools=[self.tmux_tool],
            verbose=True
        )

        # Define frontend tasks
        ui_architecture_task = Task(
            description="""Design frontend architecture for the requested feature including:
            1. Component hierarchy and relationships
            2. State management patterns
            3. Routing structure
            4. Integration with backend APIs""",
            expected_output="Complete frontend architecture specification",
            agent=ui_architect
        )

        component_implementation_task = Task(
            description="""Implement the React components based on the architecture specification.
            Include proper TypeScript types, state management, and styling.""",
            expected_output="Implemented React components with TypeScript",
            agent=component_developer
        )

        # Create frontend crew
        frontend_crew = Crew(
            agents=[frontend_pm, ui_architect, component_developer],
            tasks=[ui_architecture_task, component_implementation_task],
            process=Process.sequential,
            verbose=2
        )

        return frontend_crew

class RionaAIOrchestrator:
    """Main orchestrator that manages CrewAI crews and integrates with existing system"""

    def __init__(self):
        self.creator = RionaAIAgentCreator()
        self.active_crews: Dict[str, Crew] = {}

    def initialize_crews(self):
        """Initialize all crews for the Riona AI system"""
        print("🚀 Initializing CrewAI integration for Riona AI...")

        # Create crews
        self.active_crews['task-coordinator'] = self.creator.create_task_coordinator_crew()
        self.active_crews['backend-api'] = self.creator.create_backend_api_crew()
        self.active_crews['frontend-ui'] = self.creator.create_frontend_ui_crew()

        print(f"✅ Initialized {len(self.active_crews)} crews")

    def execute_project_task(self, project_type: str, description: str) -> Dict:
        """Execute a project task using the appropriate crews"""
        print(f"📋 Executing {project_type} project: {description}")

        # Start with task coordinator crew
        coordinator_crew = self.active_crews.get('task-coordinator')
        if not coordinator_crew:
            return {"error": "Task coordinator crew not initialized"}

        try:
            # Execute coordination phase
            coordination_result = coordinator_crew.kickoff(inputs={
                'project_type': project_type,
                'description': description,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })

            print("✅ Task coordination completed")

            # Based on project type, execute appropriate specialized crews
            results = {'coordination': coordination_result}

            if project_type in ['full-stack-feature', 'backend-feature']:
                backend_crew = self.active_crews.get('backend-api')
                if backend_crew:
                    backend_result = backend_crew.kickoff(inputs={
                        'feature_description': description,
                        'coordination_plan': coordination_result
                    })
                    results['backend'] = backend_result
                    print("✅ Backend development completed")

            if project_type in ['full-stack-feature', 'frontend-feature']:
                frontend_crew = self.active_crews.get('frontend-ui')
                if frontend_crew:
                    frontend_result = frontend_crew.kickoff(inputs={
                        'feature_description': description,
                        'coordination_plan': coordination_result
                    })
                    results['frontend'] = frontend_result
                    print("✅ Frontend development completed")

            return results

        except Exception as e:
            return {"error": f"Project execution failed: {str(e)}"}

    def get_system_status(self) -> Dict:
        """Get status of all crews and integration points"""
        return {
            'crews': list(self.active_crews.keys()),
            'tmux_integration': True,
            'authorization_system': True,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }

def main():
    """Main function for testing the integration"""
    orchestrator = RionaAIOrchestrator()
    orchestrator.initialize_crews()

    # Test project execution
    test_result = orchestrator.execute_project_task(
        'full-stack-feature',
        'Create user profile management system with Instagram integration'
    )

    print("\n📊 Project Execution Results:")
    print(json.dumps(test_result, indent=2, default=str))

if __name__ == "__main__":
    main()