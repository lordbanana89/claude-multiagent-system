"""
Overmind Client - Python interface for Overmind process management
Provides programmatic control over Overmind-managed processes
"""

import subprocess
import re
import os
import time
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import PROJECT_ROOT, DEBUG

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


class OvermindClient:
    """Client for Overmind process management"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize Overmind client

        Args:
            project_root: Project root directory (defaults to config.PROJECT_ROOT)
        """
        self.project_root = project_root or PROJECT_ROOT
        self.overmind_socket = os.getenv("OVERMIND_SOCKET", "/tmp/overmind-claude-multiagent")

    @staticmethod
    def is_installed() -> bool:
        """Check if Overmind is installed"""
        result = subprocess.run(
            ["which", "overmind"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0

    @staticmethod
    def get_version() -> Optional[str]:
        """Get Overmind version"""
        try:
            result = subprocess.run(
                ["overmind", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse "Overmind version X.Y.Z"
                match = re.search(r"Overmind version ([\d.]+)", result.stdout)
                if match:
                    return match.group(1)
            return None
        except Exception as e:
            logger.error(f"Error getting Overmind version: {e}")
            return None

    def start(self, procfile: str = "Procfile",
             detached: bool = True,
             formation: Optional[Dict[str, int]] = None,
             port: Optional[int] = None) -> bool:
        """
        Start Overmind with specified Procfile

        Args:
            procfile: Path to Procfile (relative to project_root)
            detached: Run in background (daemon mode)
            formation: Process formation (e.g., {"web": 2, "worker": 3})
            port: Base port for process allocation

        Returns:
            True if started successfully
        """
        cmd = ["overmind", "start"]

        # Procfile selection
        if procfile != "Procfile":
            cmd.extend(["-f", procfile])

        # Daemon mode
        if not detached:
            cmd.append("--no-daemon")

        # Formation (process scaling)
        if formation:
            formation_str = ",".join([f"{k}={v}" for k, v in formation.items()])
            cmd.extend(["-m", formation_str])

        # Port configuration
        if port:
            cmd.extend(["-p", str(port)])

        logger.info(f"Starting Overmind: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("Overmind started successfully")
                return True
            else:
                logger.error(f"Failed to start Overmind: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout starting Overmind")
            return False
        except Exception as e:
            logger.error(f"Error starting Overmind: {e}")
            return False

    def stop(self) -> bool:
        """Stop all Overmind processes gracefully"""
        try:
            result = subprocess.run(
                ["overmind", "quit"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error stopping Overmind: {e}")
            return False

    def kill(self) -> bool:
        """Kill all Overmind processes forcefully"""
        try:
            result = subprocess.run(
                ["overmind", "kill"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error killing Overmind: {e}")
            return False

    def get_processes(self) -> Dict[str, Dict[str, any]]:
        """
        Get all Overmind-managed processes with detailed status

        Returns:
            Dictionary mapping process names to their status info
        """
        try:
            result = subprocess.run(
                ["overmind", "ps"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            processes = {}
            if result.returncode == 0:
                # Parse output format:
                # supervisor: running (pid 12345)
                # backend: stopped (exit 1)
                for line in result.stdout.splitlines():
                    # More comprehensive regex for different statuses
                    match = re.match(
                        r"(\w+):\s+(\w+)(?:\s+\((?:pid\s+)?(\d+)?\))?(?:\s+\(exit\s+(\d+)\))?",
                        line
                    )
                    if match:
                        name = match.group(1)
                        status = match.group(2)
                        pid = match.group(3)
                        exit_code = match.group(4)

                        processes[name] = {
                            "status": status,
                            "pid": int(pid) if pid else None,
                            "exit_code": int(exit_code) if exit_code else None
                        }

            return processes

        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            return {}

    def restart_process(self, name: str) -> bool:
        """
        Restart specific process

        Args:
            name: Process name from Procfile

        Returns:
            True if restarted successfully
        """
        try:
            logger.info(f"Restarting process: {name}")
            result = subprocess.run(
                ["overmind", "restart", name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"Process {name} restarted successfully")
                return True
            else:
                logger.error(f"Failed to restart {name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error restarting process {name}: {e}")
            return False

    def stop_process(self, name: str) -> bool:
        """
        Stop specific process

        Args:
            name: Process name from Procfile

        Returns:
            True if stopped successfully
        """
        try:
            logger.info(f"Stopping process: {name}")
            result = subprocess.run(
                ["overmind", "stop", name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error stopping process {name}: {e}")
            return False

    def start_process(self, name: str) -> bool:
        """
        Start specific stopped process

        Args:
            name: Process name from Procfile

        Returns:
            True if started successfully
        """
        try:
            logger.info(f"Starting process: {name}")
            result = subprocess.run(
                ["overmind", "start", name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error starting process {name}: {e}")
            return False

    def connect_to_process(self, name: str):
        """
        Connect to process terminal (interactive - opens tmux pane)

        Args:
            name: Process name from Procfile

        Note: This is an interactive command that attaches to tmux
        """
        try:
            logger.info(f"Connecting to process: {name}")
            subprocess.run(
                ["overmind", "connect", name],
                cwd=self.project_root
            )
        except KeyboardInterrupt:
            logger.info(f"Disconnected from {name}")
        except Exception as e:
            logger.error(f"Error connecting to process {name}: {e}")

    def echo_environment(self) -> Dict[str, str]:
        """
        Get environment variables available to processes

        Returns:
            Dictionary of environment variables
        """
        try:
            result = subprocess.run(
                ["overmind", "echo"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            env_vars = {}
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value

            return env_vars

        except Exception as e:
            logger.error(f"Error getting environment: {e}")
            return {}

    def is_running(self) -> bool:
        """Check if Overmind is currently running"""
        processes = self.get_processes()
        return len(processes) > 0

    def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all processes

        Returns:
            Dictionary mapping process names to health status
        """
        processes = self.get_processes()
        health = {}

        for name, info in processes.items():
            health[name] = info["status"] == "running"

        return health

    def wait_for_startup(self, timeout: int = 30,
                        required_processes: Optional[List[str]] = None) -> bool:
        """
        Wait for processes to start up

        Args:
            timeout: Maximum wait time in seconds
            required_processes: List of process names that must be running

        Returns:
            True if all required processes are running
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            processes = self.get_processes()

            if required_processes:
                all_running = all(
                    processes.get(name, {}).get("status") == "running"
                    for name in required_processes
                )
                if all_running:
                    return True
            elif processes:
                # If no specific processes required, just check if any are running
                return True

            time.sleep(1)

        return False


# Convenience functions
def quick_start(dev_mode: bool = False) -> bool:
    """Quick start Overmind with appropriate Procfile"""
    client = OvermindClient()
    procfile = "Procfile.dev" if dev_mode else "Procfile"
    return client.start(procfile=procfile)


def quick_status() -> Dict[str, Dict]:
    """Get quick status of all processes"""
    client = OvermindClient()
    return client.get_processes()


def quick_restart(process_name: str) -> bool:
    """Quick restart a specific process"""
    client = OvermindClient()
    return client.restart_process(process_name)


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Overmind Client CLI")
    parser.add_argument("command", choices=["start", "stop", "status", "restart", "kill"],
                       help="Command to execute")
    parser.add_argument("--process", help="Process name for restart command")
    parser.add_argument("--dev", action="store_true", help="Use development Procfile")

    args = parser.parse_args()

    client = OvermindClient()

    if args.command == "start":
        procfile = "Procfile.dev" if args.dev else "Procfile"
        success = client.start(procfile=procfile)
        print("✅ Started" if success else "❌ Failed to start")

    elif args.command == "stop":
        success = client.stop()
        print("✅ Stopped" if success else "❌ Failed to stop")

    elif args.command == "kill":
        success = client.kill()
        print("✅ Killed" if success else "❌ Failed to kill")

    elif args.command == "status":
        processes = client.get_processes()
        if processes:
            print("📊 Process Status:")
            for name, info in processes.items():
                status_icon = "✅" if info["status"] == "running" else "❌"
                print(f"  {status_icon} {name}: {info['status']}", end="")
                if info.get("pid"):
                    print(f" (pid {info['pid']})", end="")
                print()
        else:
            print("❌ No processes running")

    elif args.command == "restart":
        if args.process:
            success = client.restart_process(args.process)
            print(f"✅ Restarted {args.process}" if success else f"❌ Failed to restart {args.process}")
        else:
            print("❌ Please specify --process name")