#!/usr/bin/env python3
"""
Gradual testing script for autonomous fixing.
Start with 1 error, then gradually increase scope.
"""

import sys
from pathlib import Path
from datetime import datetime

from state_manager import StateManager, Task, generate_task_id
from executor_runner import AirExecutorRunner


def create_test_task() -> Task:
    """Create a single simple test task"""
    # Example: Fix missing @riverpod annotation resolution
    return Task(
        id=generate_task_id(),
        type="fix_build_error",
        priority=1,
        phase="build",
        file="lib/core/injection/injection.dart",
        line=None,
        message="Injectable dependencies not registered properly",
        context="""
The following types need @injectable annotation or module registration:

1. HiveInterface from package:hive - external package
2. FirebaseAnalytics from package:firebase_analytics - external package
3. AssetBundle from package:flutter - external package
4. InAppPurchase from package:in_app_purchase - external package

These need to be registered in a @module class for dependency injection.

Example fix:
```dart
@module
abstract class ExternalDependenciesModule {
  @preResolve
  Future<HiveInterface> get hive => Hive;

  @injectable
  FirebaseAnalytics get analytics => FirebaseAnalytics.instance;

  // ... etc
}
```
""",
        created_at=datetime.now().isoformat()
    )


def test_single_fix(simulation: bool = True):
    """Test fixing a single error"""
    print("🧪 Gradual Test: Single Error Fix")
    print("=" * 60)

    # Setup
    state_mgr = StateManager()
    task = create_test_task()

    print(f"\n📝 Test task:")
    print(f"  Type: {task.type}")
    print(f"  File: {task.file}")
    print(f"  Issue: {task.message}")

    if simulation:
        print("\n🎭 SIMULATION MODE - No actual changes")
        print(f"\nPrompt that would be sent to air-executor:")
        print("-" * 60)
        print(task.context[:500] + "...")
        print("-" * 60)
        return

    # Queue and execute
    print("\n📋 Queuing task...")
    state_mgr.queue_task(task)

    print("🚀 Executing via air-executor...")
    executor = AirExecutorRunner(
        wrapper_path="/home/rmondo/repos/air-executor/scripts/claude_wrapper.py",
        working_dir="/home/rmondo/repos/money-making-app",
        timeout=300,
        auto_commit=True
    )

    result = executor.run_task(task)

    print("\n📊 Result:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration:.1f}s")

    if result.success:
        print("\n✅ Task completed successfully!")
        state_mgr.mark_task_complete(task.id)
    else:
        print("\n❌ Task failed")
        print(f"  Error: {result.stderr[:200]}")
        state_mgr.mark_task_failed(task.id, result.stderr)


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python gradual_test.py [simulation|live]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "simulation":
        test_single_fix(simulation=True)
    elif mode == "live":
        print("⚠️ WARNING: This will make REAL code changes and commits!")
        response = input("Continue? (yes/no): ")
        if response.lower() == "yes":
            test_single_fix(simulation=False)
        else:
            print("Cancelled.")
    else:
        print(f"Unknown mode: {mode}")
        print("Use 'simulation' or 'live'")
        sys.exit(1)


if __name__ == "__main__":
    main()
