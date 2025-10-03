#!/usr/bin/env python3
"""
Analyze Prompt Experiment Results

Usage:
    python scripts/analyze_experiments.py logs/prompt-experiments/suite_20251003_151530.json
    python scripts/analyze_experiments.py --list  # List all experiments
    python scripts/analyze_experiments.py --compare suite1.json suite2.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def load_suite(suite_file: Path) -> Dict:
    """Load suite summary."""
    with open(suite_file) as f:
        return json.load(f)


def print_suite_summary(suite: Dict):
    """Print suite summary."""
    print(f"\n{'='*80}")
    print(f"Suite: {suite['suite_name']}")
    print(f"Session: {suite['session_id']}")
    print(f"{'='*80}")
    print(f"Project: {suite['project']}")
    print(f"Baseline: {suite['baseline_commit'][:8]}")
    print(f"Experiments: {suite['experiments_run']}")
    print(f"Timestamp: {suite['timestamp']}")
    print()


def print_experiment_table(experiments: List[Dict]):
    """Print experiments in table format."""
    print(f"{'Name':<30} {'Success':<10} {'Duration':<12} {'Files':<8} {'Lines':<8} {'Commit':<10}")
    print(f"{'-'*30} {'-'*10} {'-'*12} {'-'*8} {'-'*8} {'-'*10}")

    for exp in experiments:
        name = exp['prompt_name']
        success = "✅" if exp['success'] else "❌"
        duration = f"{exp['duration']:.1f}s"
        files = exp.get('metrics', {}).get('files_changed', 0)
        lines = exp.get('metrics', {}).get('lines_changed', 0)
        commit = exp.get('git_commit_sha', 'none')[:8] if exp.get('git_commit_sha') else 'none'

        print(f"{name:<30} {success:<10} {duration:>10}  {files:>6}  {lines:>6}  {commit:<10}")


def print_comparison(comparison: Dict):
    """Print comparison details."""
    if not comparison:
        return

    print(f"\n{'='*80}")
    print("COMPARISON ANALYSIS")
    print(f"{'='*80}\n")

    print(f"Baseline: {comparison['baseline_id'].split('_')[-1]}")
    print(f"Variants: {len(comparison['variants'])}")

    if comparison.get('winner'):
        print(f"\n🏆 Winner: {comparison['winner']}")
        print(f"   {comparison['winner_reason']}")

    print(f"\n{'Variant':<30} {'Duration Δ':<15} {'Files Δ':<10} {'Lines Δ':<10}")
    print(f"{'-'*30} {'-'*15} {'-'*10} {'-'*10}")

    metrics_comp = comparison.get('metrics_comparison', {})
    for variant_name, comp in metrics_comp.items():
        duration_diff = comp.get('duration_diff', 0)
        duration_sign = '+' if duration_diff > 0 else ''

        files_diff = comp.get('metrics', {}).get('files_changed_diff', 0)
        files_sign = '+' if files_diff > 0 else ''

        lines_diff = comp.get('metrics', {}).get('lines_changed_diff', 0)
        lines_sign = '+' if lines_diff > 0 else ''

        print(f"{variant_name:<30} {duration_sign}{duration_diff:>6.1f}s       "
              f"{files_sign}{files_diff:>5}     {lines_sign}{lines_diff:>5}")


def analyze_prompt_effectiveness(experiments: List[Dict]):
    """Analyze prompt effectiveness patterns."""
    print(f"\n{'='*80}")
    print("PROMPT EFFECTIVENESS ANALYSIS")
    print(f"{'='*80}\n")

    successful = [e for e in experiments if e['success']]
    failed = [e for e in experiments if not e['success']]

    print(f"Success Rate: {len(successful)}/{len(experiments)} ({len(successful)/len(experiments)*100:.1f}%)")

    if successful:
        avg_duration = sum(e['duration'] for e in successful) / len(successful)
        min_duration = min(e['duration'] for e in successful)
        max_duration = max(e['duration'] for e in successful)

        print(f"\nSuccessful Experiments:")
        print(f"  Average duration: {avg_duration:.1f}s")
        print(f"  Range: {min_duration:.1f}s - {max_duration:.1f}s")

        fastest = min(successful, key=lambda e: e['duration'])
        print(f"  Fastest: {fastest['prompt_name']} ({fastest['duration']:.1f}s)")

        if any(e.get('metrics', {}).get('files_changed') for e in successful):
            avg_files = sum(e.get('metrics', {}).get('files_changed', 0) for e in successful) / len(successful)
            avg_lines = sum(e.get('metrics', {}).get('lines_changed', 0) for e in successful) / len(successful)
            print(f"  Average changes: {avg_files:.1f} files, {avg_lines:.1f} lines")

    if failed:
        print(f"\nFailed Experiments: {len(failed)}")
        for exp in failed:
            error = exp.get('error', 'Unknown error')
            print(f"  - {exp['prompt_name']}: {error}")


def print_prompt_details(experiment: Dict):
    """Print detailed prompt information."""
    print(f"\n{'='*80}")
    print(f"PROMPT DETAILS: {experiment['prompt_name']}")
    print(f"{'='*80}\n")

    print(f"Success: {'✅ Yes' if experiment['success'] else '❌ No'}")
    print(f"Duration: {experiment['duration']:.1f}s")
    print(f"Timestamp: {experiment['timestamp']}")

    if experiment.get('git_commit_sha'):
        print(f"Commit: {experiment['git_commit_sha']}")
        if experiment.get('git_diff_stats'):
            stats = experiment['git_diff_stats']
            print(f"Changes: {stats.get('files_changed', 0)} files, "
                  f"+{stats.get('insertions', 0)}/-{stats.get('deletions', 0)} lines")

    print(f"\n--- PROMPT TEXT ---")
    print(experiment['prompt_text'])
    print(f"--- END PROMPT ---\n")

    if experiment.get('error'):
        print(f"Error: {experiment['error']}")


def list_all_experiments(log_dir: Path):
    """List all experiment suites."""
    suites = sorted(log_dir.glob('suite_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)

    if not suites:
        print("No experiment suites found")
        return

    print(f"\n{'='*80}")
    print("EXPERIMENT SUITES")
    print(f"{'='*80}\n")

    print(f"{'Session ID':<20} {'Suite Name':<30} {'Experiments':<12} {'Date':<20}")
    print(f"{'-'*20} {'-'*30} {'-'*12} {'-'*20}")

    for suite_file in suites:
        suite = load_suite(suite_file)
        session_id = suite['session_id']
        name = suite['suite_name'][:28]
        exp_count = suite['experiments_run']
        timestamp = datetime.fromisoformat(suite['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

        print(f"{session_id:<20} {name:<30} {exp_count:^12} {timestamp:<20}")

    print(f"\nTotal: {len(suites)} suites")
    print(f"\nTo analyze: python scripts/analyze_experiments.py logs/prompt-experiments/suite_[SESSION_ID].json")


def compare_suites(suite1_file: Path, suite2_file: Path):
    """Compare two experiment suites."""
    suite1 = load_suite(suite1_file)
    suite2 = load_suite(suite2_file)

    print(f"\n{'='*80}")
    print("SUITE COMPARISON")
    print(f"{'='*80}\n")

    print(f"Suite 1: {suite1['suite_name']} ({suite1['session_id']})")
    print(f"Suite 2: {suite2['suite_name']} ({suite2['session_id']})")
    print()

    # Compare common prompts
    suite1_prompts = {e['prompt_name']: e for e in suite1['experiments']}
    suite2_prompts = {e['prompt_name']: e for e in suite2['experiments']}

    common_prompts = set(suite1_prompts.keys()) & set(suite2_prompts.keys())

    if common_prompts:
        print(f"Common Prompts: {len(common_prompts)}\n")
        print(f"{'Prompt':<30} {'Suite 1 Duration':<20} {'Suite 2 Duration':<20} {'Difference':<15}")
        print(f"{'-'*30} {'-'*20} {'-'*20} {'-'*15}")

        for prompt_name in sorted(common_prompts):
            exp1 = suite1_prompts[prompt_name]
            exp2 = suite2_prompts[prompt_name]

            dur1 = exp1['duration']
            dur2 = exp2['duration']
            diff = dur2 - dur1
            diff_pct = (diff / dur1 * 100) if dur1 > 0 else 0

            print(f"{prompt_name:<30} {dur1:>10.1f}s         {dur2:>10.1f}s         "
                  f"{diff:+6.1f}s ({diff_pct:+.1f}%)")
    else:
        print("No common prompts found between suites")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/analyze_experiments.py <suite.json>")
        print("  python scripts/analyze_experiments.py --list")
        print("  python scripts/analyze_experiments.py --compare suite1.json suite2.json")
        print("  python scripts/analyze_experiments.py --prompt <suite.json> <prompt_name>")
        sys.exit(1)

    log_dir = Path('logs/prompt-experiments')

    if sys.argv[1] == '--list':
        list_all_experiments(log_dir)
        return

    if sys.argv[1] == '--compare':
        if len(sys.argv) < 4:
            print("Error: --compare requires 2 suite files")
            sys.exit(1)
        compare_suites(Path(sys.argv[2]), Path(sys.argv[3]))
        return

    suite_file = Path(sys.argv[1])
    if not suite_file.exists():
        print(f"Error: Suite file not found: {suite_file}")
        sys.exit(1)

    suite = load_suite(suite_file)

    print_suite_summary(suite)
    print_experiment_table(suite['experiments'])

    if suite.get('comparison'):
        print_comparison(suite['comparison'])

    analyze_prompt_effectiveness(suite['experiments'])

    # If --prompt flag, show prompt details
    if len(sys.argv) > 2 and sys.argv[2] == '--prompt':
        if len(sys.argv) < 4:
            print("\nAvailable prompts:")
            for exp in suite['experiments']:
                print(f"  - {exp['prompt_name']}")
        else:
            prompt_name = sys.argv[3]
            exp = next((e for e in suite['experiments'] if e['prompt_name'] == prompt_name), None)
            if exp:
                print_prompt_details(exp)
            else:
                print(f"Error: Prompt not found: {prompt_name}")


if __name__ == '__main__':
    main()
