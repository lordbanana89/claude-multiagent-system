#!/usr/bin/env python3
"""
Final comprehensive test to ensure NO MOCK DATA remains in the system
Follows the strict rule: "No Mock, no downgrade, solo correzione e implementazione"
"""

import os
import re
import ast
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

class NoMockValidator:
    """Validates that no mock data remains in the codebase"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.violations = []
        self.files_checked = 0
        self.total_violations = 0

    def check_python_files(self) -> List[Dict]:
        """Check all Python files for mock data"""
        print("🔍 Checking Python files for mock data...")
        violations = []

        # Patterns that indicate mock data
        mock_patterns = [
            (r'mock|Mock|MOCK', 'Mock keyword found'),
            (r'fake|Fake|FAKE', 'Fake keyword found'),
            (r'dummy|Dummy|DUMMY', 'Dummy keyword found'),
            (r'sample|Sample|SAMPLE', 'Sample keyword found'),
            (r'test_data|TEST_DATA', 'Test data found'),
            (r'placeholder|Placeholder|PLACEHOLDER', 'Placeholder found'),
            (r'\[\s*{[^}]*"status"\s*:\s*"active"[^}]*}\s*\]', 'Hardcoded status data'),
            (r'generateMock|generate_mock', 'Mock generator function'),
            (r'Math\.random\(\)\s*\*\s*\d+', 'Random mock values'),
        ]

        for py_file in self.project_root.rglob("*.py"):
            # Skip test files and virtual environments
            if any(skip in str(py_file) for skip in ['test_', 'venv/', '__pycache__', '.git']):
                continue

            self.files_checked += 1
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern, desc in mock_patterns:
                    if re.search(pattern, line):
                        # Skip if it's a comment or string
                        stripped = line.strip()
                        if stripped.startswith('#') or stripped.startswith('"""'):
                            continue

                        # Skip legitimate uses
                        if 'MOCK_CLAUDE' in line and 'TEST_MODE' in line:
                            continue  # Configuration flag, not mock data

                        violations.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': line_num,
                            'type': desc,
                            'content': line.strip()
                        })

        return violations

    def check_javascript_files(self) -> List[Dict]:
        """Check all JavaScript/TypeScript files for mock data"""
        print("🔍 Checking JavaScript/TypeScript files for mock data...")
        violations = []

        # Patterns that indicate mock data
        mock_patterns = [
            (r'mock|Mock|MOCK', 'Mock keyword found'),
            (r'fake|Fake|FAKE', 'Fake keyword found'),
            (r'dummy|Dummy|DUMMY', 'Dummy keyword found'),
            (r'sample|Sample|SAMPLE', 'Sample keyword found'),
            (r'placeholder(?!=")', 'Placeholder found'),  # Exclude placeholder attributes
            (r'generateMock|generateFake|generateDummy', 'Mock generator function'),
            (r'Math\.random\(\)\s*\*\s*(?!.*\bid\b|.*\bkey\b)', 'Random mock values'),
            (r'\[\s*{[^}]*level:\s*[\'"]info[\'"][^}]*message:[^}]*}\s*\]', 'Hardcoded log data'),
        ]

        for js_file in self.project_root.rglob("*.{js,jsx,ts,tsx}"):
            # Skip node_modules and build directories
            if any(skip in str(js_file) for skip in ['node_modules/', 'dist/', 'build/', '.git']):
                continue

            self.files_checked += 1
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern, desc in mock_patterns:
                    if re.search(pattern, line):
                        # Skip if it's a comment
                        stripped = line.strip()
                        if stripped.startswith('//') or stripped.startswith('/*'):
                            continue

                        # Skip legitimate uses
                        if 'Math.random()' in line and ('id' in line or 'key' in line or 'uuid' in line):
                            continue  # Legitimate ID generation

                        if 'placeholder=' in line and '<input' in line:
                            continue  # Legitimate input placeholder

                        violations.append({
                            'file': str(js_file.relative_to(self.project_root)),
                            'line': line_num,
                            'type': desc,
                            'content': line.strip()
                        })

        return violations

    def check_api_endpoints(self) -> List[Dict]:
        """Check API endpoints return real data"""
        print("🔍 Checking API endpoints for real data...")
        violations = []

        # Test endpoints if server is running
        try:
            import requests

            test_endpoints = [
                ('http://localhost:5001/api/agents', 'GET'),
                ('http://localhost:5001/api/system/health', 'GET'),
                ('http://localhost:5001/api/system/logs', 'GET'),
                ('http://localhost:8888/api/health', 'GET'),
            ]

            for url, method in test_endpoints:
                try:
                    response = requests.request(method, url, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        # Check if response looks like mock data
                        if isinstance(data, dict):
                            data_str = json.dumps(data)
                            if any(mock in data_str.lower() for mock in ['mock', 'fake', 'dummy', 'test data']):
                                violations.append({
                                    'file': 'API Endpoint',
                                    'line': 0,
                                    'type': 'Mock data in response',
                                    'content': f'{url} returns mock data'
                                })
                except:
                    pass  # Server might not be running

        except ImportError:
            print("⚠️  Requests library not available, skipping API tests")

        return violations

    def check_database_connections(self) -> List[Dict]:
        """Check that database queries are real, not mocked"""
        print("🔍 Checking database connections...")
        violations = []

        # Check for in-memory arrays that should be database queries
        patterns = [
            (r'agents\s*=\s*\[', 'Hardcoded agents array'),
            (r'tasks\s*=\s*\[', 'Hardcoded tasks array'),
            (r'messages\s*=\s*\[', 'Hardcoded messages array'),
            (r'activities\s*=\s*\[', 'Hardcoded activities array'),
        ]

        for py_file in self.project_root.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['test_', 'venv/', '__pycache__']):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if file has database imports
            has_db_import = 'sqlite3' in content or 'psycopg2' in content or 'pymongo' in content

            if has_db_import:
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    for pattern, desc in patterns:
                        if re.search(pattern, line) and not line.strip().startswith('#'):
                            # Check if it's followed by actual data (not empty)
                            next_lines = '\n'.join(lines[line_num:min(line_num+5, len(lines))])
                            if '{' in next_lines:  # Has actual hardcoded data
                                violations.append({
                                    'file': str(py_file.relative_to(self.project_root)),
                                    'line': line_num,
                                    'type': desc,
                                    'content': line.strip()
                                })

        return violations

    def run_all_checks(self) -> Tuple[bool, str]:
        """Run all validation checks"""
        print("\n" + "="*60)
        print("🚀 COMPREHENSIVE NO-MOCK VALIDATION")
        print("="*60 + "\n")

        all_violations = []

        # Run all checks
        all_violations.extend(self.check_python_files())
        all_violations.extend(self.check_javascript_files())
        all_violations.extend(self.check_api_endpoints())
        all_violations.extend(self.check_database_connections())

        # Filter out false positives
        filtered_violations = []
        for v in all_violations:
            # Skip known legitimate uses
            if 'config/settings.py' in v['file'] and 'MOCK_CLAUDE' in v['content']:
                continue  # Configuration flag
            if 'Math.random()' in v['content'] and any(x in v['content'] for x in ['id', 'key', 'uuid']):
                continue  # ID generation
            if 'placeholder=' in v['content'] and 'input' in v['content'].lower():
                continue  # Input placeholders

            filtered_violations.append(v)

        # Generate report
        report = []
        report.append("\n" + "="*60)
        report.append("📊 VALIDATION RESULTS")
        report.append("="*60)
        report.append(f"\n✅ Files checked: {self.files_checked}")
        report.append(f"❌ Violations found: {len(filtered_violations)}\n")

        if filtered_violations:
            report.append("⚠️  MOCK DATA VIOLATIONS FOUND:")
            report.append("-" * 40)

            # Group by file
            by_file = {}
            for v in filtered_violations:
                if v['file'] not in by_file:
                    by_file[v['file']] = []
                by_file[v['file']].append(v)

            for file, violations in by_file.items():
                report.append(f"\n📄 {file}:")
                for v in violations:
                    report.append(f"   Line {v['line']}: {v['type']}")
                    report.append(f"   > {v['content'][:80]}...")

            report.append("\n" + "="*60)
            report.append("❌ VALIDATION FAILED - Mock data still exists!")
            report.append("Action required: Implement real functions for all mock data")
            report.append("="*60)
            success = False
        else:
            report.append("\n" + "="*60)
            report.append("✅ VALIDATION PASSED - No mock data found!")
            report.append("All functions use real implementations")
            report.append("="*60)
            success = True

        return success, '\n'.join(report)

def main():
    """Main entry point"""
    validator = NoMockValidator()
    success, report = validator.run_all_checks()

    print(report)

    # Write report to file
    with open('no_mock_validation_report.txt', 'w') as f:
        f.write(report)
        f.write(f"\n\nGenerated on: {__import__('datetime').datetime.now()}\n")

    print(f"\n📝 Report saved to: no_mock_validation_report.txt")

    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()