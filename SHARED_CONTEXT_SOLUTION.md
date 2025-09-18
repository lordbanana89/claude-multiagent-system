# 🧠 Soluzione: Sistema di Contesto Condiviso per Agenti Claude

## 🔴 Il Problema Critico

Ogni agente Claude CLI opera in isolamento totale:
- Non sa cosa stanno facendo gli altri agenti
- Non ha visibilità sulle decisioni già prese
- Non può coordinare il proprio lavoro con gli altri
- Rischia di fare modifiche conflittuali o duplicate

## 💡 Soluzioni Proposte

### Soluzione 1: **Shared Context Terminal** (Raccomandata)
Creare un terminale TMUX condiviso dove tutti i messaggi vengono aggregati.

```bash
#!/bin/bash
# create_shared_context.sh

# Crea sessione condivisa
tmux new-session -d -s claude-shared-context

# Ogni agente scrive qui i suoi progressi
tmux send-keys -t claude-shared-context "=== SHARED CONTEXT TERMINAL ===" Enter
```

**Implementazione:**
```python
# core/shared_context.py
class SharedContextManager:
    def __init__(self):
        self.context_session = "claude-shared-context"
        self.tmux = TMUXClient()

    def broadcast_action(self, agent_name, action):
        """Ogni agente annuncia cosa sta per fare"""
        message = f"[{agent_name}] {action}"
        self.tmux.send_command(self.context_session, message)

        # Invia anche a tutti gli altri agenti
        for other_agent in self.get_all_agents():
            if other_agent != agent_name:
                context_msg = f"📢 CONTEXT: {message}"
                self.tmux.send_command(other_agent, context_msg)

    def get_shared_context(self):
        """Recupera tutto il contesto condiviso"""
        return self.tmux.capture_pane(self.context_session)
```

### Soluzione 2: **Message Broadcasting System**
Ogni agente riceve copia di tutti i messaggi degli altri.

```python
# agents/agent_bridge_enhanced.py
class EnhancedAgentBridge(AgentBridge):
    def execute_task(self, task):
        # Prima di eseguire, recupera contesto
        context = self.get_all_agents_context()

        # Prepara il task con contesto
        enhanced_task = f"""
        📋 TASK: {task}

        📊 CURRENT SYSTEM STATE:
        {context}

        Please proceed knowing what other agents are doing.
        """

        # Invia a Claude con contesto
        self.send_to_claude(enhanced_task)

        # Dopo l'esecuzione, broadcast il risultato
        result = self.get_claude_response()
        self.broadcast_to_all_agents(result)
```

### Soluzione 3: **Shared State File** (Semplice ma Efficace)
Un file markdown che tutti gli agenti leggono/scrivono.

```python
# core/shared_state_manager.py
class SharedStateManager:
    def __init__(self):
        self.state_file = "CURRENT_SYSTEM_STATE.md"

    def update_state(self, agent_name, component, status):
        """Aggiorna lo stato condiviso"""
        with open(self.state_file, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n[{timestamp}] {agent_name}: {component} - {status}")

    def inject_state_to_agent(self, agent_session):
        """Inietta lo stato nel prompt dell'agente"""
        state = open(self.state_file).read()

        context_prompt = f"""
        📊 SYSTEM STATE UPDATE:
        {state}

        Consider this information for your next actions.
        """

        tmux.send_command(agent_session, context_prompt)
```

### Soluzione 4: **Supervisor Pattern con Context Injection**
Il Supervisor mantiene e distribuisce il contesto.

```python
# agents/supervisor_enhanced.py
class EnhancedSupervisor:
    def __init__(self):
        self.global_context = {}
        self.agent_activities = []

    def assign_task(self, agent, task):
        # Prepara contesto completo
        context = self.build_context_for_agent(agent)

        # Inietta contesto nel task
        contextualized_task = f"""
        🎯 TASK ASSIGNMENT

        Your task: {task}

        📊 WHAT OTHER AGENTS ARE DOING:
        {self.format_agent_activities()}

        🗂️ CURRENT PROJECT STATE:
        {self.format_global_context()}

        ⚠️ COORDINATION NOTES:
        - Backend is working on: {self.global_context.get('backend', 'N/A')}
        - Database schema includes: {self.global_context.get('database', 'N/A')}
        - Frontend expects: {self.global_context.get('frontend', 'N/A')}

        Please ensure your work aligns with the above.
        """

        self.send_to_agent(agent, contextualized_task)
```

## 🚀 Implementazione Raccomandata: Hybrid Approach

Combinare le soluzioni per massima efficacia:

```bash
#!/bin/bash
# start_coordinated_system.sh

# 1. Crea shared context terminal
tmux new-session -d -s claude-shared-context

# 2. Avvia tutti gli agenti
agents=("backend-api" "database" "frontend-ui")
for agent in "${agents[@]}"; do
    tmux new-session -d -s "claude-$agent"

    # Avvia Claude con contesto iniziale
    tmux send-keys -t "claude-$agent" "claude" Enter
    sleep 2

    # Inietta awareness del sistema
    tmux send-keys -t "claude-$agent" "
    You are part of a multi-agent system. Other agents include: ${agents[@]}.
    Before making changes, consider what others might be doing.
    Announce your major decisions so others are aware.
    Check the shared context regularly.
    " Enter
done

# 3. Avvia context synchronizer
python3 context_synchronizer.py &

echo "✅ Coordinated system started with shared context!"
```

## 📝 Context Synchronizer Script

```python
#!/usr/bin/env python3
# context_synchronizer.py

import time
import threading
from core.tmux_client import TMUXClient

class ContextSynchronizer:
    def __init__(self):
        self.tmux = TMUXClient()
        self.agents = ["claude-backend-api", "claude-database", "claude-frontend-ui"]
        self.shared_context = "claude-shared-context"
        self.last_activities = {}

    def monitor_agent(self, agent):
        """Monitora un agente e broadcasta le sue attività"""
        while True:
            # Cattura output recente
            output = self.tmux.capture_pane(agent, lines=10)

            # Detecta nuove attività significative
            if self.is_significant_activity(output, agent):
                # Broadcasta agli altri
                self.broadcast_activity(agent, output)

                # Aggiorna contesto condiviso
                self.update_shared_context(agent, output)

            time.sleep(5)

    def broadcast_activity(self, source_agent, activity):
        """Invia attività agli altri agenti"""
        summary = self.summarize_activity(activity)

        for agent in self.agents:
            if agent != source_agent:
                message = f"📢 [{source_agent}] is {summary}"
                self.tmux.send_command(agent, f"# {message}")

    def periodic_context_injection(self):
        """Inietta periodicamente il contesto globale"""
        while True:
            time.sleep(60)  # Ogni minuto

            context = self.tmux.capture_pane(self.shared_context)

            for agent in self.agents:
                self.tmux.send_command(agent, f"""
                # 📊 PERIODIC CONTEXT UPDATE
                # Recent system activities:
                {context[-20:]}  # Ultime 20 righe
                """)

    def run(self):
        """Avvia monitoring threads"""
        threads = []

        # Thread per ogni agente
        for agent in self.agents:
            t = threading.Thread(target=self.monitor_agent, args=(agent,))
            t.start()
            threads.append(t)

        # Thread per context injection
        t = threading.Thread(target=self.periodic_context_injection)
        t.start()
        threads.append(t)

        # Wait
        for t in threads:
            t.join()

if __name__ == "__main__":
    syncer = ContextSynchronizer()
    syncer.run()
```

## ✅ Benefici della Soluzione

1. **Coerenza**: Tutti gli agenti sanno cosa fanno gli altri
2. **Prevenzione Conflitti**: Evita modifiche duplicate o conflittuali
3. **Collaborazione**: Gli agenti possono costruire sul lavoro degli altri
4. **Tracciabilità**: Log completo di tutte le attività
5. **Debugging**: Facile capire cosa è successo e perché

## 🎯 Prossimi Passi

1. **Immediato**: Implementare shared context terminal
2. **Breve termine**: Aggiungere context synchronizer
3. **Medio termine**: Sviluppare protocolli di coordinamento avanzati
4. **Lungo termine**: Machine learning per ottimizzare collaborazione

## 💡 Esempio di Flusso Coordinato

```
[Supervisor] → "Create user authentication system"
    ↓
[Shared Context] → "NEW TASK: User authentication system"
    ↓
[Backend] → "I'll create /api/auth endpoints"
[Shared Context] → "Backend: Creating /api/auth endpoints"
    ↓
[Database] → "I see Backend needs auth. Creating users table with email, password_hash"
[Shared Context] → "Database: Creating users table for auth"
    ↓
[Frontend] → "I see auth API and users table. Creating login form to match"
[Shared Context] → "Frontend: Creating login form for /api/auth"
    ↓
[Testing] → "I see the full auth stack. Writing integration tests"
```

## 🚨 Importante

Senza questo sistema di contesto condiviso, il sistema multi-agente Claude **non può funzionare efficacemente** per progetti complessi. È essenziale implementarlo prima di procedere con task di sviluppo reali.

---

*Documento creato: 18 Settembre 2025*
*Priorità: CRITICA - Implementare prima di qualsiasi altro sviluppo*