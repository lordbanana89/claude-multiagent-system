#!/usr/bin/env python3
"""
✅ Complete Task - Completa task corrente
Uso: python3 complete_task.py [messaggio]
"""

import sys
from shared_state.manager import SharedStateManager

def main():
    try:
        print("📋 Controllando task corrente...")

        manager = SharedStateManager()
        current = manager.state.current_task

        if not current:
            print("❌ Nessun task attivo da completare")
            print("💡 Usa 'python3 quick_task.py' per creare un nuovo task")
            sys.exit(1)

        print(f"📋 Task trovato: {current.task_id}")
        print(f"   Descrizione: {current.description}")
        print(f"   Agenti assegnati: {current.assigned_agents}")

        # Messaggio di completamento
        message = sys.argv[1] if len(sys.argv) > 1 else "Completato manualmente"

        # Crea risultati per tutti gli agenti assegnati
        results = {}
        for agent_id in current.assigned_agents:
            results[agent_id] = message

        print(f"✅ Completando task con messaggio: '{message}'")

        # Completa task
        success = manager.complete_task(current.task_id, results)

        if success:
            print(f"🎉 Task {current.task_id} completato con successo!")

            # Mostra stato finale
            final_stats = manager.get_system_stats()
            print(f"📊 Sistema ora: {final_stats['system_status']}")
            print(f"📈 Task completati totali: {final_stats['completed_tasks']}")

        else:
            print("❌ Errore durante il completamento del task")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()