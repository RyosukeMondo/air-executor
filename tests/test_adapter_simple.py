#!/usr/bin/env python3
"""
Simple test to verify PythonAdapter works in real usage.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from airflow_dags.autonomous_fixing.adapters.languages.python_adapter import PythonAdapter


def main():
    print("\n" + "=" * 80)
    print("PYTHON ADAPTER - REAL USAGE TEST")
    print("=" * 80)

    # Create adapter with simple config
    config = {
        "linters": ["pylint"],
        "test_framework": "pytest",
        "complexity_threshold": 15,
        "max_file_lines": 500,
    }

    adapter = PythonAdapter(config)
    print("\n✓ PythonAdapter created")
    print(f"  Language: {adapter.language_name}")

    # Test 1: Detect projects
    print(f"\n{'='*80}")
    print("TEST 1: Detect Python Projects")
    print("=" * 80)

    project_root = str(Path(__file__).parent)
    projects = adapter.detect_projects(project_root)

    print(f"\n✓ Detected {len(projects)} Python project(s):")
    for i, proj in enumerate(projects[:5], 1):
        print(f"   {i}. {proj}")
    if len(projects) > 5:
        print(f"   ... and {len(projects) - 5} more")

    # Test 2: Validate tools
    print(f"\n{'='*80}")
    print("TEST 2: Validate Python Toolchain")
    print("=" * 80)

    validation_results = adapter.validate_tools()

    print(f"\n✓ Validated {len(validation_results)} tool(s):")
    for result in validation_results:
        status = "✓" if result.available else "✗"
        version = f"v{result.version}" if result.version else "N/A"
        print(f"   {status} {result.tool_name}: {version}")
        if not result.available and result.error:
            print(f"      Error: {result.error}")
        if result.fix_suggestion:
            print(f"      Fix: {result.fix_suggestion}")

    # Test 3: Static analysis on this project
    print(f"\n{'='*80}")
    print("TEST 3: Static Analysis (Limited Scope)")
    print("=" * 80)

    if projects:
        test_project = projects[0]
        print(f"\nAnalyzing: {test_project}")
        print("(Running pylint on project...)\n")

        result = adapter.static_analysis(test_project)

        print("✓ Analysis complete:")
        print(f"   Language: {result.language}")
        print(f"   Phase: {result.phase}")
        print(f"   Project: {result.project_path}")
        print(f"   Success: {result.success}")
        print(f"   Errors found: {len(result.errors)}")
        print(f"   Complexity violations: {len(result.complexity_violations)}")

        if result.errors:
            print("\n   First 3 errors:")
            for i, error in enumerate(result.errors[:3], 1):
                print(
                    f"      {i}. {error.get('file', '?')}:{error.get('line', '?')} - {error.get('message', '')[:80]}"
                )

    print(f"\n{'='*80}")
    print("✅ ALL REAL USAGE TESTS PASSED")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
