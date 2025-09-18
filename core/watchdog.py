#!/usr/bin/env python3
"""
Watchdog - Monitora la salute degli agenti e gestisce timeout
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class AgentWatchdog:
    """Monitora heartbeat degli agenti e gestisce timeout"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.agents = {}  # {agent_id: {'last_heartbeat': timestamp, 'timeout': seconds}}
            self.callbacks = {}  # {agent_id: callback_function}
            self.monitoring = False
            self.monitor_thread = None
            self.heartbeat_interval = 30  # secondi
            self.timeout_threshold = 90  # 3 heartbeat mancati
            self.initialized = True

    def start(self):
        """Avvia monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Watchdog started")

    def stop(self):
        """Ferma monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Watchdog stopped")

    def _monitor_loop(self):
        """Loop di monitoring"""
        while self.monitoring:
            try:
                current_time = datetime.now()
                agents_to_check = list(self.agents.keys())

                for agent in agents_to_check:
                    if agent in self.agents:
                        agent_info = self.agents[agent]
                        last_heartbeat = agent_info.get('last_heartbeat')
                        timeout = agent_info.get('timeout', self.timeout_threshold)

                        if last_heartbeat:
                            elapsed = (current_time - last_heartbeat).total_seconds()

                            if elapsed > timeout:
                                self._handle_timeout(agent, elapsed)

                time.sleep(5)  # Check ogni 5 secondi

            except Exception as e:
                logger.error(f"Watchdog monitor error: {e}")
                time.sleep(5)

    def reset_timeout(self, agent: str):
        """Reset timeout per agente"""
        if agent not in self.agents:
            self.agents[agent] = {}

        self.agents[agent]['last_heartbeat'] = datetime.now()
        logger.debug(f"Watchdog: Reset timeout for {agent}")

    def set_timeout(self, agent: str, timeout_seconds: int):
        """Imposta timeout personalizzato per agente"""
        if agent not in self.agents:
            self.agents[agent] = {}

        self.agents[agent]['timeout'] = timeout_seconds
        logger.info(f"Watchdog: Set timeout for {agent} to {timeout_seconds}s")

    def register_callback(self, agent: str, callback: Callable):
        """Registra callback per timeout"""
        self.callbacks[agent] = callback
        logger.info(f"Watchdog: Registered callback for {agent}")

    def _handle_timeout(self, agent: str, elapsed: float):
        """Gestisci timeout agente"""
        logger.warning(f"Watchdog: Agent {agent} timeout! No heartbeat for {elapsed:.1f}s")

        # Esegui callback se registrata
        if agent in self.callbacks:
            try:
                self.callbacks[agent](agent, elapsed)
            except Exception as e:
                logger.error(f"Watchdog: Callback error for {agent}: {e}")

        # Rimuovi agente dal monitoring
        if agent in self.agents:
            del self.agents[agent]

    def get_status(self) -> Dict:
        """Ottieni stato watchdog"""
        current_time = datetime.now()
        status = {
            'monitoring': self.monitoring,
            'agents': {}
        }

        for agent, info in self.agents.items():
            last_heartbeat = info.get('last_heartbeat')
            if last_heartbeat:
                elapsed = (current_time - last_heartbeat).total_seconds()
                status['agents'][agent] = {
                    'last_heartbeat': last_heartbeat.isoformat(),
                    'elapsed_seconds': elapsed,
                    'healthy': elapsed < info.get('timeout', self.timeout_threshold)
                }

        return status

    def is_agent_healthy(self, agent: str) -> bool:
        """Controlla se agente è healthy"""
        if agent not in self.agents:
            return False

        agent_info = self.agents[agent]
        last_heartbeat = agent_info.get('last_heartbeat')

        if not last_heartbeat:
            return False

        elapsed = (datetime.now() - last_heartbeat).total_seconds()
        return elapsed < agent_info.get('timeout', self.timeout_threshold)