#!/usr/bin/env python3
"""Simplest possible test of task execution"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tmux_client import TMUXClient

# Test sending commands with new markers
tmux = TMUXClient()
session = "test-simple"

# Clean start
if tmux.session_exists(session):
    tmux.kill_session(session)
tmux.create_session(session)

print("Created session")

# Send commands as they would be sent
tmux.send_command(session, "echo '### TASK_START:test-123'")
time.sleep(0.5)
tmux.send_command(session, "echo 'Executing task'")
time.sleep(0.5)
tmux.send_command(session, "echo '### TASK_END:test-123'")
time.sleep(1)

# Check output
output = tmux.capture_pane(session)
print("\nOutput:")
print("-" * 40)
print(output)
print("-" * 40)

# Check for markers
if "### TASK_START:test-123" in output:
    print("✅ START marker found")
else:
    print("❌ START marker NOT found")

if "### TASK_END:test-123" in output:
    print("✅ END marker found")
else:
    print("❌ END marker NOT found")

if "Executing task" in output:
    print("✅ Task content found")
else:
    print("❌ Task content NOT found")

# Cleanup
tmux.kill_session(session)