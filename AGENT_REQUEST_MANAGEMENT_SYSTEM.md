# 🔐 Agent Request Management System

## 📋 Panoramica

Il **Sistema di Gestione Richieste Agenti** è un componente avanzato del Claude Multi-Agent System che fornisce controllo granulare, tracciamento e autorizzazione di tutte le azioni richieste dagli agenti Claude. Risolve il problema critico della sincronizzazione tra comandi agent e stato sistema, garantendo sicurezza e coordinamento.

---

## 🎯 **A Cosa Serve**

### **Problemi Risolti**

1. **🔒 Controllo Sicurezza**: Previene esecuzione di comandi pericolosi non autorizzati
2. **⚡ Sincronizzazione**: Risolve conflitti timing tra comandi Claude e system commands
3. **📊 Tracciabilità**: Audit trail completo di tutte le azioni degli agenti
4. **🔄 Coordinamento**: Gestisce ordine sequenziale delle richieste evitando interferenze
5. **🎯 Autorizzazione**: Sistema flessibile di approvazione manuale/automatica

### **Benefici Operativi**

- **Sicurezza**: Nessun comando critico eseguito senza approvazione
- **Trasparenza**: Visibilità completa su tutte le richieste agent
- **Efficienza**: Auto-approvazione per comandi sicuri (echo, task-status, etc.)
- **Controllo**: Approvazione manuale per operazioni sensibili
- **Scalabilità**: Sistema estensibile per nuovi tipi di richieste

---

## 🏗️ **Architettura del Sistema**

### **Componenti Principali**

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB INTERFACE                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Request Manager │  │ Pending Queue   │  │ History     │ │
│  │ Tab             │  │ Approval/Reject │  │ Analytics   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              AGENT REQUEST MANAGER                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Request         │  │ Risk Assessment │  │ Approval    │ │
│  │ Creation        │  │ & Auto-Rules    │  │ Engine      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              AGENT REQUEST MONITOR                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Terminal        │  │ Pattern         │  │ Auto        │ │
│  │ Scanning        │  │ Detection       │  │ Execution   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   TMUX AGENTS                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────┐ │
│  │ backend-api │ │ database    │ │ frontend-ui │ │ ...   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 **Struttura File**

### **1. `agent_request_manager.py`** - Core Engine

**Responsabilità**: Gestione centrale di tutte le richieste agenti

**Classi Principali**:
```python
class RequestType(Enum):
    BASH_COMMAND = "bash_command"
    TASK_COMPLETE = "task_complete"
    TASK_PROGRESS = "task_progress"
    TASK_FAIL = "task_fail"
    FILE_ACCESS = "file_access"
    SYSTEM_ACCESS = "system_access"

class RequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    TIMEOUT = "timeout"

class AgentRequest:
    - request_id: str
    - agent_id: str
    - request_type: RequestType
    - command: str
    - risk_level: str (low/medium/high/critical)
    - auto_approve: bool
    - status: RequestStatus
```

**Metodi Chiave**:
- `create_request()`: Crea nuova richiesta con valutazione rischio
- `approve_request()`: Approva richiesta manualmente
- `execute_request()`: Esegue richiesta approvata
- `_assess_risk()`: Valuta livello rischio comando
- `_check_auto_approval()`: Controlla se auto-approvabile

### **2. `agent_request_monitor.py`** - Sistema Monitoraggio

**Responsabilità**: Scansiona terminali tmux per rilevare richieste

**Classe Principale**:
```python
class AgentRequestMonitor:
    - request_manager: AgentRequestManager
    - agent_sessions: Dict[str, str]  # agent_id -> session_id
    - monitoring: bool
```

**Funzionalità**:
- Scansione continua terminali tmux (ogni 5 secondi)
- Pattern matching per rilevare richieste bash
- Rilevamento comandi task (task-complete, task-progress)
- Auto-esecuzione richieste approvate
- Cleanup automatico richieste vecchie

### **3. Web Interface Integration**

**File**: `interfaces/web/complete_integration.py`

**Nuova Tab**: 🔐 Request Manager

**Sezioni**:
- **Control Panel**: Start/stop monitor, creazione richieste manuali, stats
- **Pending Requests**: Coda approvazione con controlli approve/reject
- **Request History**: Storico richieste con analytics
- **Statistics**: Grafici distribuzione status e livelli rischio

---

## 🔧 **Come Funziona**

### **1. Flusso Richiesta Automatica**

```
Agent executes command
        ↓
Monitor detects command in terminal
        ↓
Request created with risk assessment
        ↓
Auto-approval check:
├─ Low risk → Auto-approved & executed
├─ Medium risk → Check patterns → Auto/Manual
└─ High/Critical → Manual approval required
        ↓
If approved → Execute command
If rejected → Log and notify
```

### **2. Flusso Richiesta Manuale**

```
User creates request via Web Interface
        ↓
Request stored in pending queue
        ↓
Manual approval via Web Interface
        ↓
Execution based on request type
        ↓
Result logged and displayed
```

### **3. Sistema Auto-Approvazione**

**Comandi Auto-Approvati** (Rischio Basso):
- `echo` - Output di testo
- `task-status` - Controllo stato task
- `task-help` - Visualizzazione help
- `pwd` - Directory corrente
- `ls` - Lista file (in modalità sicura)
- `task-progress` - Aggiornamenti progresso

**Comandi Approvazione Manuale** (Rischio Medio/Alto):
- `task-complete` - Completamento task
- `git` commands - Operazioni repository
- `npm/pip install` - Installazione pacchetti
- File system operations
- Network operations (`curl`, `wget`)

**Comandi Bloccati** (Rischio Critico):
- `rm -rf` - Cancellazione ricorsiva
- `sudo` - Privilegi elevati
- `chmod 777` - Permessi file pericolosi
- System shutdown/reboot commands

---

## 💾 **Persistenza Dati**

### **File di Storage**

**`agent_requests.json`**: Storage richieste
```json
{
  "requests": {
    "req_1234567890": {
      "request_id": "req_1234567890",
      "agent_id": "backend-api",
      "request_type": "bash_command",
      "command": "task-status",
      "description": "Check current task status",
      "created_at": "2025-09-16T18:00:00.000000",
      "status": "executed",
      "risk_level": "low",
      "auto_approve": true,
      "approved_by": "auto_system",
      "executed_at": "2025-09-16T18:00:00.100000"
    }
  },
  "pending_requests": []
}
```

### **Integrazione SharedState**

Il sistema si integra completamente con il SharedState esistente:
- Lettura stato agenti per validazione richieste
- Aggiornamento task progress via richieste
- Completamento task attraverso sistema approvazione
- Sincronizzazione stato tra componenti

---

## 🚀 **Utilizzo Pratico**

### **Avvio Sistema**

```python
# Via Python
from agent_request_manager import AgentRequestManager
from agent_request_monitor import AgentRequestMonitor

manager = AgentRequestManager()
monitor = AgentRequestMonitor()
monitor.start_monitoring()
```

```bash
# Via CLI
python3 agent_request_monitor.py
```

### **Via Web Interface**

1. **Accedi alla tab "🔐 Request Manager"**
2. **Avvia il monitor**: Click "▶️ Start Monitor"
3. **Monitora richieste pending**: Sezione "⏳ Pending Requests"
4. **Approva/rifiuta**: Bottoni ✅ Approve / ❌ Reject
5. **Visualizza storico**: Sezione "📚 Request History"

### **Creazione Richiesta Manuale**

1. Seleziona Agent
2. Seleziona Type (bash_command, task_complete, etc.)
3. Inserisci Command
4. Click "Create Request"
5. Sistema valuta automaticamente rischio e approval

---

## 📊 **Monitoraggio e Analytics**

### **Metriche Disponibili**

- **Pending Requests**: Numero richieste in attesa
- **Total Requests**: Totale richieste storiche
- **Status Distribution**: Distribuzione approved/rejected/executed
- **Risk Level Distribution**: Distribuzione low/medium/high/critical
- **Auto-Approval Rate**: Percentuale richieste auto-approvate
- **Agent Activity**: Attività per agente

### **Grafici Real-time**

- **Pie Chart**: Distribuzione status richieste
- **Bar Chart**: Distribuzione livelli rischio
- **Timeline**: Attività richieste nel tempo
- **Heatmap**: Attività per agente e tipo richiesta

---

## 🔧 **Configurazione e Personalizzazione**

### **Regole Auto-Approvazione**

Modificare in `AgentRequestManager._setup_default_rules()`:

```python
self.auto_approval_patterns = [
    {
        "type": RequestType.BASH_COMMAND,
        "patterns": ["echo", "task-status", "custom-command"],
        "risk_level": "low"
    }
]
```

### **Valutazione Rischio Custom**

Override `_assess_risk()` method:

```python
def _assess_risk(self, request_type: RequestType, command: str) -> str:
    # Custom risk assessment logic
    if "my-safe-command" in command:
        return "low"
    return "medium"
```

### **Timeout Configurabili**

```python
# Cleanup richieste vecchie
manager.cleanup_old_requests(days=7)

# Timeout richieste pending
manager.timeout_pending_requests(minutes=30)
```

---

## 🛠️ **Estensibilità**

### **Nuovi Tipi di Richiesta**

```python
class RequestType(Enum):
    # Esistenti...
    DATABASE_QUERY = "database_query"
    API_CALL = "api_call"
    FILE_UPLOAD = "file_upload"
```

### **Custom Executors**

```python
def _execute_database_query(self, request: AgentRequest) -> bool:
    # Custom execution logic for database queries
    pass

# Register in _execute_by_type()
```

### **Plugin System**

Il sistema supporta plugin per:
- Custom risk assessors
- Custom approval rules
- Custom execution handlers
- Custom notification systems

---

## 🚨 **Sicurezza**

### **Principi Sicurezza**

1. **Deny by Default**: Tutto bloccato finché non approvato
2. **Least Privilege**: Minimi privilegi necessari
3. **Audit Trail**: Log completo di tutte le azioni
4. **Time-based Expiry**: Richieste scadono automaticamente
5. **Role-based Access**: Diversi livelli di approvazione

### **Best Practices**

- Aggiorna regolarmente le regole di rischio
- Monitora pattern di richieste anomale
- Usa auto-approvazione solo per comandi veramente sicuri
- Implementa notifiche per richieste critiche
- Backup regolare del database richieste

---

## 📈 **Performance**

### **Ottimizzazioni**

- **Background Monitoring**: Scansione asincrona terminali
- **Pattern Caching**: Cache pattern di auto-approvazione
- **Batch Processing**: Elaborazione batch richieste multiple
- **Cleanup Automatico**: Rimozione automatica dati vecchi

### **Scalabilità**

- Supporta centinaia di agenti simultanei
- Database request scalabile (SQLite → PostgreSQL)
- Monitoraggio distribuito per sistemi multi-host
- API RESTful per integrazione esterna

---

## 🔄 **Roadmap Futura**

### **Phase 3 - Advanced Features**

- **Machine Learning**: Risk assessment automatico via ML
- **Workflow Automation**: Catene approvazione automatiche
- **External Integration**: Webhook per sistemi esterni
- **Mobile Interface**: App mobile per approvazioni
- **Voice Control**: Comandi vocali per approvazioni urgenti

### **Phase 4 - Enterprise Features**

- **Multi-tenancy**: Supporto più organizzazioni
- **SSO Integration**: Single Sign-On aziendale
- **Compliance Reporting**: Report conformità automatici
- **Disaster Recovery**: Backup e recovery automatico
- **High Availability**: Sistema ridondante multi-region

---

## ✅ **Conclusioni**

Il **Sistema di Gestione Richieste Agenti** trasforma il Claude Multi-Agent System da prototipo a sistema production-ready, fornendo:

- **Controllo completo** su tutte le azioni degli agenti
- **Sicurezza enterprise-grade** con audit trail completo
- **Automazione intelligente** con approvazione selettiva
- **Scalabilità** per sistemi complessi multi-agente
- **Trasparenza** totale nelle operazioni

Il sistema risolve definitivamente i problemi di sincronizzazione e sicurezza, abilitando deployment sicuro in ambienti production.

---

*📝 Documentazione creata: 2025-09-16*
*🔄 Ultima modifica: 2025-09-16*
*✍️ Autore: Claude AI Assistant*