#!/usr/bin/env python3
"""
🚨 CRITICAL SHARED_STATE DIAGNOSTIC TOOL
Root cause analysis and validation testing for storage layer failures
"""

import os
import sys
import json
import sqlite3
import tempfile
import time
import threading
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_state.models import SharedState, AgentState, TaskInfo, AgentMessage, AgentStatus, TaskPriority
from shared_state.persistence import JSONPersistence, SQLitePersistence, PersistenceManager
from shared_state.manager import SharedStateManager


class SharedStateDiagnostics:
    """🔍 Comprehensive diagnostics for shared_state storage layer"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "critical_issues": [],
            "warnings": [],
            "performance_metrics": {}
        }

    def run_all_diagnostics(self):
        """Execute all diagnostic tests"""
        print("🚨 STARTING CRITICAL SHARED_STATE DIAGNOSTICS")
        print("=" * 60)

        # Test 1: Model validation
        self.test_model_structure()

        # Test 2: JSON persistence
        self.test_json_persistence()

        # Test 3: SQLite persistence
        self.test_sqlite_persistence()

        # Test 4: Manager functionality
        self.test_manager_functionality()

        # Test 5: Concurrent access
        self.test_concurrent_access()

        # Test 6: Performance under load
        self.test_performance()

        # Test 7: Real shared_state file validation
        self.test_existing_shared_state()

        # Generate summary
        self.generate_summary()

        return self.results

    def test_model_structure(self):
        """Test data model structure and serialization"""
        print("\n🔍 Testing Model Structure...")

        try:
            # Test SharedState creation
            state = SharedState()
            self.results["tests"]["model_creation"] = "PASS"

            # Test AgentState creation with correct parameters
            agent = AgentState(
                agent_id="test_agent",
                name="Test Agent",
                status=AgentStatus.IDLE
            )
            state.agents["test_agent"] = agent
            self.results["tests"]["agent_model"] = "PASS"

            # Test TaskInfo creation
            task = TaskInfo(
                task_id="test_task",
                description="Test task",
                priority=TaskPriority.NORMAL,
                assigned_agents=["test_agent"]
            )
            state.task_history.append(task)
            self.results["tests"]["task_model"] = "PASS"

            # Test serialization
            state_dict = state.to_dict()
            reconstructed = SharedState.from_dict(state_dict)

            if len(reconstructed.agents) == 1 and len(reconstructed.task_history) == 1:
                self.results["tests"]["serialization"] = "PASS"
                print("✅ Model structure tests PASSED")
            else:
                self.results["tests"]["serialization"] = "FAIL"
                self.results["critical_issues"].append("Serialization/deserialization failed")
                print("❌ Model serialization FAILED")

        except Exception as e:
            self.results["tests"]["model_structure"] = f"FAIL: {e}"
            self.results["critical_issues"].append(f"Model structure error: {e}")
            print(f"❌ Model structure test FAILED: {e}")

    def test_json_persistence(self):
        """Test JSON persistence layer"""
        print("\n🔍 Testing JSON Persistence...")

        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "diagnostic_test.json")

        try:
            persistence = JSONPersistence(test_file)

            # Create test state
            state = SharedState()
            state.agents["json_test"] = AgentState(
                agent_id="json_test",
                name="JSON Test Agent",
                status=AgentStatus.IDLE,
                current_task="testing_json"
            )

            # Test save
            start_time = time.time()
            save_result = persistence.save(state)
            save_time = time.time() - start_time

            if save_result and os.path.exists(test_file):
                self.results["tests"]["json_save"] = "PASS"
                self.results["performance_metrics"]["json_save_time"] = save_time
                print(f"✅ JSON save successful ({save_time:.3f}s)")
            else:
                self.results["tests"]["json_save"] = "FAIL"
                self.results["critical_issues"].append("JSON save failed")
                print("❌ JSON save FAILED")
                return

            # Test load
            start_time = time.time()
            loaded_state = persistence.load()
            load_time = time.time() - start_time

            if loaded_state and "json_test" in loaded_state.agents:
                self.results["tests"]["json_load"] = "PASS"
                self.results["performance_metrics"]["json_load_time"] = load_time
                print(f"✅ JSON load successful ({load_time:.3f}s)")
            else:
                self.results["tests"]["json_load"] = "FAIL"
                self.results["critical_issues"].append("JSON load failed")
                print("❌ JSON load FAILED")

            # Test file corruption recovery
            with open(test_file, 'w') as f:
                f.write('{"corrupted": "json"')  # Invalid JSON

            recovery_state = persistence.load()
            if recovery_state is None:
                self.results["tests"]["json_corruption_handling"] = "PASS"
                print("✅ JSON corruption handled gracefully")
            else:
                self.results["tests"]["json_corruption_handling"] = "FAIL"
                self.results["warnings"].append("JSON corruption not handled properly")

        except Exception as e:
            self.results["tests"]["json_persistence"] = f"FAIL: {e}"
            self.results["critical_issues"].append(f"JSON persistence error: {e}")
            print(f"❌ JSON persistence test FAILED: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_sqlite_persistence(self):
        """Test SQLite persistence layer"""
        print("\n🔍 Testing SQLite Persistence...")

        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "diagnostic_test.db")

        try:
            persistence = SQLitePersistence(test_db)

            # Create test state
            state = SharedState()
            state.agents["sqlite_test"] = AgentState(
                agent_id="sqlite_test",
                name="SQLite Test Agent",
                status=AgentStatus.BUSY,
                current_task="testing_sqlite"
            )

            # Test save
            start_time = time.time()
            save_result = persistence.save(state)
            save_time = time.time() - start_time

            if save_result:
                self.results["tests"]["sqlite_save"] = "PASS"
                self.results["performance_metrics"]["sqlite_save_time"] = save_time
                print(f"✅ SQLite save successful ({save_time:.3f}s)")
            else:
                self.results["tests"]["sqlite_save"] = "FAIL"
                self.results["critical_issues"].append("SQLite save failed")
                print("❌ SQLite save FAILED")
                return

            # Test load
            start_time = time.time()
            loaded_state = persistence.load()
            load_time = time.time() - start_time

            if loaded_state and "sqlite_test" in loaded_state.agents:
                self.results["tests"]["sqlite_load"] = "PASS"
                self.results["performance_metrics"]["sqlite_load_time"] = load_time
                print(f"✅ SQLite load successful ({load_time:.3f}s)")
            else:
                self.results["tests"]["sqlite_load"] = "FAIL"
                self.results["critical_issues"].append("SQLite load failed")
                print("❌ SQLite load FAILED")

            # Test history functionality
            history = persistence.get_history(limit=5)
            if isinstance(history, list):
                self.results["tests"]["sqlite_history"] = "PASS"
                print(f"✅ SQLite history successful ({len(history)} records)")
            else:
                self.results["tests"]["sqlite_history"] = "FAIL"
                self.results["warnings"].append("SQLite history functionality failed")

        except Exception as e:
            self.results["tests"]["sqlite_persistence"] = f"FAIL: {e}"
            self.results["critical_issues"].append(f"SQLite persistence error: {e}")
            print(f"❌ SQLite persistence test FAILED: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_manager_functionality(self):
        """Test SharedStateManager functionality"""
        print("\n🔍 Testing SharedStateManager...")

        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "manager_test.json")

        try:
            # Test manager initialization
            manager = SharedStateManager(
                persistence_type="json",
                persistence_file=test_file
            )
            self.results["tests"]["manager_init"] = "PASS"
            print("✅ Manager initialization successful")

            # Test agent registration
            def dummy_callback(data):
                pass

            manager.register_agent("test_manager_agent", dummy_callback)

            if "test_manager_agent" in manager.state.agents:
                self.results["tests"]["agent_registration"] = "PASS"
                print("✅ Agent registration successful")
            else:
                self.results["tests"]["agent_registration"] = "FAIL"
                self.results["critical_issues"].append("Agent registration failed")

            # Test state saving
            save_result = manager.save_state()
            if save_result:
                self.results["tests"]["manager_save"] = "PASS"
                print("✅ Manager save successful")
            else:
                self.results["tests"]["manager_save"] = "FAIL"
                self.results["critical_issues"].append("Manager save failed")

            # Test agent status update
            manager.update_agent_status("test_manager_agent", AgentStatus.BUSY)
            agent_state = manager.state.agents.get("test_manager_agent")

            if agent_state and agent_state.status == AgentStatus.BUSY:
                self.results["tests"]["status_update"] = "PASS"
                print("✅ Status update successful")
            else:
                self.results["tests"]["status_update"] = "FAIL"
                self.results["warnings"].append("Status update failed")

        except Exception as e:
            self.results["tests"]["manager_functionality"] = f"FAIL: {e}"
            self.results["critical_issues"].append(f"Manager functionality error: {e}")
            print(f"❌ Manager functionality test FAILED: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_concurrent_access(self):
        """Test concurrent access safety"""
        print("\n🔍 Testing Concurrent Access...")

        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "concurrent_test.json")

        try:
            manager = SharedStateManager(
                persistence_type="json",
                persistence_file=test_file
            )

            def concurrent_worker(worker_id):
                """Worker function for concurrent testing"""
                try:
                    for i in range(10):
                        agent_id = f"worker_{worker_id}_agent_{i}"
                        manager.register_agent(agent_id, lambda x: None)
                        manager.update_agent_status(agent_id, AgentStatus.BUSY)
                        manager.save_state()
                        time.sleep(0.001)
                    return True
                except Exception as e:
                    print(f"Concurrent worker {worker_id} error: {e}")
                    return False

            # Run concurrent workers
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_worker, i) for i in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

            success_count = sum(results)
            if success_count == 5:
                self.results["tests"]["concurrent_access"] = "PASS"
                print("✅ Concurrent access test successful")
            else:
                self.results["tests"]["concurrent_access"] = f"PARTIAL: {success_count}/5"
                self.results["warnings"].append(f"Concurrent access partially failed: {success_count}/5")

        except Exception as e:
            self.results["tests"]["concurrent_access"] = f"FAIL: {e}"
            self.results["critical_issues"].append(f"Concurrent access error: {e}")
            print(f"❌ Concurrent access test FAILED: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_performance(self):
        """Test performance under load"""
        print("\n🔍 Testing Performance Under Load...")

        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "performance_test.json")

        try:
            manager = SharedStateManager(
                persistence_type="json",
                persistence_file=test_file
            )

            # Test large state performance
            start_time = time.time()

            # Add 100 agents
            for i in range(100):
                agent_id = f"perf_agent_{i}"
                manager.register_agent(agent_id, lambda x: None)
                manager.update_agent_status(agent_id, AgentStatus.IDLE)

            # Add 50 tasks
            for i in range(50):
                task = TaskInfo(
                    task_id=f"perf_task_{i}",
                    description=f"Performance test task {i}",
                    priority=TaskPriority.NORMAL,
                    assigned_agents=[f"perf_agent_{i % 10}"]
                )
                manager.state.task_history.append(task)

            # Save large state
            save_start = time.time()
            save_result = manager.save_state()
            save_time = time.time() - save_start

            total_time = time.time() - start_time

            if save_result and save_time < 5.0:
                self.results["tests"]["performance"] = "PASS"
                self.results["performance_metrics"]["large_state_save"] = save_time
                self.results["performance_metrics"]["total_setup_time"] = total_time
                print(f"✅ Performance test successful (save: {save_time:.3f}s, total: {total_time:.3f}s)")
            else:
                self.results["tests"]["performance"] = "FAIL"
                self.results["critical_issues"].append(f"Performance test failed: save_time={save_time:.3f}s")

        except Exception as e:
            self.results["tests"]["performance"] = f"FAIL: {e}"
            self.results["critical_issues"].append(f"Performance test error: {e}")
            print(f"❌ Performance test FAILED: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_existing_shared_state(self):
        """Test the actual shared_state.json file"""
        print("\n🔍 Testing Existing shared_state.json...")

        current_file = "shared_state.json"
        if not os.path.exists(current_file):
            self.results["tests"]["existing_file"] = "SKIP: File not found"
            print("⚠️ shared_state.json not found")
            return

        try:
            # Test loading existing file
            persistence = JSONPersistence(current_file)
            loaded_state = persistence.load()

            if loaded_state:
                self.results["tests"]["existing_file_load"] = "PASS"
                self.results["performance_metrics"]["existing_agents"] = len(loaded_state.agents)
                self.results["performance_metrics"]["existing_tasks"] = len(loaded_state.task_history)
                print(f"✅ Existing file loaded: {len(loaded_state.agents)} agents, {len(loaded_state.task_history)} tasks")

                # Test file size
                file_size = os.path.getsize(current_file) / 1024  # KB
                self.results["performance_metrics"]["file_size_kb"] = file_size

                if file_size > 1000:  # > 1MB
                    self.results["warnings"].append(f"Large file size: {file_size:.1f}KB")
            else:
                self.results["tests"]["existing_file_load"] = "FAIL"
                self.results["critical_issues"].append("Failed to load existing shared_state.json")
                print("❌ Failed to load existing shared_state.json")

        except Exception as e:
            self.results["tests"]["existing_file"] = f"FAIL: {e}"
            self.results["critical_issues"].append(f"Existing file error: {e}")
            print(f"❌ Existing file test FAILED: {e}")

    def generate_summary(self):
        """Generate diagnostic summary"""
        print("\n" + "="*60)
        print("🚨 CRITICAL SHARED_STATE DIAGNOSTIC SUMMARY")
        print("="*60)

        # Count results
        total_tests = len(self.results["tests"])
        passed_tests = len([t for t in self.results["tests"].values() if t == "PASS"])
        failed_tests = len([t for t in self.results["tests"].values() if "FAIL" in str(t)])

        print(f"\n📊 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Success Rate: {(passed_tests/total_tests*100):.1f}%")

        # Critical issues
        if self.results["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.results['critical_issues'])}):")
            for issue in self.results["critical_issues"]:
                print(f"   • {issue}")
        else:
            print(f"\n✅ No critical issues found")

        # Warnings
        if self.results["warnings"]:
            print(f"\n⚠️ WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"]:
                print(f"   • {warning}")

        # Performance metrics
        if self.results["performance_metrics"]:
            print(f"\n📈 Performance Metrics:")
            for metric, value in self.results["performance_metrics"].items():
                if isinstance(value, float):
                    print(f"   {metric}: {value:.3f}")
                else:
                    print(f"   {metric}: {value}")

        # Recommendations
        print(f"\n💡 Recommendations:")

        if failed_tests > 0:
            print("   1. Address critical storage layer failures immediately")

        if self.results["performance_metrics"].get("file_size_kb", 0) > 100:
            print("   2. Consider implementing state cleanup/archival")

        if "concurrent_access" in [t for t in self.results["tests"] if "FAIL" in str(self.results["tests"].get(t, ""))]:
            print("   3. Fix concurrent access synchronization issues")

        print("   4. Implement automated storage layer monitoring")
        print("   5. Add storage layer health checks to CI/CD")

        return self.results


if __name__ == "__main__":
    """Run comprehensive shared_state diagnostics"""

    diagnostics = SharedStateDiagnostics()
    results = diagnostics.run_all_diagnostics()

    # Save results to file
    with open("shared_state_diagnostic_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Full diagnostic report saved to: shared_state_diagnostic_report.json")

    # Exit with error code if critical issues found
    if results["critical_issues"]:
        print(f"\n🚨 EXITING WITH ERROR: {len(results['critical_issues'])} critical issues found")
        sys.exit(1)
    else:
        print(f"\n✅ Diagnostics completed successfully")
        sys.exit(0)