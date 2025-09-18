#!/usr/bin/env python3
"""
Test Phase 0 Components - Verify all critical fixes are working
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all imports work with new paths"""
    print("Testing imports...")

    try:
        # Test config import
        from config.settings import PROJECT_ROOT, TMUX_BIN, AGENT_SESSIONS
        print("✅ config.settings imported successfully")
        print(f"   PROJECT_ROOT: {PROJECT_ROOT}")
        print(f"   TMUX_BIN: {TMUX_BIN}")
        print(f"   Agents: {list(AGENT_SESSIONS.keys())}")
    except ImportError as e:
        print(f"❌ Failed to import config.settings: {e}")
        return False

    try:
        # Test TMUXClient import
        from core.tmux_client import TMUXClient
        print("✅ core.tmux_client imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import core.tmux_client: {e}")
        return False

    try:
        # Test auth manager import
        from core.auth_manager import AuthManager
        print("✅ core.auth_manager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import core.auth_manager: {e}")
        return False

    try:
        # Test shared state import - add langgraph-test to path first
        sys.path.insert(0, str(Path(__file__).parent.parent / "langgraph-test"))
        from shared_state.manager import SharedStateManager
        print("✅ shared_state.manager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import shared_state: {e}")
        return False

    return True


def test_tmux_delay():
    """Test that TMUX delay is configured"""
    from config.settings import TMUX_COMMAND_DELAY

    print("\nTesting TMUX delay configuration...")
    if TMUX_COMMAND_DELAY >= 0.1:
        print(f"✅ TMUX_COMMAND_DELAY is {TMUX_COMMAND_DELAY}s (>= 0.1s required)")
        return True
    else:
        print(f"❌ TMUX_COMMAND_DELAY is {TMUX_COMMAND_DELAY}s (too low!)")
        return False


def test_project_paths():
    """Test that paths are relative to PROJECT_ROOT"""
    from config.settings import PROJECT_ROOT, STATE_DIR, SHARED_STATE_FILE, AUTH_DB_PATH

    print("\nTesting path configuration...")

    # Check that paths are Path objects and relative to PROJECT_ROOT
    checks = [
        ("STATE_DIR", STATE_DIR, PROJECT_ROOT / "langgraph-test"),
        ("SHARED_STATE_FILE", SHARED_STATE_FILE, STATE_DIR / "shared_state.json"),
        ("AUTH_DB_PATH", AUTH_DB_PATH, PROJECT_ROOT / ".auth" / "auth.db"),
    ]

    all_good = True
    for name, actual, expected in checks:
        if actual == expected:
            print(f"✅ {name}: {actual}")
        else:
            print(f"❌ {name}: {actual} (expected {expected})")
            all_good = False

    # Check that paths use PROJECT_ROOT (they will resolve to absolute paths)
    # This is expected and correct - we use PROJECT_ROOT to build paths
    if STATE_DIR == PROJECT_ROOT / "langgraph-test":
        print("✅ STATE_DIR correctly uses PROJECT_ROOT")
    else:
        print("❌ STATE_DIR not using PROJECT_ROOT correctly")
        all_good = False

    return all_good


def test_tmux_client():
    """Test TMUXClient methods"""
    from core.tmux_client import TMUXClient

    print("\nTesting TMUXClient...")

    # Test that methods exist
    methods = ['send_command', 'send_keys', 'send_command_raw', 'capture_pane',
               'session_exists', 'list_sessions', 'create_session']

    all_good = True
    for method in methods:
        if hasattr(TMUXClient, method):
            print(f"✅ TMUXClient.{method} exists")
        else:
            print(f"❌ TMUXClient.{method} missing")
            all_good = False

    return all_good


def test_package_structure():
    """Test that all packages have __init__.py"""
    print("\nTesting package structure...")

    packages = [
        "core",
        "config",
        "langgraph-test",
        "langgraph-test/shared_state",
        "langgraph-test/messaging",
        "langgraph-test/inbox",
        "langgraph-test/dramatiq_queue",
        "interfaces",
        "interfaces/web",
        "tests",
        "task_queue"
    ]

    all_good = True
    for package in packages:
        init_file = Path(package) / "__init__.py"
        if init_file.exists():
            print(f"✅ {package}/__init__.py exists")
        else:
            print(f"❌ {package}/__init__.py missing")
            all_good = False

    return all_good


def main():
    """Run all Phase 0 tests"""
    print("=" * 60)
    print("PHASE 0 VERIFICATION TESTS")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("TMUX Delay Test", test_tmux_delay),
        ("Project Paths Test", test_project_paths),
        ("TMUX Client Test", test_tmux_client),
        ("Package Structure Test", test_package_structure),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 Phase 0 is COMPLETE!")
        return 0
    else:
        print("\n⚠️  Phase 0 has issues that need fixing")
        return 1


if __name__ == "__main__":
    sys.exit(main())