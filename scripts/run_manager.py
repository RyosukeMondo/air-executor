#!/usr/bin/env python3
"""
Simple script to run Air-Executor job manager in foreground.
Use this for development and testing.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from air_executor.manager.config import Config
from air_executor.manager.poller import JobPoller
from air_executor.manager.spawner import RunnerSpawner
from air_executor.runners.subprocess_runner import SubprocessRunner
from air_executor.storage.file_store import FileStore

def main():
    print("🚀 Air-Executor Job Manager")
    print("=" * 60)

    # Load config
    config = Config.load_or_default()

    print(f"📊 Configuration:")
    print(f"   Poll interval: {config.poll_interval}s")
    print(f"   Task timeout: {config.task_timeout}s")
    print(f"   Max concurrent runners: {config.max_concurrent_runners}")
    print(f"   Base path: {config.base_path}")
    print()

    # Initialize components
    print("🔧 Initializing components...")
    store = FileStore(config.base_path)
    runner = SubprocessRunner(config.task_timeout)
    spawner = RunnerSpawner(store, runner, config.max_concurrent_runners)
    poller = JobPoller(store, spawner, config)

    print("✅ Components initialized")
    print()
    print("🎮 Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Start polling (blocks until Ctrl+C)
    try:
        poller.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutdown requested...")
        poller.stop()
        print("✅ Air-Executor stopped cleanly")
        return 0
    except Exception as e:
        print(f"\n\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
