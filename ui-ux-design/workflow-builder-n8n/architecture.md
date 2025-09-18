# Workflow Builder Architecture - n8n Style

## 🏗️ Architettura Completa Sistema Workflow

### Core Components

```typescript
// Tipo principale per i nodi del workflow
interface WorkflowNode {
  id: string;
  type: NodeType;
  position: Position;
  data: NodeData;
  inputs: NodePort[];
  outputs: NodePort[];
  execution?: ExecutionData;
}

// Sistema di connessioni tra nodi
interface Connection {
  id: string;
  source: PortReference;
  target: PortReference;
  type: ConnectionType;
  data?: DataFlow;
  conditions?: ExecutionCondition[];
}

// Workflow completo
interface Workflow {
  id: string;
  name: string;
  description: string;
  version: string;
  nodes: Map<string, WorkflowNode>;
  connections: Map<string, Connection>;
  variables: WorkflowVariables;
  settings: WorkflowSettings;
  triggers: TriggerConfiguration[];
}
```

## 📦 Node Types Library

### 1. Core Nodes

```yaml
trigger_nodes:
  - webhook:
      inputs: []
      outputs: [data, headers, params]
      config:
        method: [GET, POST, PUT, DELETE]
        path: string
        authentication: boolean

  - schedule:
      inputs: []
      outputs: [timestamp, iteration]
      config:
        cron: string
        timezone: string

  - manual:
      inputs: []
      outputs: [user_data]
      config:
        form_fields: Field[]

  - event:
      inputs: []
      outputs: [event_data]
      config:
        source: string
        event_type: string
        filters: Filter[]

agent_nodes:
  - claude_agent:
      inputs: [task, context, parameters]
      outputs: [result, status, logs]
      config:
        agent_id: string
        timeout: number
        retry: RetryConfig

  - specialist_agent:
      inputs: [specialization, task, data]
      outputs: [analysis, recommendations, actions]
      config:
        type: [backend, database, frontend, testing]
        capabilities: string[]

logic_nodes:
  - condition:
      inputs: [data]
      outputs: [true_branch, false_branch]
      config:
        conditions: Condition[]
        logic: AND | OR

  - switch:
      inputs: [value]
      outputs: dynamic<case_branches>
      config:
        cases: Case[]
        default: boolean

  - loop:
      inputs: [items, iterator]
      outputs: [item, index, done]
      config:
        type: [for, while, foreach]
        break_condition: string

  - merge:
      inputs: dynamic<branches>
      outputs: [merged_data]
      config:
        strategy: [combine, override, append]
        key: string

transform_nodes:
  - mapper:
      inputs: [input_data]
      outputs: [mapped_data]
      config:
        mapping: MappingRules

  - filter:
      inputs: [array]
      outputs: [filtered_array]
      config:
        conditions: FilterCondition[]

  - aggregate:
      inputs: [data_stream]
      outputs: [aggregated_result]
      config:
        operation: [sum, avg, count, min, max, group_by]
        field: string
```

## 🎨 Visual Workflow Editor Components

### Canvas Component

```tsx
// WorkflowCanvas.tsx
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
} from 'reactflow';

const WorkflowCanvas = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('nodeType');
      const position = reactFlowInstance.project({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = createNode(type, position);
      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance]
  );

  return (
    <ReactFlowProvider>
      <div className="workflow-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes}
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          snapToGrid
          snapGrid={[15, 15]}
        >
          <Background variant="dots" gap={12} size={1} />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
};
```

### Custom Node Components

```tsx
// nodes/AgentNode.tsx
import { Handle, Position } from 'reactflow';

const AgentNode = ({ data, selected }) => {
  return (
    <div className={`agent-node ${selected ? 'selected' : ''}`}>
      <Handle
        type="target"
        position={Position.Left}
        id="task-input"
        style={{ top: '30%' }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="context-input"
        style={{ top: '70%' }}
      />

      <div className="node-header">
        <span className="node-icon">{data.icon}</span>
        <span className="node-title">{data.label}</span>
      </div>

      <div className="node-body">
        <div className="agent-type">{data.agentType}</div>
        <div className="agent-status">
          <span className={`status-dot ${data.status}`}></span>
          {data.status}
        </div>
      </div>

      <div className="node-config">
        <button className="config-btn" onClick={data.onConfig}>
          ⚙️
        </button>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        id="result-output"
        style={{ top: '30%' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="status-output"
        style={{ top: '70%' }}
      />
    </div>
  );
};
```

## 🔧 Workflow Execution Engine

### Execution Flow

```python
# workflow_executor.py
from typing import Dict, Any, List
from asyncio import create_task, gather
from dataclasses import dataclass

@dataclass
class ExecutionContext:
    workflow_id: str
    execution_id: str
    variables: Dict[str, Any]
    node_results: Dict[str, Any]
    connections_map: Dict[str, List[Connection]]

class WorkflowExecutor:
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.execution_graph = self._build_execution_graph()

    async def execute(self, trigger_data: Dict[str, Any]) -> ExecutionResult:
        context = ExecutionContext(
            workflow_id=self.workflow.id,
            execution_id=generate_uuid(),
            variables=self.workflow.variables,
            node_results={},
            connections_map=self._build_connections_map()
        )

        # Find start nodes (triggers)
        start_nodes = self._find_start_nodes()

        # Execute workflow
        for node in start_nodes:
            await self._execute_node_tree(node, trigger_data, context)

        return ExecutionResult(
            success=True,
            data=context.node_results,
            execution_id=context.execution_id
        )

    async def _execute_node_tree(
        self,
        node: WorkflowNode,
        input_data: Any,
        context: ExecutionContext
    ):
        # Execute current node
        result = await self._execute_single_node(node, input_data, context)
        context.node_results[node.id] = result

        # Find connected nodes
        next_nodes = self._get_next_nodes(node.id)

        # Execute next nodes in parallel if possible
        if len(next_nodes) > 1:
            tasks = [
                create_task(
                    self._execute_node_tree(next_node, result, context)
                )
                for next_node in next_nodes
            ]
            await gather(*tasks)
        elif next_nodes:
            await self._execute_node_tree(next_nodes[0], result, context)

    async def _execute_single_node(
        self,
        node: WorkflowNode,
        input_data: Any,
        context: ExecutionContext
    ) -> Any:
        executor = self._get_node_executor(node.type)
        return await executor.execute(node, input_data, context)
```

### Node Executors

```python
# executors/agent_executor.py
class AgentNodeExecutor:
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager

    async def execute(
        self,
        node: WorkflowNode,
        input_data: Any,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        agent_id = node.data.get('agent_id')
        task = self._prepare_task(input_data, node.data)

        # Get agent instance
        agent = self.agent_manager.get_agent(agent_id)

        # Execute task with timeout
        try:
            result = await asyncio.wait_for(
                agent.execute_task(task),
                timeout=node.data.get('timeout', 300)
            )

            return {
                'success': True,
                'result': result,
                'execution_time': time.time() - start_time,
                'agent_id': agent_id
            }
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'Task timeout',
                'agent_id': agent_id
            }
```

## 🗄️ Data Flow Management

### Variable System

```typescript
interface WorkflowVariables {
  global: Map<string, Variable>;
  nodeSpecific: Map<string, Map<string, Variable>>;
}

interface Variable {
  name: string;
  type: VariableType;
  value: any;
  source?: VariableSource;
  scope: 'global' | 'local' | 'node';
  mutable: boolean;
}

enum VariableType {
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  ARRAY = 'array',
  OBJECT = 'object',
  DATE = 'date',
  FILE = 'file'
}

interface VariableSource {
  type: 'input' | 'node_output' | 'external' | 'computed';
  reference?: string;
  transformer?: DataTransformer;
}
```

### Data Transformation

```javascript
// Transform Pipeline
class TransformPipeline {
  constructor() {
    this.transformers = new Map();
    this.registerBuiltinTransformers();
  }

  registerTransformer(name, transformer) {
    this.transformers.set(name, transformer);
  }

  async transform(data, pipeline) {
    let result = data;

    for (const step of pipeline) {
      const transformer = this.transformers.get(step.type);
      if (!transformer) {
        throw new Error(`Unknown transformer: ${step.type}`);
      }

      result = await transformer(result, step.config);
    }

    return result;
  }

  registerBuiltinTransformers() {
    // JSON Path extraction
    this.registerTransformer('jsonpath', (data, config) => {
      return JSONPath.query(data, config.path);
    });

    // JavaScript expression
    this.registerTransformer('expression', (data, config) => {
      const fn = new Function('$', 'return ' + config.expression);
      return fn(data);
    });

    // Template string
    this.registerTransformer('template', (data, config) => {
      return config.template.replace(/\{\{(.*?)\}\}/g, (match, path) => {
        return _.get(data, path.trim());
      });
    });

    // Array operations
    this.registerTransformer('array.map', (data, config) => {
      return data.map(item => this.transform(item, config.pipeline));
    });

    this.registerTransformer('array.filter', (data, config) => {
      return data.filter(item => {
        const fn = new Function('$', 'return ' + config.condition);
        return fn(item);
      });
    });

    // Object operations
    this.registerTransformer('object.pick', (data, config) => {
      return _.pick(data, config.fields);
    });

    this.registerTransformer('object.merge', (data, config) => {
      return _.merge({}, data, config.additional);
    });
  }
}
```

## 🎯 Advanced Features

### 1. Workflow Templates

```yaml
templates:
  - id: "auth-flow"
    name: "Authentication Workflow"
    description: "Complete user authentication with JWT"
    category: "Security"
    nodes:
      - trigger:
          type: "http"
          config:
            path: "/auth/login"
            method: "POST"
      - validator:
          type: "agent"
          agent_type: "backend"
          task: "Validate credentials"
      - database:
          type: "agent"
          agent_type: "database"
          task: "Query user data"
      - jwt:
          type: "action"
          action: "generate_jwt"
      - response:
          type: "http_response"

  - id: "data-pipeline"
    name: "ETL Data Pipeline"
    description: "Extract, transform, and load data"
    category: "Data"
    nodes:
      - extract:
          type: "database_query"
      - transform:
          type: "mapper"
      - validate:
          type: "filter"
      - load:
          type: "database_insert"
```

### 2. Collaborative Editing

```typescript
// Real-time collaboration using CRDTs
interface CollaborativeSession {
  sessionId: string;
  workflowId: string;
  participants: Participant[];
  operations: CRDT.Operation[];

  // Methods
  addParticipant(user: User): void;
  applyOperation(op: CRDT.Operation): void;
  syncState(): WorkflowState;
  resolveConflict(conflict: Conflict): Resolution;
}

// WebSocket events for collaboration
enum CollaborationEvent {
  NODE_ADDED = 'node:added',
  NODE_UPDATED = 'node:updated',
  NODE_DELETED = 'node:deleted',
  CONNECTION_CREATED = 'connection:created',
  CONNECTION_DELETED = 'connection:deleted',
  CURSOR_MOVED = 'cursor:moved',
  SELECTION_CHANGED = 'selection:changed'
}
```

### 3. Version Control

```typescript
interface WorkflowVersion {
  id: string;
  workflowId: string;
  version: string;
  changes: Change[];
  author: User;
  timestamp: Date;
  message: string;
  tags: string[];
}

interface Change {
  type: 'add' | 'modify' | 'delete';
  target: 'node' | 'connection' | 'variable';
  targetId: string;
  before?: any;
  after?: any;
}

class WorkflowVersionControl {
  createVersion(workflow: Workflow, message: string): WorkflowVersion;
  compareVersions(v1: string, v2: string): VersionDiff;
  rollback(workflowId: string, versionId: string): void;
  merge(branch1: string, branch2: string): MergeResult;
}
```

### 4. Testing & Debugging

```typescript
interface WorkflowTest {
  id: string;
  name: string;
  workflow: Workflow;
  testCases: TestCase[];
  assertions: Assertion[];
}

interface TestCase {
  id: string;
  name: string;
  input: any;
  expectedOutput: any;
  timeout: number;
}

interface DebugSession {
  sessionId: string;
  workflow: Workflow;
  breakpoints: Breakpoint[];
  stepMode: 'into' | 'over' | 'out';
  variables: Map<string, any>;
  callStack: NodeExecution[];
}

class WorkflowDebugger {
  setBreakpoint(nodeId: string): void;
  removeBreakpoint(nodeId: string): void;
  step(): Promise<DebugState>;
  continue(): Promise<void>;
  evaluateExpression(expr: string): any;
  inspectVariable(name: string): VariableInfo;
}
```

## 🚀 Performance Optimizations

### 1. Lazy Loading

```javascript
// Lazy load node definitions
const nodeRegistry = new Map();

async function loadNodeType(type) {
  if (!nodeRegistry.has(type)) {
    const module = await import(`./nodes/${type}.js`);
    nodeRegistry.set(type, module.default);
  }
  return nodeRegistry.get(type);
}
```

### 2. Execution Caching

```python
# Cache execution results
class ExecutionCache:
    def __init__(self, redis_client):
        self.redis = redis_client

    def cache_key(self, node_id: str, input_hash: str) -> str:
        return f"exec:{node_id}:{input_hash}"

    async def get_cached_result(self, node: Node, input_data: Any) -> Optional[Any]:
        input_hash = self.hash_input(input_data)
        key = self.cache_key(node.id, input_hash)

        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def cache_result(self, node: Node, input_data: Any, result: Any):
        input_hash = self.hash_input(input_data)
        key = self.cache_key(node.id, input_hash)

        await self.redis.setex(
            key,
            node.cache_ttl or 3600,
            json.dumps(result)
        )
```

### 3. Parallel Execution

```python
# Parallel node execution
async def execute_parallel_nodes(nodes: List[Node], context: Context):
    # Group nodes by dependency level
    levels = group_by_dependency_level(nodes)

    for level in levels:
        # Execute all nodes at the same level in parallel
        tasks = [
            execute_node(node, context)
            for node in level
        ]
        results = await asyncio.gather(*tasks)

        # Store results in context
        for node, result in zip(level, results):
            context.results[node.id] = result
```

## 📈 Monitoring & Analytics

```typescript
interface WorkflowMetrics {
  executionCount: number;
  averageExecutionTime: number;
  successRate: number;
  errorRate: number;
  nodeMetrics: Map<string, NodeMetrics>;
}

interface NodeMetrics {
  executionCount: number;
  averageExecutionTime: number;
  errorCount: number;
  lastExecution: Date;
  resourceUsage: ResourceMetrics;
}

class WorkflowMonitor {
  trackExecution(execution: WorkflowExecution): void;
  getMetrics(workflowId: string): WorkflowMetrics;
  getNodeMetrics(nodeId: string): NodeMetrics;
  generateReport(timeRange: TimeRange): AnalyticsReport;
  detectAnomalies(): Anomaly[];
  predictPerformance(workflow: Workflow): PerformancePrediction;
}
```

Questa architettura fornisce un sistema completo di workflow builder stile n8n, con tutte le funzionalità enterprise necessarie per gestire workflow complessi in un ambiente multi-agente.