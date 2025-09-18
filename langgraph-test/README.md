# Claude Multi-Agent System

Sistema multi-agente distribuito basato su LangGraph con comunicazione via terminali tmux.

## ⚠️ REGOLA CRITICA OBBLIGATORIA - TMUX DELAY

### 🚨 **ATTENZIONE: QUESTA È UNA REGOLA TASSATIVA**

**TUTTI I COMANDI INVIATI AI TERMINALI DEVONO AVERE UN DELAY OBBLIGATORIO**

Questo è il **BUG PRINCIPALE** che blocca lo sviluppo in molti casi. NON IGNORARE.

### ❌ SBAGLIATO (causa race conditions e comandi non eseguiti):
```python
subprocess.run([
    "tmux", "send-keys", "-t", session_name,
    "echo 'comando'", "Enter"
], check=True)
```

### ✅ CORRETTO (con delay obbligatorio):
```python
# 1. Invia il comando
subprocess.run([
    "tmux", "send-keys", "-t", session_name,
    "echo 'comando'"
], check=True)

# 2. DELAY OBBLIGATORIO (0.1 secondi minimo)
import time
time.sleep(0.1)  # OBBLIGATORIO - NON RIMUOVERE MAI

# 3. Invia Enter
subprocess.run([
    "tmux", "send-keys", "-t", session_name,
    "Enter"
], check=True)
```

### 🔧 PERCHÉ È OBBLIGATORIO:

1. **Race Condition**: Tmux ha bisogno di tempo per processare il comando
2. **Messaggi Persi**: Senza delay i comandi vengono solo "incollati" ma non eseguiti
3. **Bug Sistemico**: Questo problema blocca la comunicazione tra agenti
4. **Comportamento Inconsistente**: I terminali non rispondono correttamente

### 📍 DOVE APPLICARE:

**OGNI SINGOLO COMANDO tmux send-keys nel progetto DEVE usare questo pattern:**

- `messaging/interface.py`
- `messaging/notifications.py`
- `agent_creator.py`
- `supervisor_agent.py`
- `quick_task.py`
- `agent_request_manager.py`
- `demo_test.py`
- `test_task_lifecycle.py`
- **QUALSIASI NUOVO FILE CHE USA tmux send-keys**

## 🎯 Architettura del Sistema

### Componenti Principali:

1. **Shared State Manager** - Gestione stato centralizzato
2. **Agent Creator** - Creazione e configurazione agenti
3. **Enhanced Messaging System** - Sistema messaggi avanzato con notifiche
4. **Terminal Integration** - Interfaccia terminali tmux con DELAY OBBLIGATORIO

### Agenti Disponibili:

- **supervisor** - Coordinamento e supervisione
- **backend-api** - Sviluppo API e servizi backend
- **frontend-ui** - Sviluppo interfacce utente
- **database** - Gestione database e query
- **testing** - Test automatizzati e validazione
- **instagram** - Gestione social media
- **master** - Controllo strategico di alto livello

## 🚀 Quick Start

### 1. Setup Iniziale:
```bash
# Crea agenti base
python3 agent_creator.py

# Avvia sistema messaging
python3 shared_state/manager.py
```

### 2. Invia Task:
```bash
# CORRETTO: con delay integrato
python3 quick_task.py "Implementa API user auth" backend-api
```

### 3. Monitora Agenti:
```bash
# Controlla terminali tmux
tmux list-sessions
tmux attach-session -t claude-backend-api
```

## 📋 Best Practices

### TMUX Commands (OBBLIGATORIO):
```python
# Pattern STANDARD per tutti i comandi tmux:
def send_tmux_command(session_id: str, command: str):
    # Invia comando
    subprocess.run([
        "tmux", "send-keys", "-t", session_id, command
    ], check=True)

    # DELAY OBBLIGATORIO
    import time
    time.sleep(0.1)  # Minimo 0.1s - OBBLIGATORIO

    # Invia Enter
    subprocess.run([
        "tmux", "send-keys", "-t", session_id, "Enter"
    ], check=True)
```

### Message Handling:
```python
# Usa sempre il sistema enhanced messaging
from shared_state.manager import SharedStateManager
manager = SharedStateManager()
manager.send_agent_message(
    sender_id="supervisor",
    recipient_id="backend-api",
    content="Task description",
    priority="HIGH"
)
```

## 🧪 Testing

### Test TMUX Delay:
```bash
# Verifica delay logic
python3 test_delay_fix.py

# Test integrazione
python3 integration_test_delay.py
```

### Test Sistema Completo:
```bash
# Test messaging avanzato
python3 test_enhanced_messaging.py

# Test integrazione completa
python3 test_integrated_notifications.py
```

## 📚 Documentazione

- `TMUX_COMMANDS_GUIDE.md` - Guida completa comandi tmux con delay
- `DEVELOPMENT_GUIDELINES.md` - Linee guida sviluppo
- `CODE_STANDARDS.md` - Standard di codifica
- `PROJECT_STATUS_ANALYSIS.md` - Analisi stato progetto

## ⚠️ TROUBLESHOOTING

### Problema: Comandi non eseguiti nei terminali
**Soluzione**: Verifica che TUTTI i comandi tmux abbiano delay 0.1s

### Problema: Agenti non rispondono ai messaggi
**Soluzione**: Controlla pattern delay in messaging/notifications.py

### Problema: Race conditions nei test
**Soluzione**: Aumenta delay a 0.2s per test intensivi

## 📞 Support

Per problemi con tmux delay o messaging:
1. Verifica pattern delay in tutti i file
2. Esegui test_delay_fix.py per validazione
3. Controlla logs tmux: `tmux capture-pane -p`

---

## 🔥 REMINDER FINALE

**OGNI COMANDO tmux send-keys DEVE AVERE DELAY 0.1s MINIMO**

**QUESTO NON È OPZIONALE - È UNA REGOLA TASSATIVA**

**IGNORARE QUESTA REGOLA CAUSA MALFUNZIONAMENTI SISTEMICI**