"""
Workflow Engine for Claude Multi-Agent System
Orchestrates complex multi-step workflows across multiple agents
"""

import json
import time
import asyncio
import uuid
import yaml
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, Future
import logging

from core.message_bus import get_message_bus, MessagePriority
from agents.agent_bridge import get_bridge_manager
from config.settings import AGENT_SESSIONS

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    id: str
    name: str
    agent: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout: int = 300
    retry_on_failure: bool = True
    max_retries: int = 3
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class WorkflowDefinition:
    """Defines a complete workflow"""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class WorkflowExecution:
    """Tracks execution of a workflow"""
    id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.READY
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None


class WorkflowEngine:
    """
    Orchestrates complex multi-step workflows
    - Dependency resolution
    - Parallel/sequential execution
    - Error handling and rollback
    - Progress monitoring
    """

    def __init__(self):
        self.message_bus = get_message_bus()
        self.bridge_manager = get_bridge_manager()
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

        logger.info("WorkflowEngine initialized")

    def define_workflow(self, definition: Dict[str, Any]) -> str:
        """
        Define a new workflow from dictionary or YAML
        Returns workflow_id
        """
        workflow_id = definition.get('id', str(uuid.uuid4()))

        # Parse steps
        steps = []
        for step_def in definition.get('steps', []):
            step = WorkflowStep(
                id=step_def.get('id', str(uuid.uuid4())),
                name=step_def.get('name', step_def['action']),
                agent=step_def['agent'],
                action=step_def['action'],
                params=step_def.get('params', {}),
                depends_on=step_def.get('depends_on', []),
                timeout=step_def.get('timeout', 300),
                retry_on_failure=step_def.get('retry_on_failure', True),
                max_retries=step_def.get('max_retries', 3)
            )
            steps.append(step)

        # Validate workflow
        self._validate_workflow(steps)

        # Create workflow definition
        workflow = WorkflowDefinition(
            id=workflow_id,
            name=definition['name'],
            description=definition.get('description', ''),
            steps=steps,
            metadata=definition.get('metadata', {})
        )

        self.workflows[workflow_id] = workflow
        logger.info(f"Defined workflow: {workflow_id} - {workflow.name}")

        return workflow_id

    def load_workflow_from_yaml(self, yaml_path: str) -> str:
        """Load workflow definition from YAML file"""
        with open(yaml_path, 'r') as f:
            definition = yaml.safe_load(f)
        return self.define_workflow(definition)

    def execute(self, workflow_id: str, params: Dict[str, Any] = None) -> str:
        """
        Execute a workflow
        Returns execution_id for tracking
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")

        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())

        # Create execution instance
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            context=params or {},
            steps={step.id: WorkflowStep(**step.__dict__) for step in workflow.steps}
        )

        self.executions[execution_id] = execution

        # Start execution in background
        self.executor.submit(self._execute_workflow, execution)

        logger.info(f"Started workflow execution: {execution_id} for {workflow_id}")
        return execution_id

    def _execute_workflow(self, execution: WorkflowExecution):
        """Execute workflow steps respecting dependencies"""
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = time.time()

            # Broadcast workflow start event
            self.message_bus.broadcast_event("workflow_started", {
                "execution_id": execution.id,
                "workflow_id": execution.workflow_id,
                "context": execution.context
            })

            # Build dependency graph
            graph = self._build_dependency_graph(execution.steps.values())

            # Execute steps in topological order
            while graph.number_of_nodes() > 0:
                # Find steps ready to execute (no dependencies)
                ready_steps = [
                    node for node in graph.nodes()
                    if graph.in_degree(node) == 0
                ]

                if not ready_steps:
                    # Circular dependency or all remaining steps failed
                    raise Exception("No executable steps found - possible circular dependency")

                # Execute ready steps in parallel
                futures = []
                for step_id in ready_steps:
                    step = execution.steps[step_id]
                    if step.status == StepStatus.PENDING:
                        future = self.executor.submit(
                            self._execute_step, execution, step
                        )
                        futures.append((step_id, future))

                # Wait for parallel steps to complete
                for step_id, future in futures:
                    try:
                        future.result(timeout=execution.steps[step_id].timeout)
                        if execution.steps[step_id].status == StepStatus.COMPLETED:
                            # Remove completed step from graph
                            graph.remove_node(step_id)
                        elif not execution.steps[step_id].retry_on_failure:
                            # Step failed and no retry - fail workflow
                            raise Exception(f"Step {step_id} failed")
                    except Exception as e:
                        logger.error(f"Step {step_id} execution error: {e}")
                        execution.steps[step_id].status = StepStatus.FAILED
                        execution.steps[step_id].error = str(e)

                        # Check if workflow should continue
                        if not self._should_continue_on_failure(execution, step_id):
                            raise

            # Check if all steps completed successfully
            failed_steps = [
                s for s in execution.steps.values()
                if s.status == StepStatus.FAILED
            ]

            if failed_steps:
                execution.status = WorkflowStatus.FAILED
                execution.error = f"Steps failed: {[s.id for s in failed_steps]}"
            else:
                execution.status = WorkflowStatus.COMPLETED

            execution.completed_at = time.time()

            # Broadcast workflow completion
            self.message_bus.broadcast_event("workflow_completed", {
                "execution_id": execution.id,
                "status": execution.status.value,
                "duration": execution.completed_at - execution.started_at
            })

            logger.info(f"Workflow {execution.id} completed with status: {execution.status}")

        except Exception as e:
            logger.error(f"Workflow {execution.id} failed: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = time.time()

            # Broadcast workflow failure
            self.message_bus.broadcast_event("workflow_failed", {
                "execution_id": execution.id,
                "error": str(e)
            })

    def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep):
        """Execute a single workflow step"""
        retry_count = 0

        while retry_count <= step.max_retries:
            try:
                step.status = StepStatus.RUNNING
                step.started_at = time.time()

                # Broadcast step start
                self.message_bus.broadcast_event("step_started", {
                    "execution_id": execution.id,
                    "step_id": step.id,
                    "agent": step.agent,
                    "action": step.action
                })

                # Prepare parameters with context
                params = self._prepare_step_params(step, execution)

                # Publish task to agent
                task_id = self.message_bus.publish_task(
                    agent=step.agent,
                    task={
                        "command": step.action,
                        "params": params,
                        "timeout": step.timeout,
                        "workflow_execution_id": execution.id,
                        "step_id": step.id
                    },
                    priority=MessagePriority.HIGH
                )

                # Wait for result
                result = self._wait_for_task_result(task_id, step.timeout)

                if result and result['status'] == 'completed':
                    step.status = StepStatus.COMPLETED
                    step.result = result.get('result', {})
                    step.completed_at = time.time()

                    # Update execution context with step results
                    execution.context[f"step_{step.id}_result"] = step.result

                    # Broadcast step completion
                    self.message_bus.broadcast_event("step_completed", {
                        "execution_id": execution.id,
                        "step_id": step.id,
                        "duration": step.completed_at - step.started_at
                    })

                    logger.info(f"Step {step.id} completed successfully")
                    return

                else:
                    raise Exception(f"Task failed or timed out: {result}")

            except Exception as e:
                retry_count += 1
                logger.warning(f"Step {step.id} attempt {retry_count} failed: {e}")

                if retry_count <= step.max_retries and step.retry_on_failure:
                    # Exponential backoff
                    time.sleep(2 ** retry_count)
                else:
                    step.status = StepStatus.FAILED
                    step.error = str(e)
                    step.completed_at = time.time()

                    # Broadcast step failure
                    self.message_bus.broadcast_event("step_failed", {
                        "execution_id": execution.id,
                        "step_id": step.id,
                        "error": str(e),
                        "retry_count": retry_count
                    })

                    raise

    def _prepare_step_params(self, step: WorkflowStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """Prepare step parameters with context substitution"""
        params = step.params.copy()

        # Substitute context variables
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Context variable reference
                context_key = value[2:-1]
                if context_key in execution.context:
                    params[key] = execution.context[context_key]

        # Add workflow context
        params['_workflow'] = {
            'execution_id': execution.id,
            'step_id': step.id,
            'context': execution.context
        }

        return params

    def _wait_for_task_result(self, task_id: str, timeout: int) -> Optional[Dict[str, Any]]:
        """Wait for task completion"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.message_bus.get_task_status(task_id)
            if result and result['status'] in ['completed', 'failed']:
                return result
            time.sleep(1)

        return None

    def _build_dependency_graph(self, steps) -> nx.DiGraph:
        """Build directed graph of step dependencies"""
        graph = nx.DiGraph()

        # Add all steps as nodes
        for step in steps:
            graph.add_node(step.id, step=step)

        # Add dependency edges
        for step in steps:
            for dep_id in step.depends_on:
                if dep_id in graph:
                    graph.add_edge(dep_id, step.id)

        return graph

    def _validate_workflow(self, steps: List[WorkflowStep]):
        """Validate workflow definition"""
        step_ids = {step.id for step in steps}

        # Check for invalid dependencies
        for step in steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step.id} depends on unknown step {dep_id}")

        # Check for invalid agents
        for step in steps:
            if step.agent not in AGENT_SESSIONS:
                raise ValueError(f"Step {step.id} references unknown agent {step.agent}")

        # Check for circular dependencies
        graph = self._build_dependency_graph(steps)
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Workflow contains circular dependencies")

    def _should_continue_on_failure(self, execution: WorkflowExecution, failed_step_id: str) -> bool:
        """Determine if workflow should continue after step failure"""
        # Check if any pending steps depend on the failed step
        for step in execution.steps.values():
            if step.status == StepStatus.PENDING and failed_step_id in step.depends_on:
                # Mark dependent steps as skipped
                step.status = StepStatus.SKIPPED
                step.error = f"Skipped due to failure of dependency: {failed_step_id}"

        # Continue if there are still executable steps
        return any(
            s.status == StepStatus.PENDING and
            all(execution.steps[d].status == StepStatus.COMPLETED for d in s.depends_on)
            for s in execution.steps.values()
        )

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of workflow execution"""
        if execution_id not in self.executions:
            return None

        execution = self.executions[execution_id]
        return {
            'id': execution.id,
            'workflow_id': execution.workflow_id,
            'status': execution.status.value,
            'started_at': execution.started_at,
            'completed_at': execution.completed_at,
            'error': execution.error,
            'steps': {
                step_id: {
                    'name': step.name,
                    'status': step.status.value,
                    'agent': step.agent,
                    'started_at': step.started_at,
                    'completed_at': step.completed_at,
                    'error': step.error
                }
                for step_id, step in execution.steps.items()
            },
            'context': execution.context
        }

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        if execution_id not in self.executions:
            return False

        execution = self.executions[execution_id]
        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = time.time()

            # Cancel pending steps
            for step in execution.steps.values():
                if step.status in [StepStatus.PENDING, StepStatus.RUNNING]:
                    step.status = StepStatus.CANCELLED

            logger.info(f"Cancelled workflow execution: {execution_id}")
            return True

        return False


# Singleton instance
_workflow_engine = None

def get_workflow_engine() -> WorkflowEngine:
    """Get or create singleton workflow engine"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine