#!/usr/bin/env python3
"""
Remove remaining riona-ai references from instruction files
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import INSTRUCTIONS_DIR, PROJECT_ROOT

def clean_instruction_file(file_path: Path):
    """Remove riona-ai references from instruction file"""
    print(f"Cleaning {file_path.name}...")

    content = file_path.read_text()
    original = content

    # Replace all riona-ai paths with PROJECT_ROOT
    replacements = [
        (f"{PROJECT_ROOT}/riona-ai/backend", str(PROJECT_ROOT)),
        (f"{PROJECT_ROOT}/riona-ai/frontend", str(PROJECT_ROOT)),
        (f"{PROJECT_ROOT}/riona-ai", str(PROJECT_ROOT)),
        ("/.claude-agents/agents/configs/", "/instructions/"),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    if content != original:
        file_path.write_text(content)
        print(f"  ✅ Cleaned {file_path.name}")
        return True
    else:
        print(f"  ⏭️ No riona-ai references in {file_path.name}")
        return False

def main():
    """Clean all instruction files"""
    print("🧹 Cleaning riona-ai References from Instructions")
    print("=" * 50)

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

    cleaned = 0
    for file_path in instruction_files:
        if clean_instruction_file(file_path):
            cleaned += 1

    print()
    print(f"✅ Cleaned {cleaned}/{len(instruction_files)} files")

if __name__ == "__main__":
    main()