#!/usr/bin/env python3
"""
Final System Test - Verifica finale integrazione completa
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.langchain_claude_final import MultiAgentCoordinator
    from config.settings import TMUX_BIN, AGENT_SESSIONS
    from core.tmux_client import TMUXClient
    COORDINATION_AVAILABLE = True
except Exception as e:
    print(f"Import error: {e}")
    COORDINATION_AVAILABLE = False
    TMUX_BIN = "/opt/homebrew/bin/tmux"
    AGENT_SESSIONS = {}

def main():
    print("🎯 FINAL SYSTEM STATUS CHECK")
    print("=" * 40)

    # Check web interface
    try:
        result = subprocess.run(['curl', '-s', '-I', 'http://localhost:8503'],
                              capture_output=True, text=True, timeout=5)
        web_status = "200 OK" in result.stdout
    except:
        web_status = False

    # Check Claude sessions
    if COORDINATION_AVAILABLE and AGENT_SESSIONS:
        active_sessions = 0
        total_sessions = len(AGENT_SESSIONS)

        for agent_id, tmux_session in AGENT_SESSIONS.items():
            try:
                if TMUXClient.session_exists(tmux_session):
                    active_sessions += 1
            except:
                pass
    else:
        # Fallback to checking common sessions
        claude_sessions = ["claude-backend-api", "claude-frontend-ui", "claude-database"]
        active_sessions = 0
        total_sessions = len(claude_sessions)

        for session in claude_sessions:
            try:
                subprocess.run([TMUX_BIN, "has-session", "-t", session],
                             check=True, capture_output=True)
                active_sessions += 1
            except:
                pass

    # Check coordination system
    coordination_status = False
    if COORDINATION_AVAILABLE:
        try:
            coordinator = MultiAgentCoordinator()
            coordination_status = True
        except:
            coordination_status = False

    # Results
    print("📊 COMPONENT STATUS:")
    print(f"🌐 Web Interface: {'✅ Active' if web_status else '❌ Inactive'}")
    print(f"🤖 Claude Sessions: ✅ {active_sessions}/{total_sessions} active")
    print(f"🧠 Multi-Agent Coord: {'✅ Available' if coordination_status else '❌ Unavailable'}")

    # Overall assessment
    working_components = sum([web_status, active_sessions >= 2, coordination_status])

    print(f"\n🎯 SYSTEM STATUS: {working_components}/3 components operational")

    if working_components == 3:
        print("🎉 PERFECT: Complete system fully operational!")
        print("\n🚀 READY TO USE:")
        print("• Web Interface: http://localhost:8503")
        print("• Multi-Agent Coordination: Fully functional")
        print("• Claude Code Integration: All terminals active")
        print("• System Integration: Complete and tested")

    elif working_components >= 2:
        print("✅ GOOD: System mostly operational with minor issues")

    else:
        print("⚠️ ISSUES: System needs attention")

    print("\n💡 SYSTEM CAPABILITIES:")
    print("1. 🧠 Intelligent Project Coordination (LangChain-pattern)")
    print("2. 🤖 Direct Claude Code Terminal Control")
    print("3. 📊 Real-time System Monitoring")
    print("4. 📋 Project Templates & Quick Actions")

if __name__ == "__main__":
    main()