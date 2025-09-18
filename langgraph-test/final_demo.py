#!/usr/bin/env python3
"""
🎯 DEMO FINALE - Prova Definitiva Sistema Completo
"""

import sys
import time
from datetime import datetime

sys.path.append('/Users/erik/Desktop/claude-multiagent-system/langgraph-test')
from shared_state.manager import SharedStateManager
from shared_state.models import TaskPriority

def demo_finale():
    print("🎯 DEMO FINALE - PROVA DEFINITIVA")
    print("=" * 50)

    manager = SharedStateManager(
        persistence_type="json",
        persistence_file="/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_state.json"
    )

    # Stato prima
    print("📊 STATO PRIMA:")
    stats_before = manager.get_system_stats()
    print(f"   Sistema: {stats_before['system_status']}")
    print(f"   Task completati: {stats_before['completed_tasks']}")
    print()

    # Crea nuovo task
    task = manager.create_task(
        description="FINAL TEST - Usa task-complete per completare",
        priority=TaskPriority.HIGH
    )
    manager.add_task(task)
    manager.assign_task(task.task_id, ["backend-api"])

    print(f"✅ NUOVO TASK CREATO:")
    print(f"   ID: {task.task_id}")
    print(f"   Descrizione: {task.description}")
    print()

    # Verifica stato
    manager.state = manager.persistence_manager.load()
    current = manager.state.current_task
    agent = manager.state.agents["backend-api"]

    print(f"📋 STATO SISTEMA DOPO CREAZIONE:")
    print(f"   Sistema status: {manager.state.system_status}")
    print(f"   Current task: {current.task_id if current else None}")
    print(f"   Agente status: {agent.status.value}")
    print(f"   Agente task: {agent.current_task}")
    print()

    print("🎯 TASK PRONTO PER COMPLETAMENTO!")
    print(f"L'agente può ora usare: task-complete 'messaggio'")
    return task.task_id

if __name__ == "__main__":
    task_id = demo_finale()