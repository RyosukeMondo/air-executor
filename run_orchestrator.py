#!/usr/bin/env python3
"""
Simple runner script for multi-language orchestrator.
Properly sets up Python path and imports.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import from the package (noqa for path setup)
from airflow_dags.autonomous_fixing.cli import OrchestratorCLI  # noqa: E402


def main():
    """Load config and run orchestrator using CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: python run_orchestrator.py <config.yaml>")
        print("\nExample:")
        print("  python run_orchestrator.py sample_config.yaml")
        sys.exit(1)

    config_path = Path(sys.argv[1])

    # Validate config file exists
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    # Run orchestrator using CLI interface
    try:
        result = OrchestratorCLI.run_from_yaml(config_path)
    except Exception as e:
        print(f"❌ Error running orchestrator: {e}")
        sys.exit(1)

    # Print result summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Success: {result.success}")
    print(f"Exit Code: {result.exit_code}")
    print(f"Iterations Completed: {result.iterations_completed}")
    print(f"Final Health Score: {result.final_health_score:.2f}")
    print(f"Duration: {result.duration_seconds:.2f}s")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    print("=" * 80)

    # Exit with result's exit code
    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
