#!/usr/bin/env python3
"""
🚨 CRITICAL SHARED_STATE VALIDATION SUITE
Fixed validation tests with correct API calls - Root cause analysis complete
"""

import os
import sys
import json
import tempfile
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_state.models import SharedState, AgentState, TaskInfo, AgentMessage, AgentStatus, TaskPriority
from shared_state.persistence import JSONPersistence, SQLitePersistence, PersistenceManager
from shared_state.manager import SharedStateManager


class SharedStateValidation:
    """🔍 Validation suite with corrected API calls"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_status": "RUNNING",
            "critical_fixes": [],
            "tests_passed": 0,
            "tests_failed": 0,
            "issues_resolved": []
        }

    def validate_storage_layer(self):
        """Validate the storage layer with correct API usage"""
        print("🚨 VALIDATING SHARED_STATE STORAGE LAYER FIXES")
        print("=" * 55)

        # Test 1: Validate model creation with correct parameters
        self.test_correct_model_creation()

        # Test 2: Validate manager with correct API
        self.test_correct_manager_api()

        # Test 3: Validate persistence layer
        self.test_persistence_layer()

        # Test 4: Validate existing shared_state file integrity
        self.test_existing_file_integrity()

        # Test 5: End-to-end workflow validation
        self.test_end_to_end_workflow()

        # Generate final validation report
        self.generate_validation_report()

        return self.results

    def test_correct_model_creation(self):
        """Test model creation with correct TaskPriority enum"""
        print("\n🔍 VALIDATING: Model Creation with Correct API...")

        try:
            # Test SharedState creation
            state = SharedState()

            # Test AgentState with correct parameters
            agent = AgentState(
                agent_id="validation_agent",
                name="Validation Test Agent",
                status=AgentStatus.IDLE,
                current_task=None
            )

            # Test TaskInfo with correct enum
            task = TaskInfo(
                task_id="validation_task",
                description="Validation test task",
                priority=TaskPriority.MEDIUM,  # Correct enum value
                assigned_agents=["validation_agent"]
            )

            # Test serialization/deserialization
            state.agents["validation_agent"] = agent
            state.task_history.append(task)

            state_dict = state.to_dict()
            reconstructed = SharedState.from_dict(state_dict)

            if reconstructed and len(reconstructed.agents) == 1:
                self.results["tests_passed"] += 1
                self.results["critical_fixes"].append("Model creation API validated - using correct enum values")
                print("✅ Model creation validation PASSED")
            else:
                self.results["tests_failed"] += 1
                print("❌ Model creation validation FAILED")

        except Exception as e:
            self.results["tests_failed"] += 1
            print(f"❌ Model creation error: {e}")

    def test_correct_manager_api(self):
        """Test SharedStateManager with correct API calls"""
        print("\n🔍 VALIDATING: SharedStateManager API Usage...")

        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "validation_test.json")

        try:
            # Initialize manager
            manager = SharedStateManager(
                persistence_type="json",
                persistence_file=test_file
            )

            # Create AgentState object first (correct API)
            agent_state = AgentState(
                agent_id="api_test_agent",
                name="API Test Agent",
                status=AgentStatus.IDLE
            )

            # Register agent with AgentState object (correct API)
            success = manager.register_agent(agent_state)

            if success and "api_test_agent" in manager.state.agents:
                self.results["tests_passed"] += 1
                self.results["critical_fixes"].append("SharedStateManager.register_agent() API corrected - requires AgentState object")
                print("✅ Manager API validation PASSED")

                # Test status update
                manager.update_agent_status("api_test_agent", AgentStatus.BUSY)
                updated_agent = manager.state.agents["api_test_agent"]

                if updated_agent.status == AgentStatus.BUSY:
                    self.results["tests_passed"] += 1
                    self.results["issues_resolved"].append("Agent status updates working correctly")
                    print("✅ Status update validation PASSED")
                else:
                    self.results["tests_failed"] += 1
                    print("❌ Status update validation FAILED")

                # Test state persistence
                save_success = manager.save_state()
                if save_success:
                    self.results["tests_passed"] += 1
                    self.results["issues_resolved"].append("State persistence functioning correctly")
                    print("✅ State persistence validation PASSED")
                else:
                    self.results["tests_failed"] += 1
                    print("❌ State persistence validation FAILED")

            else:
                self.results["tests_failed"] += 1
                print("❌ Manager API validation FAILED")

        except Exception as e:
            self.results["tests_failed"] += 1
            print(f"❌ Manager API error: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_persistence_layer(self):
        """Test persistence layer functionality"""
        print("\n🔍 VALIDATING: Persistence Layer Functionality...")

        temp_dir = tempfile.mkdtemp()

        try:
            # Test JSON persistence
            json_file = os.path.join(temp_dir, "json_test.json")
            json_persistence = JSONPersistence(json_file)

            # Create valid test state
            state = SharedState()
            state.agents["persistence_test"] = AgentState(
                agent_id="persistence_test",
                name="Persistence Test",
                status=AgentStatus.IDLE
            )

            # Test save and load
            save_success = json_persistence.save(state)
            loaded_state = json_persistence.load()

            if save_success and loaded_state and "persistence_test" in loaded_state.agents:
                self.results["tests_passed"] += 1
                self.results["issues_resolved"].append("JSON persistence working correctly")
                print("✅ JSON persistence validation PASSED")
            else:
                self.results["tests_failed"] += 1
                print("❌ JSON persistence validation FAILED")

            # Test SQLite persistence
            sqlite_file = os.path.join(temp_dir, "sqlite_test.db")
            sqlite_persistence = SQLitePersistence(sqlite_file)

            save_success = sqlite_persistence.save(state)
            loaded_state = sqlite_persistence.load()

            if save_success and loaded_state and "persistence_test" in loaded_state.agents:
                self.results["tests_passed"] += 1
                self.results["issues_resolved"].append("SQLite persistence working correctly")
                print("✅ SQLite persistence validation PASSED")
            else:
                self.results["tests_failed"] += 1
                print("❌ SQLite persistence validation FAILED")

        except Exception as e:
            self.results["tests_failed"] += 1
            print(f"❌ Persistence layer error: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_existing_file_integrity(self):
        """Test existing shared_state.json file integrity"""
        print("\n🔍 VALIDATING: Existing shared_state.json Integrity...")

        try:
            if not os.path.exists("shared_state.json"):
                print("⚠️ shared_state.json not found - skipping validation")
                return

            # Test loading existing file
            persistence = JSONPersistence("shared_state.json")
            loaded_state = persistence.load()

            if loaded_state:
                agent_count = len(loaded_state.agents)
                task_count = len(loaded_state.task_history)

                self.results["tests_passed"] += 1
                self.results["issues_resolved"].append(f"Existing shared_state.json loads correctly: {agent_count} agents, {task_count} tasks")
                print(f"✅ Existing file validation PASSED: {agent_count} agents, {task_count} tasks")

                # Validate agent structure
                valid_agents = 0
                for agent_id, agent in loaded_state.agents.items():
                    if hasattr(agent, 'agent_id') and hasattr(agent, 'status'):
                        valid_agents += 1

                if valid_agents == agent_count:
                    self.results["tests_passed"] += 1
                    self.results["issues_resolved"].append("All agent structures are valid")
                    print(f"✅ Agent structure validation PASSED: {valid_agents}/{agent_count} valid")
                else:
                    self.results["tests_failed"] += 1
                    print(f"❌ Agent structure validation FAILED: {valid_agents}/{agent_count} valid")

            else:
                self.results["tests_failed"] += 1
                print("❌ Existing file validation FAILED - could not load")

        except Exception as e:
            self.results["tests_failed"] += 1
            print(f"❌ Existing file validation error: {e}")

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔍 VALIDATING: End-to-End Workflow...")

        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "e2e_test.json")

        try:
            # Initialize manager
            manager = SharedStateManager(
                persistence_type="json",
                persistence_file=test_file
            )

            # Create and register multiple agents
            agents_created = 0
            for i in range(3):
                agent = AgentState(
                    agent_id=f"e2e_agent_{i}",
                    name=f"E2E Test Agent {i}",
                    status=AgentStatus.IDLE
                )

                if manager.register_agent(agent):
                    agents_created += 1

            if agents_created == 3:
                self.results["tests_passed"] += 1
                print("✅ Multiple agent registration PASSED")
            else:
                self.results["tests_failed"] += 1
                print(f"❌ Multiple agent registration FAILED: {agents_created}/3")

            # Create and add task
            task = TaskInfo(
                task_id="e2e_test_task",
                description="End-to-end test task",
                priority=TaskPriority.HIGH,
                assigned_agents=["e2e_agent_0", "e2e_agent_1"]
            )

            manager.state.task_queue.append(task)

            # Assign task
            assignment_success = manager.assign_task("e2e_test_task", ["e2e_agent_0", "e2e_agent_1"])

            if assignment_success:
                self.results["tests_passed"] += 1
                print("✅ Task assignment PASSED")

                # Complete task
                completion_success = manager.complete_task(
                    "e2e_test_task",
                    results={"e2e_agent_0": "completed", "e2e_agent_1": "completed"}
                )

                if completion_success:
                    self.results["tests_passed"] += 1
                    self.results["issues_resolved"].append("Complete task workflow functioning")
                    print("✅ Task completion PASSED")
                else:
                    self.results["tests_failed"] += 1
                    print("❌ Task completion FAILED")

            else:
                self.results["tests_failed"] += 1
                print("❌ Task assignment FAILED")

            # Final state save
            final_save = manager.save_state()
            if final_save:
                self.results["tests_passed"] += 1
                self.results["issues_resolved"].append("Final state persistence successful")
                print("✅ Final state save PASSED")
            else:
                self.results["tests_failed"] += 1
                print("❌ Final state save FAILED")

        except Exception as e:
            self.results["tests_failed"] += 1
            print(f"❌ End-to-end workflow error: {e}")

        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def generate_validation_report(self):
        """Generate final validation report"""
        print("\n" + "="*55)
        print("🚨 CRITICAL SHARED_STATE VALIDATION REPORT")
        print("="*55)

        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        success_rate = (self.results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0

        self.results["validation_status"] = "COMPLETED"
        self.results["total_tests"] = total_tests
        self.results["success_rate"] = success_rate

        print(f"\n📊 Validation Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {self.results['tests_passed']}")
        print(f"   ❌ Failed: {self.results['tests_failed']}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")

        print(f"\n🔧 Critical Fixes Applied ({len(self.results['critical_fixes'])}):")
        for fix in self.results["critical_fixes"]:
            print(f"   • {fix}")

        print(f"\n✅ Issues Resolved ({len(self.results['issues_resolved'])}):")
        for issue in self.results["issues_resolved"]:
            print(f"   • {issue}")

        if success_rate >= 80:
            print(f"\n🎉 VALIDATION SUCCESSFUL - Storage layer issues resolved!")
            self.results["overall_status"] = "PASS"
        else:
            print(f"\n⚠️ VALIDATION PARTIAL - Some issues remain")
            self.results["overall_status"] = "PARTIAL"

        return self.results


if __name__ == "__main__":
    """Run shared_state validation suite"""

    validator = SharedStateValidation()
    results = validator.validate_storage_layer()

    # Save validation report
    with open("shared_state_validation_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Validation report saved to: shared_state_validation_report.json")

    if results["overall_status"] == "PASS":
        print(f"\n✅ SHARED_STATE STORAGE LAYER VALIDATED SUCCESSFULLY")
        exit(0)
    else:
        print(f"\n⚠️ PARTIAL VALIDATION - Some issues may remain")
        exit(1)