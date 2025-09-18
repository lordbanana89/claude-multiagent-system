#!/usr/bin/env python3
"""
Fix agent instruction files:
1. Replace Riona AI references with Claude Multi-Agent System
2. Update working directories to use PROJECT_ROOT
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import PROJECT_ROOT, INSTRUCTIONS_DIR

def fix_instruction_file(file_path: Path):
    """Fix a single instruction file"""
    print(f"Fixing {file_path.name}...")

    content = file_path.read_text()
    original = content

    # Replace Riona AI references
    replacements = [
        ("Riona AI - Instagram automation platform", "Claude Multi-Agent System"),
        ("Riona AI", "Claude Multi-Agent System"),
        ("riona_ai", "claude-multiagent-system"),
        ("/Users/erik/Desktop/riona_ai/riona-ai", str(PROJECT_ROOT)),
        ("/.riona/", "/.claude-agents/"),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    # Update the footer
    content = content.replace(
        "*Generated automatically from config:",
        "*Updated for Claude Multi-Agent System. Original from:"
    )

    if content != original:
        file_path.write_text(content)
        print(f"  ✅ Updated {file_path.name}")
        return True
    else:
        print(f"  ⏭️ No changes needed for {file_path.name}")
        return False

def main():
    """Fix all instruction files"""
    print("🔧 Fixing Agent Instructions")
    print("=" * 40)

    if not INSTRUCTIONS_DIR.exists():
        print(f"❌ Instructions directory not found: {INSTRUCTIONS_DIR}")
        return

    # Find all .md files
    instruction_files = list(INSTRUCTIONS_DIR.glob("*.md"))

    if not instruction_files:
        print(f"❌ No instruction files found in {INSTRUCTIONS_DIR}")
        return

    print(f"Found {len(instruction_files)} instruction files")
    print()

    updated = 0
    for file_path in instruction_files:
        if fix_instruction_file(file_path):
            updated += 1

    print()
    print(f"✅ Updated {updated}/{len(instruction_files)} files")

    # Create supervisor and master instructions if missing
    supervisor_file = INSTRUCTIONS_DIR / "supervisor.md"
    master_file = INSTRUCTIONS_DIR / "master.md"

    if not supervisor_file.exists():
        print("\n📝 Creating supervisor.md...")
        supervisor_content = """# Supervisor Agent Instructions

You are the **Supervisor Agent** for the Claude Multi-Agent System.

## Role
- Coordinate tasks between different agents
- Monitor system health and performance
- Ensure smooth communication between components
- Handle task prioritization and delegation

## Context
- **Project**: Claude Multi-Agent System
- **Working Directory**: """ + str(PROJECT_ROOT) + """

## Responsibilities
1. Task coordination and delegation
2. System monitoring and health checks
3. Inter-agent communication
4. Performance optimization
5. Error handling and recovery

## Available Agents
- backend-api: Backend development
- frontend-ui: Frontend development
- database: Database management
- testing: Testing and QA
- instagram: Social media integration
- queue-manager: Task queue management
- deployment: DevOps and deployment

## Commands
- Monitor system: `python monitoring/health.py`
- Check queues: `python -m task_queue.client stats`
- View logs: `tail -f logs/*.log`

*Created for Claude Multi-Agent System*
"""
        supervisor_file.write_text(supervisor_content)
        print("  ✅ Created supervisor.md")

    if not master_file.exists():
        print("📝 Creating master.md...")
        master_content = """# Master Agent Instructions

You are the **Master Agent** for the Claude Multi-Agent System.

## Role
- Supreme strategic oversight and crisis management
- System-wide coordination requiring highest authority
- Emergency response and critical decision making
- Long-term planning and vision setting

## Context
- **Project**: Claude Multi-Agent System
- **Working Directory**: """ + str(PROJECT_ROOT) + """

## Responsibilities
1. Crisis management and emergency response
2. Strategic planning and architecture decisions
3. Cross-functional coordination at highest level
4. Compliance and governance oversight
5. Performance optimization at enterprise level
6. Authoritative direction for other agents

## Authority Level
- Maximum system privileges
- Can override other agent decisions
- Direct access to all system components
- Emergency shutdown capabilities

## Critical Commands
- System status: `python monitoring/health.py --full`
- Emergency stop: `overmind kill`
- Full diagnostics: `python scripts/diagnose.py`
- Backup state: `python scripts/backup_state.py`

## Escalation Triggers
- System-wide outages
- Security breaches
- Data integrity issues
- Performance degradation > 50%
- Multi-agent coordination failures

*Created for Claude Multi-Agent System*
"""
        master_file.write_text(master_content)
        print("  ✅ Created master.md")

if __name__ == "__main__":
    main()