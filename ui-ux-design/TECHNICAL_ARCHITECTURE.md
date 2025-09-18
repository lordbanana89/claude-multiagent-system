# 🏗️ TECHNICAL ARCHITECTURE DOCUMENT

## System Architecture Overview

```mermaid
C4Context
    title System Context Diagram - Claude Multi-Agent System UI

    Person(user, "User", "System operator")
    System(webui, "Web UI", "Hybrid Streamlit-React interface")
    System_Ext(claude, "Claude Agents", "7 specialized AI agents")
    System_Ext(langgraph, "LangGraph", "Workflow engine")
    SystemDb(postgres, "PostgreSQL", "Workflow storage")
    SystemDb(redis, "Redis", "Cache & state")

    Rel(user, webui, "Uses", "HTTPS")
    Rel(webui, claude, "Controls", "tmux/subprocess")
    Rel(webui, langgraph, "Executes", "Python API")
    Rel(webui, postgres, "Stores", "SQLAlchemy")
    Rel(webui, redis, "Caches", "Redis protocol")
```

## Container Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        ST[Streamlit App<br/>Port 8501]
        RC[React Components<br/>Embedded]
        WB[Workflow Builder<br/>ReactFlow]
        DB[Dashboard<br/>AgGrid]
    end

    subgraph "API Layer"
        FA[FastAPI Server<br/>Port 8001]
        WS[WebSocket Server]
        REST[REST Endpoints]
    end

    subgraph "Business Logic"
        SM[SharedStateManager]
        LG[LangGraph Engine]
        TM[TMUXClient]
        DQ[Dramatiq Queue]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Workflows)]
        RD[(Redis<br/>Cache)]
        FS[(File System<br/>Instructions)]
    end

    subgraph "External Systems"
        CA[Claude Agents<br/>tmux sessions]
        LS[LangSmith<br/>Monitoring]
    end

    ST --> RC
    RC --> WB
    RC --> DB
    ST --> FA
    FA --> WS
    FA --> REST
    REST --> SM
    WS --> SM
    SM --> LG
    SM --> TM
    LG --> DQ
    TM --> CA
    SM --> RD
    LG --> PG
    SM --> FS
    LG --> LS
```

## Component Architecture

```mermaid
classDiagram
    class StreamlitApp {
        +render_main_interface()
        +render_sidebar()
        +session_state: Dict
    }

    class ReactComponent {
        <<interface>>
        +props: Dict
        +state: Dict
        +render()
        +componentDidMount()
    }

    class WorkflowBuilder {
        +nodes: List~Node~
        +edges: List~Edge~
        +onDrop()
        +onConnect()
        +save()
        +load()
    }

    class AgentDashboard {
        +agents: List~Agent~
        +metrics: Dict
        +updateStatus()
        +showLogs()
    }

    class FastAPIServer {
        +app: FastAPI
        +websocket_manager: ConnectionManager
        +get_agents()
        +execute_workflow()
        +stream_updates()
    }

    class SharedStateManager {
        +agents: Dict
        +tasks: Queue
        +register_agent()
        +update_state()
        +get_state()
        +subscribe()
    }

    class LangGraphEngine {
        +graph: StateGraph
        +execute()
        +compile()
        +checkpoint()
    }

    class TMUXClient {
        +sessions: Dict
        +send_command()
        +capture_output()
        +create_session()
    }

    StreamlitApp --> ReactComponent
    ReactComponent <|-- WorkflowBuilder
    ReactComponent <|-- AgentDashboard
    StreamlitApp --> FastAPIServer
    FastAPIServer --> SharedStateManager
    SharedStateManager --> LangGraphEngine
    SharedStateManager --> TMUXClient
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant S as Streamlit
    participant R as React Component
    participant F as FastAPI
    participant W as WebSocket
    participant SM as StateManager
    participant L as LangGraph
    participant A as Agents

    U->>S: Open Dashboard
    S->>R: Load Components
    R->>F: GET /api/agents
    F->>SM: get_agents()
    SM-->>F: agents_data
    F-->>R: JSON response
    R-->>U: Display UI

    U->>R: Create Workflow
    R->>R: Drag & Drop nodes
    U->>R: Execute
    R->>F: POST /api/workflow/execute
    F->>L: execute(workflow)
    L->>A: Run tasks
    A-->>L: Results
    L->>W: Broadcast updates
    W-->>R: Real-time status
    R-->>U: Show progress
```

## Deployment Architecture

```mermaid
graph TD
    subgraph "Development"
        D1[Local Streamlit<br/>localhost:8501]
        D2[Local FastAPI<br/>localhost:8001]
        D3[Local React<br/>localhost:3001]
        D4[Docker Compose]
    end

    subgraph "Staging"
        S1[Streamlit Container]
        S2[FastAPI Container]
        S3[Nginx Reverse Proxy]
        S4[PostgreSQL Container]
        S5[Redis Container]
    end

    subgraph "Production"
        subgraph "Kubernetes Cluster"
            P1[Streamlit Pods<br/>Replicas: 2]
            P2[FastAPI Pods<br/>Replicas: 3]
            P3[Ingress Controller]
        end
        P4[(CloudSQL<br/>PostgreSQL)]
        P5[(Memorystore<br/>Redis)]
        P6[Cloud CDN]
    end

    D4 --> S1
    S3 --> P3
    P3 --> P1
    P3 --> P2
    P1 --> P4
    P2 --> P5
    P6 --> P3
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Network Security"
            NS1[HTTPS/TLS 1.3]
            NS2[CORS Policy]
            NS3[Rate Limiting]
        end

        subgraph "Application Security"
            AS1[JWT Authentication]
            AS2[RBAC Authorization]
            AS3[Input Validation]
            AS4[XSS Protection]
        end

        subgraph "Data Security"
            DS1[Encryption at Rest]
            DS2[Encryption in Transit]
            DS3[Secrets Management]
        end

        subgraph "Infrastructure Security"
            IS1[Network Isolation]
            IS2[Container Security]
            IS3[SIEM Monitoring]
        end
    end

    NS1 --> AS1
    AS1 --> AS2
    AS2 --> DS1
    DS3 --> IS1
```

## API Specification

```yaml
openapi: 3.0.0
info:
  title: Claude Multi-Agent System API
  version: 1.0.0

paths:
  /api/agents:
    get:
      summary: Get all agents
      responses:
        200:
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Agent'

  /api/workflows:
    post:
      summary: Create workflow
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Workflow'

  /api/workflows/{id}/execute:
    post:
      summary: Execute workflow
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string

  /ws/updates:
    get:
      summary: WebSocket connection for real-time updates

components:
  schemas:
    Agent:
      type: object
      properties:
        id: string
        name: string
        status: string
        cpu: number
        memory: number

    Workflow:
      type: object
      properties:
        nodes: array
        edges: array
        metadata: object
```

## Database Schema

```mermaid
erDiagram
    WORKFLOWS ||--o{ WORKFLOW_NODES : contains
    WORKFLOWS ||--o{ WORKFLOW_EDGES : contains
    WORKFLOW_NODES ||--o{ NODE_CONFIGS : has
    WORKFLOWS ||--o{ EXECUTIONS : has
    EXECUTIONS ||--o{ EXECUTION_LOGS : generates
    AGENTS ||--o{ AGENT_TASKS : performs
    AGENTS ||--o{ AGENT_METRICS : tracks

    WORKFLOWS {
        uuid id PK
        string name
        json metadata
        timestamp created_at
        timestamp updated_at
        string created_by
    }

    WORKFLOW_NODES {
        uuid id PK
        uuid workflow_id FK
        string node_type
        json position
        json data
    }

    WORKFLOW_EDGES {
        uuid id PK
        uuid workflow_id FK
        uuid source_node_id FK
        uuid target_node_id FK
        json conditions
    }

    EXECUTIONS {
        uuid id PK
        uuid workflow_id FK
        string status
        timestamp started_at
        timestamp completed_at
        json result
    }

    AGENTS {
        string id PK
        string name
        string type
        string status
        json capabilities
        timestamp last_activity
    }
```

## Performance Architecture

```mermaid
graph LR
    subgraph "Optimization Strategies"
        subgraph "Frontend"
            F1[Code Splitting]
            F2[Lazy Loading]
            F3[Virtual DOM]
            F4[Memoization]
        end

        subgraph "Backend"
            B1[Connection Pooling]
            B2[Query Optimization]
            B3[Caching Strategy]
            B4[Async Operations]
        end

        subgraph "Infrastructure"
            I1[CDN]
            I2[Load Balancing]
            I3[Auto-scaling]
            I4[Edge Caching]
        end
    end
```

## Technology Stack

```mermaid
mindmap
  root((Tech Stack))
    Frontend
      Streamlit 1.28+
      React 18.2
      TypeScript 5.0
      ReactFlow 11
      AgGrid
      Material-UI
      Vite
    Backend
      Python 3.11+
      FastAPI 0.104
      SQLAlchemy 2.0
      Dramatiq
      LangGraph
      WebSockets
    Data
      PostgreSQL 15
      Redis 7
      JSON Storage
    Infrastructure
      Docker
      Kubernetes
      Nginx
      GitHub Actions
    Monitoring
      Prometheus
      Grafana
      Sentry
      DataDog
```

## Network Topology

```mermaid
graph TB
    subgraph "Client Layer"
        C1[Browser]
        C2[Mobile App]
    end

    subgraph "Edge Layer"
        E1[CloudFlare CDN]
        E2[WAF]
    end

    subgraph "Application Layer"
        A1[Load Balancer]
        A2[Streamlit Instances]
        A3[FastAPI Instances]
    end

    subgraph "Service Layer"
        S1[WebSocket Server]
        S2[Task Queue]
        S3[Cache Layer]
    end

    subgraph "Data Layer"
        D1[(Primary DB)]
        D2[(Read Replica)]
        D3[(Redis Cluster)]
    end

    C1 --> E1
    C2 --> E1
    E1 --> E2
    E2 --> A1
    A1 --> A2
    A1 --> A3
    A2 --> S1
    A3 --> S2
    S2 --> S3
    S3 --> D3
    A3 --> D1
    A2 --> D2
```

## Error Handling Strategy

```mermaid
stateDiagram-v2
    [*] --> Normal
    Normal --> Error: Exception
    Error --> Logging: Capture
    Logging --> Analysis: Process
    Analysis --> Recovery: Automatic
    Analysis --> Alert: Manual
    Recovery --> Normal: Success
    Recovery --> Fallback: Failure
    Alert --> Investigation: Human
    Investigation --> Fix: Resolution
    Fix --> Normal: Deployed
    Fallback --> Degraded: Temporary
    Degraded --> Normal: Restored
```

## Monitoring & Observability

```yaml
monitoring:
  metrics:
    application:
      - request_rate
      - response_time
      - error_rate
      - active_users

    infrastructure:
      - cpu_usage
      - memory_usage
      - disk_io
      - network_traffic

    business:
      - workflows_created
      - tasks_completed
      - agent_efficiency
      - user_satisfaction

  logging:
    levels:
      - ERROR: Sentry
      - WARNING: Application logs
      - INFO: Structured logs
      - DEBUG: Development only

  tracing:
    - Request flow
    - Database queries
    - External API calls
    - WebSocket messages

  alerting:
    channels:
      - email
      - slack
      - pagerduty

    rules:
      - error_rate > 1%
      - response_time > 2s
      - cpu_usage > 80%
      - memory_usage > 90%
```

## Scaling Strategy

```mermaid
graph TD
    subgraph "Horizontal Scaling"
        H1[Auto-scaling Groups]
        H2[Container Orchestration]
        H3[Database Sharding]
        H4[Cache Distribution]
    end

    subgraph "Vertical Scaling"
        V1[Resource Optimization]
        V2[Query Tuning]
        V3[Code Optimization]
    end

    subgraph "Metrics"
        M1[Response Time]
        M2[Throughput]
        M3[Resource Usage]
    end

    M1 --> H1
    M2 --> H2
    M3 --> V1
```

---

**Document Version**: 1.0
**Last Updated**: January 2024
**Status**: APPROVED
**Next Review**: Q2 2024
