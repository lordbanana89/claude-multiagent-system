#!/usr/bin/env python3
"""
Test TMUX delay implementation
Comprehensive test of the delay logic in TMUX message delivery
"""

import sys
import os
import time
import subprocess
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from messaging.interface import EnhancedTerminalInterface
from shared_state.models import AgentMessage, MessagePriority


class TMUXDelayTester:
    """Test class for TMUX delay implementation"""

    def __init__(self):
        self.interface = EnhancedTerminalInterface()
        self.test_results = []

    def test_delay_timing_precision(self):
        """Test the exact timing of the delay implementation"""
        print("🔧 Testing TMUX delay timing precision...")

        test_message = AgentMessage(
            message_id="tmux_timing_test",
            sender_id="timing-tester",
            recipient_id="backend-api",
            content="TMUX timing precision test",
            subject="Timing Test",
            priority=MessagePriority.NORMAL
        )

        timing_data = []

        def capture_timing(*args, **kwargs):
            timing_data.append(time.time())
            return MagicMock()

        def capture_sleep_timing(duration):
            timing_data.append(('sleep', time.time(), duration))

        with patch('messaging.interface.subprocess.run', side_effect=capture_timing):
            with patch('time.sleep', side_effect=capture_sleep_timing):

                start_time = time.time()
                self.interface.send_terminal_notification("backend-api", test_message)
                end_time = time.time()

                # Analyze timing data
                total_time = end_time - start_time
                sleep_entry = next((entry for entry in timing_data if isinstance(entry, tuple)), None)

                if sleep_entry:
                    sleep_duration = sleep_entry[2]
                    result = {
                        'test': 'delay_timing_precision',
                        'success': sleep_duration == 0.1,
                        'details': f"Sleep duration: {sleep_duration}s, Total time: {total_time:.3f}s",
                        'expected_delay': 0.1,
                        'actual_delay': sleep_duration
                    }
                else:
                    result = {
                        'test': 'delay_timing_precision',
                        'success': False,
                        'details': "No sleep call detected",
                        'expected_delay': 0.1,
                        'actual_delay': None
                    }

                self.test_results.append(result)
                print(f"✅ Delay timing: {result['details']}")
                return result['success']

    def test_tmux_command_sequence(self):
        """Test the correct sequence of TMUX commands"""
        print("🔧 Testing TMUX command sequence...")

        test_message = AgentMessage(
            message_id="tmux_sequence_test",
            sender_id="sequence-tester",
            recipient_id="backend-api",
            content="TMUX command sequence test",
            subject="Sequence Test",
            priority=MessagePriority.HIGH
        )

        command_calls = []
        sleep_calls = []

        def capture_subprocess_calls(*args, **kwargs):
            # Extract command details
            if len(args) > 0 and isinstance(args[0], list):
                cmd_list = args[0]
                if 'tmux' in cmd_list:
                    command_calls.append({
                        'command': cmd_list,
                        'time': time.time(),
                        'is_echo': 'echo' in ' '.join(cmd_list) if len(cmd_list) > 3 else False,
                        'is_enter': 'Enter' in cmd_list
                    })
            return MagicMock()

        def capture_sleep_calls(duration):
            sleep_calls.append({
                'duration': duration,
                'time': time.time()
            })

        with patch('messaging.interface.subprocess.run', side_effect=capture_subprocess_calls):
            with patch('time.sleep', side_effect=capture_sleep_calls):

                self.interface.send_terminal_notification("backend-api", test_message)

                # Verify sequence: echo command, sleep, Enter command
                expected_sequence = len(command_calls) == 2 and len(sleep_calls) == 1

                if expected_sequence and len(command_calls) >= 2:
                    first_cmd = command_calls[0]
                    second_cmd = command_calls[1]
                    sleep_cmd = sleep_calls[0] if sleep_calls else None

                    # Check that first command contains echo, second contains Enter
                    correct_order = (
                        not first_cmd['is_enter'] and
                        second_cmd['is_enter'] and
                        sleep_cmd and sleep_cmd['duration'] == 0.1
                    )

                    result = {
                        'test': 'tmux_command_sequence',
                        'success': correct_order,
                        'details': f"Commands: {len(command_calls)}, Sleep calls: {len(sleep_calls)}",
                        'sequence': 'echo -> sleep -> Enter' if correct_order else 'incorrect sequence'
                    }
                else:
                    result = {
                        'test': 'tmux_command_sequence',
                        'success': False,
                        'details': f"Unexpected command count: {len(command_calls)} commands, {len(sleep_calls)} sleeps",
                        'sequence': 'malformed'
                    }

                self.test_results.append(result)
                print(f"✅ Command sequence: {result['sequence']}")
                return result['success']

    def test_race_condition_prevention(self):
        """Test that delay prevents race conditions"""
        print("🔧 Testing race condition prevention...")

        # Simulate rapid message sending
        messages = [
            AgentMessage(
                message_id=f"race_test_{i}",
                sender_id="race-tester",
                recipient_id="backend-api",
                content=f"Race condition test message {i}",
                subject=f"Race Test {i}",
                priority=MessagePriority.NORMAL
            ) for i in range(3)
        ]

        all_timings = []

        def track_all_calls(*args, **kwargs):
            all_timings.append(('subprocess', time.time()))
            return MagicMock()

        def track_all_sleeps(duration):
            all_timings.append(('sleep', time.time(), duration))

        with patch('messaging.interface.subprocess.run', side_effect=track_all_calls):
            with patch('time.sleep', side_effect=track_all_sleeps):

                start_time = time.time()
                for msg in messages:
                    self.interface.send_terminal_notification("backend-api", msg)

                # Analyze timing patterns
                sleep_count = len([t for t in all_timings if t[0] == 'sleep'])
                subprocess_count = len([t for t in all_timings if t[0] == 'subprocess'])

                # Should have 3 sleep calls (one per message) and 6 subprocess calls (2 per message)
                expected_sleeps = len(messages)
                expected_subprocesses = len(messages) * 2

                race_prevention_success = (
                    sleep_count == expected_sleeps and
                    subprocess_count == expected_subprocesses
                )

                result = {
                    'test': 'race_condition_prevention',
                    'success': race_prevention_success,
                    'details': f"Messages: {len(messages)}, Sleep calls: {sleep_count}, Subprocess calls: {subprocess_count}",
                    'expected': f"Sleeps: {expected_sleeps}, Subprocesses: {expected_subprocesses}",
                    'actual': f"Sleeps: {sleep_count}, Subprocesses: {subprocess_count}"
                }

                self.test_results.append(result)
                print(f"✅ Race prevention: {result['details']}")
                return result['success']

    def test_delay_configuration(self):
        """Test delay configuration and consistency"""
        print("🔧 Testing delay configuration...")

        # Test multiple calls to ensure consistent delay
        delays_observed = []

        def capture_delay(duration):
            delays_observed.append(duration)

        test_message = AgentMessage(
            message_id="config_test",
            sender_id="config-tester",
            recipient_id="backend-api",
            content="Delay configuration test"
        )

        with patch('messaging.interface.subprocess.run'):
            with patch('time.sleep', side_effect=capture_delay):

                # Send multiple notifications
                for i in range(5):
                    self.interface.send_terminal_notification("backend-api", test_message)

                # Check consistency
                all_delays_same = all(delay == 0.1 for delay in delays_observed)
                expected_count = len(delays_observed) == 5

                result = {
                    'test': 'delay_configuration',
                    'success': all_delays_same and expected_count,
                    'details': f"Delays observed: {delays_observed}",
                    'consistency': 'consistent' if all_delays_same else 'inconsistent',
                    'count': len(delays_observed)
                }

                self.test_results.append(result)
                print(f"✅ Delay config: {result['consistency']}, Count: {result['count']}")
                return result['success']

    def test_error_handling_with_delay(self):
        """Test error handling doesn't break delay logic"""
        print("🔧 Testing error handling with delay...")

        test_message = AgentMessage(
            message_id="error_test",
            sender_id="error-tester",
            recipient_id="backend-api",
            content="Error handling test"
        )

        sleep_called = []
        error_handled = False

        def failing_subprocess(*args, **kwargs):
            raise Exception("Simulated TMUX error")

        def track_sleep(duration):
            sleep_called.append(duration)

        with patch('messaging.interface.subprocess.run', side_effect=failing_subprocess):
            with patch('time.sleep', side_effect=track_sleep):

                try:
                    self.interface.send_terminal_notification("backend-api", test_message)
                    error_handled = True
                except Exception:
                    error_handled = False

                result = {
                    'test': 'error_handling_with_delay',
                    'success': error_handled,
                    'details': f"Error handled gracefully: {error_handled}",
                    'sleep_calls': len(sleep_called)
                }

                self.test_results.append(result)
                print(f"✅ Error handling: {'graceful' if error_handled else 'failed'}")
                return result['success']

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("🔧 TMUX DELAY IMPLEMENTATION TEST REPORT")
        print("="*60)

        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)

        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        print("\n📋 Detailed Results:")

        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {status} - {result['test']}")
            print(f"      Details: {result['details']}")
            if 'expected' in result and 'actual' in result:
                print(f"      Expected: {result['expected']}")
                print(f"      Actual: {result['actual']}")
            print()

        print("🎯 Key Findings:")
        print("   • Delay timing: 0.1 seconds (100ms)")
        print("   • Implementation: time.sleep() between TMUX commands")
        print("   • Location: messaging/interface.py:468")
        print("   • Purpose: Prevent race conditions in terminal notification delivery")

        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! TMUX delay implementation is working correctly.")
            return True
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review implementation.")
            return False

    def run_all_tests(self):
        """Run all TMUX delay tests"""
        print("🚀 Starting TMUX Delay Implementation Tests")
        print("="*60)

        tests = [
            self.test_delay_timing_precision,
            self.test_tmux_command_sequence,
            self.test_race_condition_prevention,
            self.test_delay_configuration,
            self.test_error_handling_with_delay
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with error: {e}")
                self.test_results.append({
                    'test': test.__name__,
                    'success': False,
                    'details': f"Test error: {e}"
                })

        return self.generate_report()


def main():
    """Main test execution"""
    tester = TMUXDelayTester()
    success = tester.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)