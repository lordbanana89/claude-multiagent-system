# 🔧 INTEGRAZIONE STREAMLIT-REACT - Guida Pratica

## Setup Componente React in Streamlit

### 1. Struttura Base Componente

```python
# workflow_builder_component.py
import streamlit.components.v1 as components
import os

# Dichiarazione componente
_RELEASE = True

if not _RELEASE:
    # Development mode
    _component_func = components.declare_component(
        "workflow_builder",
        url="http://localhost:3001"  # React dev server
    )
else:
    # Production mode
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component(
        "workflow_builder",
        path=build_dir
    )

def workflow_builder(agents=None, workflows=None, height=600, key=None):
    """Create workflow builder component"""

    component_value = _component_func(
        agents=agents,
        workflows=workflows,
        height=height,
        key=key,
        default=None
    )

    return component_value
```

### 2. React Component Setup

```bash
# Create React component
mkdir -p interfaces/web/components/workflow-builder/frontend
cd interfaces/web/components/workflow-builder/frontend

# Initialize React with TypeScript
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install \
    @streamlit/component \
    reactflow \
    zustand \
    axios
```

### 3. React Component Implementation

```tsx
// src/StreamlitWorkflowBuilder.tsx
import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection
} from "@streamlit/component"
import React from "react"
import ReactFlow, { Node, Edge } from 'reactflow'
import 'reactflow/dist/style.css'

interface Props {
  agents: string[]
  workflows: any[]
  height: number
}

class StreamlitWorkflowBuilder extends StreamlitComponentBase<{}, Props> {
  state = {
    nodes: [],
    edges: [],
    selectedWorkflow: null
  }

  componentDidMount() {
    // Tell Streamlit we're ready
    Streamlit.setFrameHeight(this.props.height)
  }

  onWorkflowChange = (nodes: Node[], edges: Edge[]) => {
    // Send data back to Streamlit
    Streamlit.setComponentValue({
      nodes,
      edges,
      timestamp: Date.now()
    })
  }

  render() {
    const { agents, workflows } = this.props

    return (
      <div style={{ height: this.props.height }}>
        <ReactFlow
          nodes={this.state.nodes}
          edges={this.state.edges}
          onNodesChange={this.onWorkflowChange}
        >
          {/* Workflow builder UI */}
        </ReactFlow>
      </div>
    )
  }
}

export default withStreamlitConnection(StreamlitWorkflowBuilder)
```

### 4. Build Configuration

```json
// package.json
{
  "name": "workflow-builder",
  "scripts": {
    "start": "vite --port 3001 --host",
    "build": "vite build",
    "serve": "vite preview"
  }
}
```

```javascript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'build',
    assetsDir: '.'
  },
  server: {
    port: 3001,
    cors: true
  }
})
```

### 5. Integration in Streamlit

```python
# complete_integration.py modification
from workflow_builder_component import workflow_builder

def render_langgraph_studio():
    st.markdown("### 🔬 LangGraph Workflow Builder")

    # Get current agents
    agents = list(st.session_state.system.agents.keys())

    # Load existing workflows
    workflows = load_workflows_from_langgraph()

    # React component embedded
    workflow_result = workflow_builder(
        agents=agents,
        workflows=workflows,
        height=600,
        key="workflow_builder_main"
    )

    # Handle result from React
    if workflow_result:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.json(workflow_result)

        with col2:
            if st.button("🚀 Execute Workflow", type="primary"):
                execute_workflow_with_langgraph(workflow_result)
```

## FastAPI Sidecar for WebSocket

```python
# api_server.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)

            # Send agent updates
            agent_status = get_agent_status()
            await manager.broadcast({
                "type": "agent_update",
                "data": agent_status
            })
    except:
        manager.active_connections.remove(websocket)

@app.get("/api/agents")
async def get_agents():
    """Get agent list from SharedStateManager"""
    from shared_state import SharedStateManager
    state_manager = SharedStateManager()
    return state_manager.get_all_agents()

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str):
    """Execute workflow via LangGraph"""
    from langgraph_executor import execute
    result = await execute(workflow_id)

    # Broadcast execution status
    await manager.broadcast({
        "type": "execution_started",
        "workflow_id": workflow_id
    })

    return result
```

## Streamlit-AgGrid per Dashboard

```python
# Enhanced agent dashboard
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def render_agent_control_center():
    st.markdown("## 🎮 Agent Control Center")

    # Get agent data
    df = pd.DataFrame([
        {
            "agent": agent_id,
            "status": agent.status,
            "cpu": agent.cpu_usage,
            "memory": agent.memory_usage,
            "tasks": agent.task_count
        }
        for agent_id, agent in st.session_state.system.agents.items()
    ])

    # Configure grid
    gb = GridOptionsBuilder.from_dataframe(df)

    # Status column with custom renderer
    status_renderer = JsCode("""
        function(params) {
            const status = params.value;
            const color = status === 'online' ? 'green' :
                         status === 'busy' ? 'orange' : 'red';
            return `<span style="color: ${color}">⬤ ${status}</span>`;
        }
    """)

    gb.configure_column("status", cellRenderer=status_renderer)

    # CPU/Memory with progress bars
    progress_renderer = JsCode("""
        function(params) {
            const value = params.value;
            return `
                <div style="width: 100%; background: #f0f0f0; border-radius: 3px;">
                    <div style="width: ${value}%; background: #4CAF50;
                         height: 20px; border-radius: 3px; text-align: center;">
                        ${value}%
                    </div>
                </div>
            `;
        }
    """)

    gb.configure_column("cpu", cellRenderer=progress_renderer)
    gb.configure_column("memory", cellRenderer=progress_renderer)

    # Show grid with real-time updates
    grid_response = AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode='STREAMING',
        height=400,
        allow_unsafe_jscode=True,
        key='agent_grid'
    )

    # Auto-refresh
    if st.checkbox("Auto-refresh (5s)", value=True):
        st.experimental_rerun()
```

## Streamlit-Elements per UI Moderna

```python
from streamlit_elements import elements, mui, html

def render_modern_dashboard():
    with elements("dashboard"):

        # Material-UI layout
        with mui.Box(sx={"flexGrow": 1}):
            with mui.Grid(container=True, spacing=2):

                # Agent cards
                for agent in agents:
                    with mui.Grid(item=True, xs=12, sm=6, md=4):
                        with mui.Card():
                            with mui.CardContent():
                                mui.Typography(agent.name, variant="h6")

                                # Status chip
                                mui.Chip(
                                    label=agent.status,
                                    color="success" if agent.status == "online" else "error",
                                    size="small"
                                )

                                # Metrics
                                with mui.Box(sx={"mt": 2}):
                                    mui.LinearProgress(
                                        variant="determinate",
                                        value=agent.cpu_usage
                                    )
                                    mui.Typography(f"CPU: {agent.cpu_usage}%", variant="body2")

                            with mui.CardActions():
                                mui.Button("View", size="small")
                                mui.Button("Logs", size="small")
```

## Scripts di Build e Deploy

```bash
#!/bin/bash
# build.sh

echo "Building React components..."

# Build workflow builder
cd interfaces/web/components/workflow-builder/frontend
npm install
npm run build

# Copy to Streamlit
cd ..
mkdir -p build
cp -r frontend/build/* build/

echo "Starting services..."

# Start FastAPI
cd ../../
uvicorn api_server:app --reload --port 8001 &

# Start Streamlit
streamlit run complete_integration.py --server.port 8501

echo "System ready!"
echo "Streamlit: http://localhost:8501"
echo "API: http://localhost:8001/docs"
```

## Testing Integration

```python
# test_integration.py
import pytest
from streamlit.testing.v1 import AppTest

def test_workflow_builder_loads():
    """Test that workflow builder component loads"""
    at = AppTest.from_file("complete_integration.py")
    at.run()

    # Navigate to LangGraph tab
    at.tabs[2].click()

    # Check component exists
    assert "workflow_builder" in at.get_components()

def test_agent_grid_updates():
    """Test AgGrid real-time updates"""
    at = AppTest.from_file("complete_integration.py")
    at.run()

    # Check grid has data
    grid = at.get("agent_grid")
    assert len(grid.data) == 7  # 7 agents
```

Questa è l'implementazione PRATICA e REALISTICA per integrare React in Streamlit senza dover riscrivere tutto.