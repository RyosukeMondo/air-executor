#!/usr/bin/env python3
"""
Claude Wrapper History Viewer - Inspect wrapper calls easily.

Usage:
  ./scripts/claude_wrapper_history.sh                    # Show last 10 calls
  ./scripts/claude_wrapper_history.sh 20                 # Show last 20 calls
  ./scripts/claude_wrapper_history.sh --failures         # Show recent failures
  ./scripts/claude_wrapper_history.sh --successes        # Show recent successes
  ./scripts/claude_wrapper_history.sh --verbose          # Show full prompts
  ./scripts/claude_wrapper_history.sh --project PATH     # Filter by project
  ./scripts/claude_wrapper_history.sh --type TYPE        # Filter by prompt type
  ./scripts/claude_wrapper_history.sh --clean            # Clean up old logs
"""

import sys
import argparse
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from airflow_dags.autonomous_fixing.adapters.ai.wrapper_history import WrapperHistoryLogger

def main():
    parser = argparse.ArgumentParser(description="Inspect claude_wrapper call history")
    parser.add_argument('limit', nargs='?', type=int, default=10, help='Number of calls to show')
    parser.add_argument('--failures', action='store_true', help='Show only failures')
    parser.add_argument('--successes', action='store_true', help='Show only successes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show full prompts')
    parser.add_argument('--project', type=str, help='Filter by project path')
    parser.add_argument('--type', type=str, help='Filter by prompt type (fix_error, fix_test, analysis, etc.)')
    parser.add_argument('--clean', action='store_true', help='Clean up old logs (keeps last 7 days)')

    args = parser.parse_args()

    # Initialize logger
    logger = WrapperHistoryLogger()

    # Clean up mode
    if args.clean:
        print("🧹 Cleaning up old wrapper logs...")
        logger.cleanup_old_logs(keep_days=7)
        return

    # Get calls based on filters
    if args.failures:
        calls = logger.get_failures(args.limit)
        title = f"Last {args.limit} Failed Calls"
    elif args.successes:
        calls = logger.get_successes(args.limit)
        title = f"Last {args.limit} Successful Calls"
    elif args.project:
        calls = logger.get_calls_by_project(args.project, args.limit)
        title = f"Last {args.limit} Calls for {args.project}"
    elif args.type:
        calls = logger.get_calls_by_type(args.type, args.limit)
        title = f"Last {args.limit} {args.type} Calls"
    else:
        calls = logger.get_recent_calls(args.limit)
        title = f"Last {args.limit} Wrapper Calls"

    # Print header
    print("="*80)
    print(f"📊 {title}")
    print("="*80)

    if not calls:
        print("\nNo calls found in history.")
        print("\nTip: Wrapper calls are logged to: logs/wrapper-history/")
        return

    # Print each call
    for i, call in enumerate(calls, 1):
        print(f"\n[{i}/{len(calls)}]", end='')
        logger.print_call_summary(call, verbose=args.verbose)

    # Print summary stats
    print("\n" + "="*80)
    print("📈 Summary")
    print("="*80)

    success_count = sum(1 for c in calls if c.get('success'))
    failure_count = len(calls) - success_count
    total_duration = sum(c.get('duration', 0) for c in calls)

    print(f"  Total calls: {len(calls)}")
    print(f"  ✅ Successes: {success_count} ({success_count / len(calls) * 100:.0f}%)")
    print(f"  ❌ Failures: {failure_count} ({failure_count / len(calls) * 100:.0f}%)")
    print(f"  ⏱️  Total time: {total_duration:.1f}s")
    if calls:
        print(f"  ⏱️  Average: {total_duration / len(calls):.1f}s per call")

    # Git commit stats
    commits_created = sum(1 for c in calls if c.get('git', {}).get('commit_created'))
    if commits_created > 0:
        print(f"  ✅ Git commits: {commits_created}/{len(calls)}")

    # Most common errors
    errors = {}
    for call in calls:
        if not call.get('success'):
            error = call.get('error', 'Unknown error')
            # Truncate error to first line for grouping
            error_key = error.split('\n')[0][:80]
            errors[error_key] = errors.get(error_key, 0) + 1

    if errors:
        print(f"\n  Common errors:")
        for error, count in sorted(errors.items(), key=lambda x: -x[1])[:3]:
            print(f"    - {error} ({count}x)")

    print("="*80)

    # Show tips based on results
    if failure_count > success_count:
        print("\n💡 High failure rate detected!")
        print("   Try: ./scripts/claude_wrapper_history.sh --failures --verbose")
        print("   To see full prompts and investigate issues.")

if __name__ == "__main__":
    main()
