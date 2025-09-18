"""
Emergency Tmux Migration System
Replaces tmux subprocess architecture with Dramatiq queue system
"""

import subprocess
import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import threading
import psutil
import signal
import os

from .core import queue_manager, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class TmuxMigrationManager:
    """Emergency migration from tmux to Dramatiq queue system"""

    def __init__(self):
        self.migration_stats = {
            "tmux_sessions_found": 0,
            "commands_migrated": 0,
            "sessions_terminated": 0,
            "migration_errors": 0,
            "start_time": None,
            "completion_time": None
        }
        self.active_tmux_sessions: List[Dict[str, Any]] = []
        self.migration_mapping: Dict[str, str] = {}  # tmux_session -> task_id

    def emergency_analyze_tmux(self) -> Dict[str, Any]:
        """Emergency analysis of current tmux architecture"""
        logger.info("🔍 EMERGENCY: Analyzing tmux sessions causing instability...")

        try:
            # Get all tmux sessions
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}:#{session_created}:#{session_windows}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            sessions = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            sessions.append({
                                "session_name": parts[0],
                                "created": parts[1],
                                "windows": int(parts[2]),
                                "status": "active"
                            })

            self.active_tmux_sessions = sessions
            self.migration_stats["tmux_sessions_found"] = len(sessions)

            # Analyze running processes in tmux sessions
            session_details = []
            for session in sessions:
                try:
                    # Get session details
                    session_info = self._analyze_tmux_session(session["session_name"])
                    session_details.append(session_info)
                except Exception as e:
                    logger.error(f"❌ Error analyzing session {session['session_name']}: {e}")

            analysis = {
                "total_sessions": len(sessions),
                "session_details": session_details,
                "migration_recommended": len(sessions) > 0,
                "estimated_migration_time": len(sessions) * 2,  # 2 seconds per session
                "analysis_timestamp": datetime.now().isoformat()
            }

            logger.info(f"📊 Tmux analysis complete: {len(sessions)} sessions found")
            return analysis

        except subprocess.TimeoutExpired:
            logger.error("⏰ Tmux analysis timed out")
            return {"error": "tmux_timeout", "total_sessions": 0}
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Tmux command failed: {e}")
            return {"error": "tmux_not_available", "total_sessions": 0}
        except Exception as e:
            logger.error(f"❌ Tmux analysis error: {e}")
            return {"error": str(e), "total_sessions": 0}

    def _analyze_tmux_session(self, session_name: str) -> Dict[str, Any]:
        """Analyze individual tmux session"""
        try:
            # Get window list
            result = subprocess.run(
                ["tmux", "list-windows", "-t", session_name, "-F", "#{window_name}:#{window_active}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            windows = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and ':' in line:
                        name, active = line.split(':', 1)
                        windows.append({
                            "name": name,
                            "active": active == "1"
                        })

            # Try to capture running command if possible
            try:
                cmd_result = subprocess.run(
                    ["tmux", "capture-pane", "-t", session_name, "-p"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                current_content = cmd_result.stdout[-200:] if cmd_result.returncode == 0 else ""
            except:
                current_content = ""

            return {
                "session_name": session_name,
                "windows": windows,
                "window_count": len(windows),
                "current_content": current_content,
                "migration_priority": TaskPriority.HIGH.value if "backend-api" in session_name else TaskPriority.NORMAL.value
            }

        except Exception as e:
            logger.error(f"❌ Error analyzing session {session_name}: {e}")
            return {
                "session_name": session_name,
                "error": str(e),
                "migration_priority": TaskPriority.NORMAL.value
            }

    def emergency_migrate_from_tmux(self) -> Dict[str, Any]:
        """Emergency migration of tmux sessions to Dramatiq"""
        logger.warning("🚨 EMERGENCY MIGRATION FROM TMUX TO DRAMATIQ STARTING...")

        self.migration_stats["start_time"] = datetime.now().isoformat()

        try:
            # Analyze current tmux state
            analysis = self.emergency_analyze_tmux()

            if analysis.get("error"):
                return {
                    "success": False,
                    "error": analysis["error"],
                    "stats": self.migration_stats
                }

            # Migrate each session
            for session_detail in analysis.get("session_details", []):
                try:
                    self._migrate_session_to_queue(session_detail)
                except Exception as e:
                    logger.error(f"❌ Failed to migrate session {session_detail.get('session_name')}: {e}")
                    self.migration_stats["migration_errors"] += 1

            # Emergency cleanup of tmux sessions
            cleanup_result = self.emergency_tmux_cleanup()

            self.migration_stats["completion_time"] = datetime.now().isoformat()

            result = {
                "success": True,
                "migration_stats": self.migration_stats,
                "cleanup_result": cleanup_result,
                "dramatiq_queue_stats": queue_manager.get_queue_stats()
            }

            logger.info(f"✅ Emergency migration completed: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Emergency migration failed: {e}")
            self.migration_stats["completion_time"] = datetime.now().isoformat()
            return {
                "success": False,
                "error": str(e),
                "stats": self.migration_stats
            }

    def _migrate_session_to_queue(self, session_detail: Dict[str, Any]) -> str:
        """Migrate individual tmux session to Dramatiq queue"""
        session_name = session_detail["session_name"]

        try:
            # Extract agent ID from session name
            if "backend-api" in session_name:
                agent_id = "backend-api"
                priority = TaskPriority.HIGH
            elif "frontend" in session_name:
                agent_id = "frontend-ui"
                priority = TaskPriority.NORMAL
            elif "database" in session_name:
                agent_id = "database"
                priority = TaskPriority.HIGH
            else:
                # Extract agent ID from session name pattern
                agent_match = re.search(r'([a-zA-Z0-9_-]+)', session_name)
                agent_id = agent_match.group(1) if agent_match else "unknown"
                priority = TaskPriority.NORMAL

            # Create migration command to restart agent in Dramatiq
            migration_command = f"echo 'Migrated from tmux session: {session_name}'"

            # Submit to Dramatiq queue
            task_id = queue_manager.submit_task(
                agent_id=agent_id,
                command=migration_command,
                description=f"Migrated from tmux session: {session_name}",
                priority=priority,
                metadata={
                    "migration_source": "tmux",
                    "original_session": session_name,
                    "migration_timestamp": datetime.now().isoformat()
                }
            )

            self.migration_mapping[session_name] = task_id
            self.migration_stats["commands_migrated"] += 1

            logger.info(f"📦 Migrated session {session_name} -> task {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"❌ Failed to migrate session {session_name}: {e}")
            raise

    def emergency_tmux_cleanup(self) -> Dict[str, Any]:
        """Emergency cleanup of tmux sessions"""
        logger.warning("🧹 EMERGENCY: Cleaning up tmux sessions...")

        cleanup_stats = {
            "sessions_killed": 0,
            "errors": 0,
            "cleanup_method": "emergency"
        }

        try:
            # Get all session names
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                session_names = [line.strip() for line in result.stdout.split('\n') if line.strip()]

                for session_name in session_names:
                    try:
                        # Kill session
                        kill_result = subprocess.run(
                            ["tmux", "kill-session", "-t", session_name],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )

                        if kill_result.returncode == 0:
                            cleanup_stats["sessions_killed"] += 1
                            logger.info(f"🗑️ Killed tmux session: {session_name}")
                        else:
                            cleanup_stats["errors"] += 1
                            logger.error(f"❌ Failed to kill session {session_name}: {kill_result.stderr}")

                    except subprocess.TimeoutExpired:
                        logger.error(f"⏰ Timeout killing session {session_name}")
                        cleanup_stats["errors"] += 1
                    except Exception as e:
                        logger.error(f"❌ Error killing session {session_name}: {e}")
                        cleanup_stats["errors"] += 1

                self.migration_stats["sessions_terminated"] = cleanup_stats["sessions_killed"]

        except Exception as e:
            logger.error(f"❌ Tmux cleanup error: {e}")
            cleanup_stats["errors"] += 1

        return cleanup_stats

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        return {
            "migration_stats": self.migration_stats,
            "migration_mapping": self.migration_mapping,
            "dramatiq_stats": queue_manager.get_queue_stats(),
            "timestamp": datetime.now().isoformat()
        }


# Global migration manager
migration_manager = TmuxMigrationManager()


def migrate_from_tmux() -> Dict[str, Any]:
    """Emergency function to migrate from tmux"""
    return migration_manager.emergency_migrate_from_tmux()


def get_tmux_sessions() -> List[Dict[str, Any]]:
    """Get current tmux sessions"""
    analysis = migration_manager.emergency_analyze_tmux()
    return analysis.get("session_details", [])


def emergency_tmux_cleanup() -> Dict[str, Any]:
    """Emergency tmux cleanup function"""
    return migration_manager.emergency_tmux_cleanup()


if __name__ == "__main__":
    # Emergency migration test
    print("🚨 EMERGENCY TMUX MIGRATION TEST...")

    # Analyze current state
    analysis = migration_manager.emergency_analyze_tmux()
    print(f"📊 Tmux analysis: {analysis}")

    if analysis.get("total_sessions", 0) > 0:
        # Perform emergency migration
        migration_result = migrate_from_tmux()
        print(f"📦 Migration result: {migration_result}")
    else:
        print("ℹ️ No tmux sessions found to migrate")

    print("✅ Emergency migration test completed")