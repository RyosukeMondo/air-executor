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
from airflow_dags.autonomous_fixing.config import OrchestratorConfig  # noqa: E402
from airflow_dags.autonomous_fixing.multi_language_orchestrator import (  # noqa: E402
    MultiLanguageOrchestrator,
)


def main():
    """Load config and run orchestrator."""
    if len(sys.argv) < 2:
        print("Usage: python run_orchestrator.py <config.yaml>")
        print("\nExample:")
        print("  python run_orchestrator.py sample_config.yaml")
        sys.exit(1)

    config_path = Path(sys.argv[1])

    # Load configuration using new OrchestratorConfig
    try:
        config = OrchestratorConfig.from_yaml(config_path)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config file: {e}")
        sys.exit(1)

    # Run orchestrator
    orchestrator = MultiLanguageOrchestrator(config)
    result = orchestrator.execute()

    # Print result summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Success: {result.get('success', False)}")
    if "error" in result:
        print(f"Error: {result['error']}")
    print("=" * 80)

    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
