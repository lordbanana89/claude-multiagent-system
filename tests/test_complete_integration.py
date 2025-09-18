#!/usr/bin/env python3
"""
Test Complete Integration - Web Interface + LangChain + Claude Code
Verifica che tutto il sistema integrato funzioni correttamente
"""

import sys
import time
import subprocess

# Add current directory to path
sys.path.append('.')

try:
    from claude_orchestrator import ClaudeNativeOrchestrator
    from langchain_claude_final import MultiAgentCoordinator
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    INTEGRATION_AVAILABLE = False

def test_web_interface():
    """Test if web interface is accessible"""
    try:
        import requests
        response = requests.get("http://localhost:8503", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_claude_sessions():
    """Test Claude Code sessions"""
    tmux_bin = "/opt/homebrew/bin/tmux"
    claude_sessions = [
        "claude-backend-api",
        "claude-frontend-ui",
        "claude-database"
    ]

    active_sessions = 0
    for session in claude_sessions:
        try:
            subprocess.run([
                tmux_bin, "has-session", "-t", session
            ], check=True, capture_output=True)
            active_sessions += 1
        except subprocess.CalledProcessError:
            pass

    return active_sessions, len(claude_sessions)

def test_langchain_coordination():
    """Test LangChain coordination system"""
    if not INTEGRATION_AVAILABLE:
        return False, "Integration not available"

    try:
        coordinator = MultiAgentCoordinator()

        # Simple test project
        test_project = "Create a simple user authentication API"

        result = coordinator.coordinate_project(test_project)

        return result.get("success", False), result
    except Exception as e:
        return False, str(e)

def main():
    """Run complete integration test"""

    print("🧪 COMPLETE SYSTEM INTEGRATION TEST")
    print("=" * 50)

    # Test 1: Web Interface
    print("🌐 Testing Web Interface...")
    web_status = test_web_interface()
    if web_status:
        print("✅ Web Interface: Running on http://localhost:8503")
    else:
        print("❌ Web Interface: Not accessible")

    # Test 2: Claude Code Sessions
    print("\n🤖 Testing Claude Code Sessions...")
    active_sessions, total_sessions = test_claude_sessions()
    print(f"📊 Claude Sessions: {active_sessions}/{total_sessions} active")
    if active_sessions >= 3:
        print("✅ Claude Code Sessions: Sufficient for testing")
    else:
        print("⚠️ Claude Code Sessions: Limited availability")

    # Test 3: LangChain Coordination
    print("\n🧠 Testing LangChain Multi-Agent Coordination...")
    if INTEGRATION_AVAILABLE:
        coord_success, coord_result = test_langchain_coordination()
        if coord_success:
            print("✅ LangChain Coordination: Working")
            print(f"📊 Coordination Result: {coord_result.get('agents_involved', 0)} agents involved")
            print(f"⚡ Execution Time: {coord_result.get('total_execution_time', 0):.2f}s")
        else:
            print(f"❌ LangChain Coordination: Failed - {coord_result}")
    else:
        print("⚠️ LangChain Coordination: Not available due to import issues")

    # Integration Assessment
    print("\n📊 INTEGRATION ASSESSMENT")
    print("=" * 30)

    components_working = 0
    total_components = 3

    if web_status:
        components_working += 1
        print("✅ Web Interface: Functional")
    else:
        print("❌ Web Interface: Issues")

    if active_sessions >= 3:
        components_working += 1
        print("✅ Claude Code Integration: Functional")
    else:
        print("❌ Claude Code Integration: Limited")

    if INTEGRATION_AVAILABLE and coord_success:
        components_working += 1
        print("✅ Multi-Agent Coordination: Functional")
    else:
        print("❌ Multi-Agent Coordination: Issues")

    # Final Assessment
    print(f"\n🎯 SYSTEM STATUS: {components_working}/{total_components} components working")

    if components_working == total_components:
        print("🎉 SUCCESS: Complete integration working perfectly!")
        print("🚀 System ready for production use")
        print("\n📋 How to use:")
        print("1. 🌐 Web Interface: http://localhost:8503")
        print("2. 🧠 Multi-Agent Coordination: Use 'Intelligent Coordination' tab")
        print("3. 🤖 Direct Control: Use 'Live Agent Terminals' tab")
        print("4. 📊 Monitoring: Use 'System Dashboard' tab")
    elif components_working >= 2:
        print("⚠️ PARTIAL SUCCESS: Most components working")
        print("🔧 System usable with some limitations")
    else:
        print("❌ ISSUES: Major integration problems")
        print("🔍 Check component status and fix issues")

    print(f"\n💡 Next steps:")
    if not web_status:
        print("- Start web interface: python3 -m streamlit run web_interface_complete.py --server.port=8503")
    if active_sessions < 3:
        print("- Create Claude sessions: ./fix_claude_sessions.sh")
    if not INTEGRATION_AVAILABLE:
        print("- Check import paths and dependencies")

if __name__ == "__main__":
    main()