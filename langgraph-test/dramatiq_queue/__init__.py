"""
Dramatiq Emergency Queue System
High-priority task queue replacing tmux architecture
"""

from .core import (
    DramatiqQueueManager,
    QueueTask,
    TaskPriority,
    TaskStatus,
    queue_manager,
    get_queue_manager,
    execute_agent_task,
    execute_urgent_task,
    execute_high_task,
    execute_normal_task,
    execute_low_task
)

from .migration import (
    TmuxMigrationManager,
    migrate_from_tmux,
    get_tmux_sessions,
    emergency_tmux_cleanup
)

__all__ = [
    'DramatiqQueueManager',
    'QueueTask',
    'TaskPriority',
    'TaskStatus',
    'queue_manager',
    'get_queue_manager',
    'execute_agent_task',
    'execute_urgent_task',
    'execute_high_task',
    'execute_normal_task',
    'execute_low_task',
    'TmuxMigrationManager',
    'migrate_from_tmux',
    'get_tmux_sessions',
    'emergency_tmux_cleanup'
]

__version__ = "1.0.0"