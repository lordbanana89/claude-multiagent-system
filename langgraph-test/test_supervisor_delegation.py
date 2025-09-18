#!/usr/bin/env python3
"""
🧪 Test del Supervisor Agent - Delegazione Task
Test completo della funzionalità di delegazione task agli agenti
"""

import sys
import time
import json
from datetime import datetime
from typing import Dict, List

sys.path.append('/Users/erik/Desktop/claude-multiagent-system/langgraph-test')
from supervisor_agent import SupervisorAgent

class SupervisorDelegationTester:
    """Tester per la delegazione task del Supervisor Agent"""

    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log dei risultati test"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")

    def test_single_agent_delegation(self) -> bool:
        """Test 1: Delegazione task a singolo agente"""
        print("\n🧪 Test 1: Delegazione task a singolo agente")

        try:
            task_description = f"TEST DELEGATION {datetime.now().strftime('%H:%M:%S')} - Rispondi con 'TASK COMPLETATO'"
            task_id = self.supervisor.delegate_task(task_description, "backend-api")

            if task_id:
                self.log_test("Single Agent Delegation", True, f"Task {task_id} delegato a backend-api")

                # Aspetta e verifica status
                time.sleep(5)
                status = self.supervisor.check_agent_status("backend-api")

                if status.get("current_task"):
                    self.log_test("Task Assignment Verification", True, f"Task assegnato correttamente")
                    return True
                else:
                    self.log_test("Task Assignment Verification", False, "Task non trovato nello status agente")
                    return False
            else:
                self.log_test("Single Agent Delegation", False, "Delegazione fallita")
                return False

        except Exception as e:
            self.log_test("Single Agent Delegation", False, f"Errore: {e}")
            return False

    def test_multiple_agents_delegation(self) -> bool:
        """Test 2: Delegazione task a multipli agenti"""
        print("\n🧪 Test 2: Delegazione task a multipli agenti")

        agents_to_test = ["backend-api", "database", "frontend-ui"]
        successful_delegations = []

        try:
            for agent_id in agents_to_test:
                task_description = f"MULTI-TEST {datetime.now().strftime('%H:%M:%S')} for {agent_id}"
                task_id = self.supervisor.delegate_task(task_description, agent_id)

                if task_id:
                    successful_delegations.append((agent_id, task_id))
                    self.log_test(f"Delegation to {agent_id}", True, f"Task {task_id}")
                else:
                    self.log_test(f"Delegation to {agent_id}", False, "Delegazione fallita")

            success_rate = len(successful_delegations) / len(agents_to_test)
            if success_rate >= 0.8:  # 80% success rate
                self.log_test("Multiple Agents Delegation", True, f"Success rate: {success_rate:.1%}")
                return True
            else:
                self.log_test("Multiple Agents Delegation", False, f"Success rate troppo basso: {success_rate:.1%}")
                return False

        except Exception as e:
            self.log_test("Multiple Agents Delegation", False, f"Errore: {e}")
            return False

    def test_agent_status_monitoring(self) -> bool:
        """Test 3: Monitoraggio status agenti"""
        print("\n🧪 Test 3: Monitoraggio status agenti")

        try:
            # Testa status di tutti gli agenti
            report = self.supervisor.monitor_all_agents()

            if report and "agents" in report:
                working_agents = 0
                total_agents = len(report["agents"])

                for agent_id, status in report["agents"].items():
                    if not status.get("error"):
                        working_agents += 1
                        self.log_test(f"Status Check {agent_id}", True, f"Status: {status.get('status', 'unknown')}")
                    else:
                        self.log_test(f"Status Check {agent_id}", False, f"Errore: {status['error']}")

                success_rate = working_agents / total_agents
                if success_rate >= 0.8:
                    self.log_test("Agent Status Monitoring", True, f"Agents attivi: {working_agents}/{total_agents}")
                    return True
                else:
                    self.log_test("Agent Status Monitoring", False, f"Troppi agenti non funzionanti: {working_agents}/{total_agents}")
                    return False
            else:
                self.log_test("Agent Status Monitoring", False, "Report non valido")
                return False

        except Exception as e:
            self.log_test("Agent Status Monitoring", False, f"Errore: {e}")
            return False

    def test_task_completion(self) -> bool:
        """Test 4: Completamento task"""
        print("\n🧪 Test 4: Completamento task")

        try:
            # Prima delega un task
            task_description = f"COMPLETION TEST {datetime.now().strftime('%H:%M:%S')}"
            task_id = self.supervisor.delegate_task(task_description, "testing")

            if not task_id:
                self.log_test("Task Completion Setup", False, "Impossibile delegare task per test")
                return False

            # Aspetta un po'
            time.sleep(3)

            # Completa il task
            success = self.supervisor.complete_task("testing", "Task completato dal test automatico")

            if success:
                self.log_test("Task Completion", True, f"Task {task_id} completato con successo")

                # Verifica che il task non sia più attivo
                if "testing" not in self.supervisor.active_tasks:
                    self.log_test("Task Cleanup", True, "Task rimosso dalla lista attiva")
                    return True
                else:
                    self.log_test("Task Cleanup", False, "Task ancora presente nella lista attiva")
                    return False
            else:
                self.log_test("Task Completion", False, "Completamento task fallito")
                return False

        except Exception as e:
            self.log_test("Task Completion", False, f"Errore: {e}")
            return False

    def test_system_recovery(self) -> bool:
        """Test 5: Sistema di recovery/reset"""
        print("\n🧪 Test 5: Sistema di recovery/reset")

        try:
            # Testa emergency reset
            success = self.supervisor.emergency_reset_all()

            if success:
                self.log_test("Emergency Reset", True, "Reset di emergenza completato")

                # Verifica che non ci siano task attivi
                if not self.supervisor.active_tasks:
                    self.log_test("Task Clear After Reset", True, "Tutti i task attivi sono stati rimossi")
                    return True
                else:
                    self.log_test("Task Clear After Reset", False, f"Task ancora attivi: {list(self.supervisor.active_tasks.keys())}")
                    return False
            else:
                self.log_test("Emergency Reset", False, "Reset di emergenza fallito")
                return False

        except Exception as e:
            self.log_test("Emergency Reset", False, f"Errore: {e}")
            return False

    def run_all_tests(self) -> Dict:
        """Esegue tutti i test e ritorna il report"""
        print("🚀 Avvio Test Suite - Supervisor Agent Delegation")
        print("=" * 60)

        tests = [
            self.test_single_agent_delegation,
            self.test_multiple_agents_delegation,
            self.test_agent_status_monitoring,
            self.test_task_completion,
            self.test_system_recovery
        ]

        passed_tests = 0

        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                time.sleep(2)  # Pausa tra test
            except Exception as e:
                print(f"❌ Errore durante esecuzione test {test_func.__name__}: {e}")

        # Report finale
        print("\n" + "=" * 60)
        print("📊 REPORT FINALE TEST")
        print("=" * 60)

        total_tests = len(tests)
        success_rate = passed_tests / total_tests

        print(f"Test completati: {passed_tests}/{total_tests}")
        print(f"Success rate: {success_rate:.1%}")

        if success_rate >= 0.8:
            print("✅ TEST SUITE: PASSATA")
        else:
            print("❌ TEST SUITE: FALLITA")

        # Dettagli risultati
        print("\n📋 Dettagli test:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "suite_passed": success_rate >= 0.8,
            "results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Main test execution"""
    tester = SupervisorDelegationTester()
    report = tester.run_all_tests()

    # Salva report
    report_file = f"/Users/erik/Desktop/claude-multiagent-system/langgraph-test/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Report salvato in: {report_file}")
    except Exception as e:
        print(f"❌ Errore salvataggio report: {e}")

    return report["suite_passed"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)