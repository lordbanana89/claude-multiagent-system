# 🧠 SharedState System Documentation

**Sistema di stato condiviso per coordinazione multi-agente avanzata**

---

## 📋 **Panoramica**

Il SharedState System è il cuore del sistema di coordinazione multi-agente che fornisce:

- **Stato centralizzato** per tutti gli agenti
- **Task management completo** con tracking e persistenza
- **Communication layer** strutturata tra agenti
- **Real-time synchronization** con observer pattern
- **Thread-safe operations** per accesso concorrente

---

## 🏗️ **Architettura**

### **Componenti Principali**

```
langgraph-test/shared_state/
├── __init__.py          # Package exports
├── models.py            # Data structures (AgentState, TaskInfo, SharedState)
├── persistence.py       # JSON/SQLite persistence layer
└── manager.py           # SharedStateManager (main controller)
```

### **Data Flow**

```
Web Interface → SharedStateManager → Persistence Layer
      ↕                ↕                    ↕
Agent Terminals ← Observer Pattern → JSON/SQLite Storage
```

---

## 📊 **Data Models**

### **AgentState**
```python
@dataclass
class AgentState:
    agent_id: str                    # Unique identifier
    name: str                        # Human-readable name
    status: AgentStatus              # IDLE/BUSY/WAITING/ERROR/COMPLETED
    current_task: Optional[str]      # Current task ID
    last_activity: datetime          # Last status update
    session_id: str                  # tmux session name
    port: int                        # ttyd port
    capabilities: List[str]          # Agent specializations
    error_message: Optional[str]     # Last error (if any)
```

### **TaskInfo**
```python
@dataclass
class TaskInfo:
    task_id: str                     # Unique task identifier
    description: str                 # Task description
    priority: TaskPriority           # LOW/MEDIUM/HIGH/URGENT
    created_at: datetime            # Creation timestamp
    assigned_agents: List[str]       # List of assigned agent IDs
    status: str                      # pending/in_progress/completed/failed
    progress: float                  # 0.0 to 100.0
    results: Dict[str, Any]         # Task results
    error_message: Optional[str]     # Error details (if failed)
    started_at: Optional[datetime]   # Task start time
    completed_at: Optional[datetime] # Task completion time
```

### **SharedState**
```python
@dataclass
class SharedState:
    # Task Management
    current_task: Optional[TaskInfo]     # Currently executing task
    task_queue: List[TaskInfo]          # Pending tasks (priority-sorted)
    task_history: List[TaskInfo]        # Completed/failed tasks

    # Agent Management
    agents: Dict[str, AgentState]       # All registered agents

    # Communication
    messages: List[InterAgentMessage]   # Inter-agent messages

    # Shared Data
    shared_variables: Dict[str, Any]    # Global shared variables

    # System State
    system_status: str                  # idle/busy/error
    last_updated: datetime             # Last state change
    settings: Dict[str, Any]           # System configuration
```

---

## ⚙️ **SharedStateManager API**

### **Agent Management**
```python
# Register new agent
manager.register_agent(agent_state: AgentState) -> bool

# Update agent status
manager.update_agent_status(agent_id: str, status: AgentStatus) -> bool

# Get agent info
manager.get_agent(agent_id: str) -> Optional[AgentState]
manager.get_all_agents() -> Dict[str, AgentState]
manager.get_available_agents() -> List[AgentState]
```

### **Task Management**
```python
# Create and add task
task = manager.create_task(description: str, priority: TaskPriority)
manager.add_task(task: TaskInfo) -> bool

# Assign task to agents
manager.assign_task(task_id: str, agent_ids: List[str]) -> bool

# Complete task
manager.complete_task(task_id: str, results: Dict = None) -> bool

# Query tasks
manager.get_current_task() -> Optional[TaskInfo]
manager.get_task_queue() -> List[TaskInfo]
manager.get_task_history(limit: int) -> List[TaskInfo]
```

### **Inter-Agent Communication**
```python
# Send message between agents
manager.send_message(from_agent: str, to_agent: str,
                    message: str, data: Dict = None) -> bool

# Get messages for agent
manager.get_messages_for_agent(agent_id: str) -> List[InterAgentMessage]

# Mark message as read
manager.mark_message_read(message_id: str) -> bool
```

### **Shared Variables**
```python
# Set/get shared variables
manager.set_shared_var(key: str, value: Any) -> bool
manager.get_shared_var(key: str, default: Any = None) -> Any
manager.delete_shared_var(key: str) -> bool
```

### **System Monitoring**
```python
# Get system statistics
manager.get_system_stats() -> Dict[str, Any]

# Get complete state snapshot
manager.get_state_snapshot() -> SharedState
```

---

## 🔄 **Observer Pattern**

### **Registrazione Observer**
```python
def my_observer(event_type: str, data: Any):
    print(f"Event: {event_type}, Data: {data}")

manager.register_observer(my_observer)
```

### **Eventi Disponibili**
- `agent_registered` - Nuovo agente registrato
- `agent_status_changed` - Status agente cambiato
- `task_added` - Task aggiunto alla coda
- `task_assigned` - Task assegnato ad agenti
- `task_completed` - Task completato/fallito
- `message_sent` - Messaggio inviato tra agenti
- `shared_var_updated` - Variabile condivisa aggiornata
- `state_saved` - Stato salvato su persistenza

---

## 💾 **Persistence**

### **JSON Persistence (Default)**
```python
# Salvataggio automatico su ogni cambiamento
persistence = JSONPersistence("shared_state.json")

# File structure
{
  "current_task": {...},
  "task_queue": [...],
  "task_history": [...],
  "agents": {...},
  "messages": [...],
  "shared_variables": {...},
  "system_status": "idle",
  "last_updated": "2025-09-16T10:30:00",
  "settings": {...}
}
```

### **SQLite Persistence (Advanced)**
```python
# Per installazioni enterprise con history tracking
persistence = SQLitePersistence("shared_state.db")

# Tables:
# - shared_state (current state)
# - state_history (historical snapshots)
```

---

## 🔐 **Thread Safety**

Il sistema è completamente thread-safe:

```python
import threading

# Tutti i metodi usano RLock interno
manager = SharedStateManager()

def worker_thread():
    manager.update_agent_status("agent1", AgentStatus.BUSY)

# Safe per accesso concorrente
threads = [threading.Thread(target=worker_thread) for _ in range(10)]
for t in threads:
    t.start()
```

---

## 📈 **Integrazione Web Interface**

### **Mission Control**
```python
# Send task to all agents with SharedState tracking
def send_to_all_agents(self, task: str) -> Dict:
    # 1. Create task in SharedState
    task_info = self.state_manager.create_task(task, TaskPriority.MEDIUM)
    self.state_manager.add_task(task_info)

    # 2. Assign to all agents
    agent_ids = list(self.agents.keys())
    self.state_manager.assign_task(task_info.task_id, agent_ids)

    # 3. Send to tmux terminals
    # ...

    return {"task_id": task_info.task_id, "shared_state": stats}
```

### **Analytics Dashboard**
```python
# Real-time metrics from SharedState
def render_analytics():
    stats = system.state_manager.get_system_stats()
    agents_state = system.state_manager.get_all_agents()
    current_task = system.state_manager.get_current_task()

    # Display real-time metrics
    st.metric("Active Agents", stats["active_agents"])
    st.metric("Tasks in Queue", stats["tasks_in_queue"])
    # ...
```

---

## 🧪 **Testing**

### **Basic Usage Test**
```python
# Initialize system
manager = SharedStateManager()

# Register agents
agent1 = AgentState(agent_id="backend", name="Backend Agent",
                   status=AgentStatus.IDLE)
manager.register_agent(agent1)

# Create and assign task
task = manager.create_task("Test task", TaskPriority.HIGH)
manager.add_task(task)
manager.assign_task(task.task_id, ["backend"])

# Verify state
assert manager.get_current_task().task_id == task.task_id
assert manager.get_agent("backend").status == AgentStatus.BUSY
```

### **Observer Test**
```python
events = []

def test_observer(event_type: str, data: Any):
    events.append((event_type, data))

manager.register_observer(test_observer)
manager.update_agent_status("backend", AgentStatus.COMPLETED)

assert len(events) == 1
assert events[0][0] == "agent_status_changed"
```

---

## 🔮 **Future Extensions**

Il SharedState System è progettato per supportare:

### **Phase 2: Task Orchestration**
- Complex task decomposition
- Dependency graphs
- Conditional execution paths
- Resource allocation

### **Phase 3: Advanced Workflows**
- Workflow definition language
- Visual workflow builder
- Parallel execution optimization
- Error recovery strategies

### **Phase 4: Machine Learning**
- Performance prediction
- Intelligent agent selection
- Task priority optimization
- Learning from execution patterns

---

## 🆘 **Troubleshooting**

### **Common Issues**

**1. State not persisting**
```bash
# Check file permissions
ls -la shared_state.json

# Check SharedStateManager initialization
tail -f streamlit.log | grep "SharedStateManager"
```

**2. Observer not firing**
```python
# Verify observer registration
print(len(manager.observers))  # Should be > 0

# Check for exceptions in observer code
def safe_observer(event_type, data):
    try:
        # your code
    except Exception as e:
        print(f"Observer error: {e}")
```

**3. Thread deadlock**
```python
# Use timeout for debugging
with manager.lock:
    # operations
    pass
```

### **Debug Mode**
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check state consistency
snapshot = manager.get_state_snapshot()
print(f"Agents: {len(snapshot.agents)}")
print(f"Tasks in queue: {len(snapshot.task_queue)}")
print(f"System status: {snapshot.system_status}")
```

---

## 📚 **Best Practices**

1. **Always use task IDs** for referencing tasks
2. **Check return values** of manager methods
3. **Handle observer exceptions** gracefully
4. **Use appropriate TaskPriority** levels
5. **Clean up completed tasks** periodically
6. **Monitor system_stats** for performance
7. **Use shared_variables** for global configuration
8. **Implement proper error handling** in agents

---

**🎯 Il SharedState System fornisce una foundation solida e scalabile per coordinazione multi-agente avanzata, pronta per essere estesa con funzionalità di orchestrazione intelligente.**