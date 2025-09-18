#!/usr/bin/env python3
"""
🎯 Quick Task - Crea task veloce senza complicazioni
Uso: python3 quick_task.py "Descrizione task" [agente]
"""

import sys
import subprocess
from shared_state.manager import SharedStateManager
from shared_state.models import TaskPriority

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python3 quick_task.py 'Descrizione task' [agente]")
        print("📝 Esempio: python3 quick_task.py 'Scrivi hello world' backend-api")
        sys.exit(1)

    task_desc = sys.argv[1]
    agent = sys.argv[2] if len(sys.argv) > 2 else 'backend-api'

    print(f"🎯 Creando task veloce...")
    print(f"   Task: {task_desc}")
    print(f"   Agente: {agent}")

    try:
        # Crea task
        manager = SharedStateManager()
        task = manager.create_task(task_desc, TaskPriority.MEDIUM)
        manager.add_task(task)
        manager.assign_task(task.task_id, [agent])

        print(f"✅ Task creato e assegnato!")
        print(f"📋 Task ID: {task.task_id}")

        # Invia all'agente via tmux
        session_map = {
            'backend-api': 'claude-backend-api',
            'database': 'claude-database',
            'frontend-ui': 'claude-frontend-ui',
            'instagram': 'claude-instagram',
            'testing': 'claude-testing'
        }

        session_name = session_map.get(agent, f'claude-{agent}')

        try:
            subprocess.run([
                "tmux", "send-keys", "-t", session_name,
                f"NUOVO TASK: {task_desc}"
            ], check=True)

            # Wait for command to be processed, then send Enter
            import time
            time.sleep(0.1)  # Short delay to let command be processed
            subprocess.run([
                "tmux", "send-keys", "-t", session_name,
                "Enter"
            ], check=True)
            print(f"📤 Task inviato al terminale {session_name}")
        except:
            print(f"⚠️ Impossibile inviare al terminale {session_name}")
            print(f"   Terminale potrebbe non essere attivo")

        print()
        print("🎯 PROSSIMI PASSI:")
        print(f"1. Vai al terminale {agent} (porta {session_map.get(agent, 'N/A')})")
        print(f"2. L'agente lavorerà sul task")
        print(f"3. Quando finito, usa: python3 complete_task.py")

    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()