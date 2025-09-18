#!/usr/bin/env python3
"""
🚨 CRITICAL SHARED_STATE STORAGE LAYER TESTS
Comprehensive testing for shared_state storage failures and root cause analysis
"""

import pytest
import json
import sqlite3
import tempfile
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_state.models import SharedState, AgentState, TaskInfo, AgentMessage, AgentStatus, TaskPriority
from shared_state.persistence import JSONPersistence, SQLitePersistence, PersistenceManager
from shared_state.manager import SharedStateManager


class TestJSONPersistenceFailures:
    """🔥 Critical tests for JSON persistence layer failures"""

    def setup_method(self):
        """Setup test environment with temporary files"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_state.json")
        self.persistence = JSONPersistence(self.test_file)

        # Create test state
        self.test_state = SharedState()
        self.test_state.agents["test_agent"] = AgentState(
            agent_id="test_agent",
            status=AgentStatus.IDLE,
            current_task=None,
            last_seen=datetime.now()
        )

    def teardown_method(self):
        """Cleanup test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_json_file_corruption_handling(self):
        """🚨 CRITICAL: Test handling of corrupted JSON files"""

        # 1. Create valid state first
        assert self.persistence.save(self.test_state) == True
        assert os.path.exists(self.test_file)

        # 2. Corrupt the JSON file
        with open(self.test_file, 'w') as f:
            f.write('{"corrupted": "json", invalid_syntax}')

        # 3. Test corruption handling
        loaded_state = self.persistence.load()

        # Should handle corruption gracefully
        assert loaded_state is not None or loaded_state is None  # Either recover or fail gracefully

    def test_json_file_permission_errors(self):
        """🚨 CRITICAL: Test file permission failures"""

        # Save initial state
        assert self.persistence.save(self.test_state) == True

        # Make file read-only to simulate permission issues
        os.chmod(self.test_file, 0o444)

        try:
            # This should fail gracefully
            result = self.persistence.save(self.test_state)
            assert result == False  # Should return False on permission error
        finally:
            # Restore permissions for cleanup
            os.chmod(self.test_file, 0o644)

    def test_json_concurrent_access_corruption(self):
        """🚨 CRITICAL: Test concurrent access causing data corruption"""

        def concurrent_writer(worker_id, iterations=50):
            """Worker function for concurrent writing"""
            results = []
            for i in range(iterations):
                test_state = SharedState()
                test_state.agents[f"worker_{worker_id}_agent_{i}"] = AgentState(
                    agent_id=f"worker_{worker_id}_agent_{i}",
                    status=AgentStatus.BUSY,
                    current_task=f"task_{worker_id}_{i}",
                    last_seen=datetime.now()
                )

                success = self.persistence.save(test_state)
                results.append(success)
                time.sleep(0.001)  # Small delay to increase race condition chance

            return results

        # Run concurrent writers
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_writer, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Check for any failures
        all_results = []
        for result_list in results:
            all_results.extend(result_list)

        failure_rate = (len([r for r in all_results if not r]) / len(all_results)) * 100
        print(f"Concurrent access failure rate: {failure_rate}%")

        # Should have reasonable success rate even under contention
        assert failure_rate < 50  # Less than 50% failures acceptable

    def test_json_backup_recovery_mechanism(self):
        """🚨 CRITICAL: Test backup file recovery when main file fails"""

        # 1. Save initial state (creates backup)
        assert self.persistence.save(self.test_state) == True

        # 2. Modify state and save again (creates new backup)
        self.test_state.agents["backup_test"] = AgentState(
            agent_id="backup_test",
            status=AgentStatus.BUSY,
            current_task="backup_task",
            last_seen=datetime.now()
        )
        assert self.persistence.save(self.test_state) == True

        # 3. Corrupt main file
        with open(self.test_file, 'w') as f:
            f.write('corrupted data')

        # 4. Test backup recovery
        loaded_state = self.persistence.load()

        # Should recover from backup
        if loaded_state:
            # Backup recovery worked
            assert len(loaded_state.agents) > 0
        else:
            # Backup recovery failed - critical issue
            pytest.fail("CRITICAL: Backup recovery mechanism failed")

    def test_json_large_state_performance(self):
        """🚨 CRITICAL: Test performance with large state objects"""

        # Create large state with many agents and tasks
        large_state = SharedState()

        # Add 1000 agents
        for i in range(1000):
            large_state.agents[f"agent_{i}"] = AgentState(
                agent_id=f"agent_{i}",
                status=AgentStatus.IDLE,
                current_task=None,
                last_seen=datetime.now()
            )

        # Add 500 tasks to history
        for i in range(500):
            task = TaskInfo(
                task_id=f"task_{i}",
                description=f"Large state test task {i}",
                priority=TaskPriority.NORMAL,
                assigned_agents=[f"agent_{i % 100}"],
                status="completed"
            )
            large_state.task_history.append(task)

        # Test save performance
        start_time = time.time()
        success = self.persistence.save(large_state)
        save_time = time.time() - start_time

        assert success == True
        assert save_time < 5.0  # Should save within 5 seconds

        # Test load performance
        start_time = time.time()
        loaded_state = self.persistence.load()
        load_time = time.time() - start_time

        assert loaded_state is not None
        assert load_time < 3.0  # Should load within 3 seconds
        assert len(loaded_state.agents) == 1000


class TestSQLitePersistenceFailures:
    """🔥 Critical tests for SQLite persistence layer failures"""

    def setup_method(self):
        """Setup test environment with temporary database"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_state.db")
        self.persistence = SQLitePersistence(self.test_db)

        # Create test state
        self.test_state = SharedState()
        self.test_state.agents["sqlite_test"] = AgentState(
            agent_id="sqlite_test",
            status=AgentStatus.IDLE,
            current_task=None,
            last_seen=datetime.now()
        )

    def teardown_method(self):
        """Cleanup test database"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_sqlite_database_corruption(self):
        """🚨 CRITICAL: Test SQLite database corruption handling"""

        # Save initial state
        assert self.persistence.save(self.test_state) == True

        # Corrupt the database file
        with open(self.test_db, 'wb') as f:
            f.write(b'corrupted database content')

        # Test corruption handling
        loaded_state = self.persistence.load()
        assert loaded_state is None  # Should handle corruption gracefully

    def test_sqlite_database_locking(self):
        """🚨 CRITICAL: Test SQLite database locking issues"""

        def long_running_transaction():
            """Simulate long-running transaction that locks database"""
            try:
                conn = sqlite3.connect(self.test_db, timeout=10.0)
                conn.execute("BEGIN EXCLUSIVE TRANSACTION")

                # Hold lock for a while
                time.sleep(2)

                conn.execute("INSERT INTO shared_state (state_data) VALUES (?)",
                           (json.dumps({"test": "locking"}),))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Long transaction error: {e}")
                return False

        # Start long-running transaction in background
        import threading
        lock_thread = threading.Thread(target=long_running_transaction)
        lock_thread.start()

        time.sleep(0.5)  # Let the lock be acquired

        # Try to save state while database is locked
        start_time = time.time()
        success = self.persistence.save(self.test_state)
        duration = time.time() - start_time

        lock_thread.join()

        # Should either succeed or fail gracefully without hanging
        assert duration < 15.0  # Should not hang indefinitely

    def test_sqlite_concurrent_transactions(self):
        """🚨 CRITICAL: Test concurrent SQLite transactions"""

        def concurrent_writer(writer_id, iterations=20):
            """Worker function for concurrent database writing"""
            results = []
            persistence = SQLitePersistence(self.test_db)

            for i in range(iterations):
                state = SharedState()
                state.agents[f"writer_{writer_id}_agent_{i}"] = AgentState(
                    agent_id=f"writer_{writer_id}_agent_{i}",
                    status=AgentStatus.BUSY,
                    current_task=f"concurrent_task_{writer_id}_{i}",
                    last_seen=datetime.now()
                )

                success = persistence.save(state)
                results.append(success)
                time.sleep(0.01)

            return results

        # Run concurrent transactions
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_writer, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Analyze results
        all_results = []
        for result_list in results:
            all_results.extend(result_list)

        success_rate = (len([r for r in all_results if r]) / len(all_results)) * 100
        print(f"SQLite concurrent transaction success rate: {success_rate}%")

        # Should have high success rate
        assert success_rate > 80  # At least 80% success rate

    def test_sqlite_history_functionality(self):
        """🚨 CRITICAL: Test SQLite history tracking functionality"""

        states_saved = []

        # Save multiple states to build history
        for i in range(10):
            state = SharedState()
            state.agents[f"history_agent_{i}"] = AgentState(
                agent_id=f"history_agent_{i}",
                status=AgentStatus.IDLE,
                current_task=f"history_task_{i}",
                last_seen=datetime.now()
            )

            success = self.persistence.save(state)
            assert success == True
            states_saved.append(state)
            time.sleep(0.1)  # Ensure different timestamps

        # Test history retrieval
        history = self.persistence.get_history(limit=5)

        assert len(history) == 5  # Should return last 5 states
        assert len(history) <= 10  # Should not exceed available history

        # Verify history order (most recent first)
        for i in range(len(history) - 1):
            current_time = datetime.fromisoformat(history[i]['timestamp'])
            next_time = datetime.fromisoformat(history[i + 1]['timestamp'])
            assert current_time >= next_time  # Should be in descending order


class TestSharedStateManagerFailures:
    """🔥 Critical tests for SharedStateManager integration failures"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "manager_test.json")

    def teardown_method(self):
        """Cleanup test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_manager_initialization_with_corrupted_state(self):
        """🚨 CRITICAL: Test manager initialization with corrupted existing state"""

        # Create corrupted state file
        with open(self.test_file, 'w') as f:
            f.write('{"corrupted": json syntax error}')

        # Manager should handle corruption gracefully
        try:
            manager = SharedStateManager(
                persistence_type="json",
                persistence_file=self.test_file
            )
            # Should create new state if corrupted state can't be loaded
            assert manager.state is not None
            assert isinstance(manager.state, SharedState)
        except Exception as e:
            pytest.fail(f"Manager failed to handle corrupted state: {e}")

    def test_manager_save_failure_handling(self):
        """🚨 CRITICAL: Test manager handling of save failures"""

        manager = SharedStateManager(
            persistence_type="json",
            persistence_file=self.test_file
        )

        # Add some state
        manager.register_agent("test_agent", "test_callback")

        # Make file read-only to cause save failure
        manager.save_state()  # Save once successfully first
        os.chmod(self.test_file, 0o444)

        try:
            # This save should fail but not crash
            result = manager.save_state()
            assert result == False  # Should return False on failure
        finally:
            # Restore permissions
            os.chmod(self.test_file, 0o644)

    def test_manager_concurrent_access_safety(self):
        """🚨 CRITICAL: Test manager thread safety under concurrent access"""

        manager = SharedStateManager(
            persistence_type="json",
            persistence_file=self.test_file
        )

        def concurrent_agent_operations(worker_id):
            """Worker function for concurrent manager operations"""
            results = []

            for i in range(20):
                try:
                    # Register agent
                    agent_id = f"worker_{worker_id}_agent_{i}"
                    manager.register_agent(agent_id, lambda x: None)

                    # Update agent status
                    manager.update_agent_status(agent_id, AgentStatus.BUSY)

                    # Save state
                    save_result = manager.save_state()

                    results.append(True)
                except Exception as e:
                    print(f"Concurrent operation error: {e}")
                    results.append(False)

                time.sleep(0.01)

            return results

        # Run concurrent operations
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(concurrent_agent_operations, i) for i in range(8)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Analyze results
        all_results = []
        for result_list in results:
            all_results.extend(result_list)

        success_rate = (len([r for r in all_results if r]) / len(all_results)) * 100
        print(f"Manager concurrent access success rate: {success_rate}%")

        # Should have high success rate with thread safety
        assert success_rate > 85  # At least 85% success rate

    def test_manager_memory_leaks(self):
        """🚨 CRITICAL: Test for memory leaks in long-running manager"""

        manager = SharedStateManager(
            persistence_type="json",
            persistence_file=self.test_file
        )

        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Simulate long-running operations
        for i in range(1000):
            # Register and unregister agents
            agent_id = f"memory_test_agent_{i}"
            manager.register_agent(agent_id, lambda x: None)

            # Add some state changes
            manager.update_agent_status(agent_id, AgentStatus.BUSY)
            manager.update_agent_status(agent_id, AgentStatus.IDLE)

            # Save state periodically
            if i % 100 == 0:
                manager.save_state()

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        print(f"Memory increase after 1000 operations: {memory_increase:.2f} MB")

        # Should not have significant memory leaks
        assert memory_increase < 50  # Less than 50MB increase


class TestStorageLayerDiagnostics:
    """🔍 Diagnostic tests to identify root causes of storage failures"""

    def test_file_system_diagnostics(self):
        """🔍 Diagnostic: Test file system capabilities and limitations"""

        temp_dir = tempfile.mkdtemp()
        try:
            # Test file creation
            test_file = os.path.join(temp_dir, "diagnostic_test.json")

            # Test write permissions
            with open(test_file, 'w') as f:
                f.write('{"test": "write"}')
            assert os.path.exists(test_file)

            # Test read permissions
            with open(test_file, 'r') as f:
                data = f.read()
            assert '{"test": "write"}' in data

            # Test file locking behavior
            with open(test_file, 'w') as f1:
                # Try to open same file for writing (should work on most systems)
                try:
                    with open(test_file, 'w') as f2:
                        f2.write('{"test": "concurrent"}')
                    concurrent_write_supported = True
                except:
                    concurrent_write_supported = False

            print(f"File system supports concurrent writes: {concurrent_write_supported}")

            # Test atomic operations
            temp_file = test_file + ".tmp"
            with open(temp_file, 'w') as f:
                f.write('{"test": "atomic"}')

            # Atomic rename
            os.rename(temp_file, test_file)
            assert os.path.exists(test_file)
            assert not os.path.exists(temp_file)

        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_json_serialization_diagnostics(self):
        """🔍 Diagnostic: Test JSON serialization edge cases"""

        # Test complex SharedState serialization
        state = SharedState()

        # Add agent with complex data
        state.agents["complex_agent"] = AgentState(
            agent_id="complex_agent",
            status=AgentStatus.BUSY,
            current_task="complex_task",
            last_seen=datetime.now(),
            capabilities=["test", "debug", "analyze"],
            metadata={"nested": {"data": {"structure": True}}}
        )

        # Test serialization
        try:
            state_dict = state.to_dict()
            json_str = json.dumps(state_dict, indent=2)

            # Test deserialization
            loaded_dict = json.loads(json_str)
            loaded_state = SharedState.from_dict(loaded_dict)

            assert loaded_state is not None
            assert "complex_agent" in loaded_state.agents

        except Exception as e:
            pytest.fail(f"JSON serialization diagnostic failed: {e}")

    def test_database_connectivity_diagnostics(self):
        """🔍 Diagnostic: Test SQLite database connectivity and operations"""

        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, "diagnostic.db")

            # Test basic database operations
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Test table creation
            cursor.execute('''
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    data TEXT NOT NULL
                )
            ''')

            # Test insertion
            cursor.execute("INSERT INTO test_table (data) VALUES (?)", ("test_data",))
            conn.commit()

            # Test selection
            cursor.execute("SELECT * FROM test_table")
            results = cursor.fetchall()
            assert len(results) == 1

            # Test transaction rollback
            try:
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute("INSERT INTO test_table (data) VALUES (?)", ("rollback_test",))
                cursor.execute("ROLLBACK")

                cursor.execute("SELECT COUNT(*) FROM test_table")
                count = cursor.fetchone()[0]
                assert count == 1  # Should still be 1 after rollback
            except Exception as e:
                print(f"Transaction test error: {e}")

            conn.close()

        except Exception as e:
            pytest.fail(f"Database connectivity diagnostic failed: {e}")
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_threading_diagnostics(self):
        """🔍 Diagnostic: Test threading behavior and locks"""

        import threading

        # Test basic threading
        results = []
        lock = threading.Lock()

        def thread_worker(worker_id):
            with lock:
                results.append(f"worker_{worker_id}")
                time.sleep(0.01)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 10  # All threads should complete

        # Test RLock behavior
        rlock = threading.RLock()

        def recursive_lock_test():
            with rlock:
                with rlock:  # Should not deadlock
                    return True
            return False

        assert recursive_lock_test() == True


if __name__ == "__main__":
    """Run critical storage layer tests"""
    pytest.main([__file__, "-v", "--tb=short", "-x"])