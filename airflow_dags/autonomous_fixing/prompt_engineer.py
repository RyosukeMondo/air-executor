"""
Prompt Engineering Mode - Systematic Prompt Testing and Refinement.

Usage:
    python prompt_engineer.py experiment.yaml

Features:
- Run multiple prompt variations on same project
- Compare results side-by-side
- Track metrics (success rate, duration, quality)
- Generate improvement suggestions
- Save all experiments for analysis
"""

import yaml
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Import core modules
try:
    from .core.claude_client import ClaudeClient
    from .core.git_verifier import GitVerifier
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from core.claude_client import ClaudeClient
    from core.git_verifier import GitVerifier


@dataclass
class PromptExperiment:
    """Single prompt experiment run."""
    experiment_id: str
    prompt_name: str
    prompt_text: str
    project_path: str
    timestamp: str
    duration: float
    success: bool

    # Results
    claude_response: Optional[Dict] = None
    git_commit_sha: Optional[str] = None
    git_diff_stats: Optional[Dict] = None
    error: Optional[str] = None

    # Metrics
    metrics: Optional[Dict] = None


@dataclass
class ExperimentComparison:
    """Comparison of multiple experiments."""
    baseline_id: str
    variants: List[str]
    winner: Optional[str] = None
    winner_reason: Optional[str] = None
    metrics_comparison: Optional[Dict] = None


class PromptEngineer:
    """
    Prompt engineering mode for systematic testing.

    Workflow:
    1. Load experiment config (project + prompt variants)
    2. For each prompt variant:
       - Reset project to clean state
       - Run prompt against project
       - Capture full response, git changes, metrics
       - Save structured experiment log
    3. Compare results
    4. Generate insights
    """

    def __init__(self, config: Dict):
        """
        Initialize prompt engineer.

        Args:
            config: Experiment configuration
        """
        self.config = config
        self.wrapper_path = config.get('wrapper', {}).get('path', 'scripts/claude_wrapper.py')
        self.python_exec = config.get('wrapper', {}).get('python_executable', 'python')

        # Setup logging
        self.log_dir = Path(config.get('logging', {}).get('experiment_dir', 'logs/prompt-experiments'))
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize clients
        self.claude = ClaudeClient(self.wrapper_path, self.python_exec)
        self.git_verifier = GitVerifier()

        # Experiment tracking
        self.experiments: List[PromptExperiment] = []
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def run_experiment_suite(self, suite_config: Dict) -> Dict:
        """
        Run a complete experiment suite.

        Args:
            suite_config: Suite configuration with prompts and projects

        Returns:
            Dict with suite results
        """
        print(f"\n{'='*80}")
        print("🧪 PROMPT ENGINEERING MODE")
        print(f"{'='*80}")
        print(f"Session: {self.session_id}")
        print(f"Suite: {suite_config.get('name', 'Unnamed')}")
        print(f"{'='*80}\n")

        # Extract config
        project_path = suite_config['project']['path']
        baseline_ref = suite_config.get('baseline', {}).get('git_ref', 'HEAD')
        prompts = suite_config['prompts']

        print(f"📂 Project: {project_path}")
        print(f"🔖 Baseline: {baseline_ref}")
        print(f"🎯 Prompts to test: {len(prompts)}")
        print()

        # Verify project exists and is git repo
        if not Path(project_path).exists():
            return {'error': f'Project path does not exist: {project_path}'}

        # Save baseline commit
        baseline_commit = self.git_verifier.get_head_commit(project_path)
        print(f"💾 Baseline commit: {baseline_commit[:8]}\n")

        # Run each prompt variant
        for idx, prompt_config in enumerate(prompts, 1):
            print(f"\n{'='*80}")
            print(f"🧪 Experiment {idx}/{len(prompts)}: {prompt_config['name']}")
            print(f"{'='*80}\n")

            # Reset to baseline
            self._reset_to_baseline(project_path, baseline_commit)

            # Run experiment
            experiment = self._run_single_experiment(
                prompt_config,
                project_path,
                baseline_commit
            )

            self.experiments.append(experiment)

            # Save experiment immediately
            self._save_experiment(experiment)

            print(f"\n{'✅' if experiment.success else '❌'} Experiment complete")
            print(f"   Duration: {experiment.duration:.1f}s")
            if experiment.git_commit_sha:
                print(f"   Commit: {experiment.git_commit_sha[:8]}")

        # Compare results
        print(f"\n{'='*80}")
        print("📊 COMPARING RESULTS")
        print(f"{'='*80}\n")

        comparison = self._compare_experiments(suite_config.get('comparison', {}))

        # Save suite summary
        suite_result = {
            'session_id': self.session_id,
            'suite_name': suite_config.get('name', 'Unnamed'),
            'project': project_path,
            'baseline_commit': baseline_commit,
            'experiments_run': len(self.experiments),
            'experiments': [asdict(e) for e in self.experiments],
            'comparison': asdict(comparison) if comparison else None,
            'timestamp': datetime.now().isoformat()
        }

        self._save_suite_summary(suite_result)

        # Print summary
        self._print_summary(comparison)

        return suite_result

    def _run_single_experiment(
        self,
        prompt_config: Dict,
        project_path: str,
        baseline_commit: str
    ) -> PromptExperiment:
        """Run a single prompt experiment."""
        experiment_id = f"{self.session_id}_{prompt_config['name']}"

        print(f"📝 Prompt: {prompt_config.get('description', 'No description')}")

        # Get prompt text (inline or from file)
        if 'text' in prompt_config:
            prompt_text = prompt_config['text']
        elif 'file' in prompt_config:
            with open(prompt_config['file']) as f:
                prompt_text = f.read()
        else:
            return PromptExperiment(
                experiment_id=experiment_id,
                prompt_name=prompt_config['name'],
                prompt_text='',
                project_path=project_path,
                timestamp=datetime.now().isoformat(),
                duration=0,
                success=False,
                error='No prompt text or file specified'
            )

        # Apply template variables
        prompt_text = self._apply_template_vars(prompt_text, prompt_config.get('variables', {}))

        print(f"🔤 Prompt length: {len(prompt_text)} chars")

        # Run prompt
        start_time = time.time()

        timeout = prompt_config.get('timeout', 600)
        result = self.claude.query(
            prompt_text,
            project_path,
            timeout,
            prompt_type=f"experiment_{prompt_config['name']}"
        )

        duration = time.time() - start_time

        # Get git changes
        git_commit_sha = None
        git_diff_stats = None

        if result.get('success'):
            after_commit = self.git_verifier.get_head_commit(project_path)
            if after_commit != baseline_commit:
                git_commit_sha = after_commit
                git_diff_stats = self._get_diff_stats(project_path, baseline_commit, after_commit)

        # Extract metrics if available
        metrics = self._extract_metrics(result, git_diff_stats)

        return PromptExperiment(
            experiment_id=experiment_id,
            prompt_name=prompt_config['name'],
            prompt_text=prompt_text,
            project_path=project_path,
            timestamp=datetime.now().isoformat(),
            duration=duration,
            success=result.get('success', False),
            claude_response=result,
            git_commit_sha=git_commit_sha,
            git_diff_stats=git_diff_stats,
            error=result.get('error'),
            metrics=metrics
        )

    def _reset_to_baseline(self, project_path: str, baseline_commit: str):
        """Reset project to baseline state."""
        print(f"🔄 Resetting to baseline...")

        import subprocess

        # Hard reset to baseline
        subprocess.run(
            ['git', 'reset', '--hard', baseline_commit],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        # Clean untracked files
        subprocess.run(
            ['git', 'clean', '-fd'],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        print("   ✓ Reset complete")

    def _apply_template_vars(self, prompt: str, variables: Dict) -> str:
        """Apply template variables to prompt."""
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt

    def _get_diff_stats(self, project_path: str, before: str, after: str) -> Dict:
        """Get git diff statistics."""
        import subprocess

        result = subprocess.run(
            ['git', 'diff', '--stat', before, after],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        # Parse diff stats
        lines = result.stdout.strip().split('\n')

        if not lines:
            return {'files_changed': 0, 'insertions': 0, 'deletions': 0}

        # Last line has summary: "X files changed, Y insertions(+), Z deletions(-)"
        summary_line = lines[-1] if lines else ''

        import re

        files_match = re.search(r'(\d+) files? changed', summary_line)
        insertions_match = re.search(r'(\d+) insertions?', summary_line)
        deletions_match = re.search(r'(\d+) deletions?', summary_line)

        return {
            'files_changed': int(files_match.group(1)) if files_match else 0,
            'insertions': int(insertions_match.group(1)) if insertions_match else 0,
            'deletions': int(deletions_match.group(1)) if deletions_match else 0,
            'diff_output': result.stdout
        }

    def _extract_metrics(self, claude_result: Dict, diff_stats: Optional[Dict]) -> Dict:
        """Extract metrics from results."""
        metrics = {
            'claude_success': claude_result.get('success', False),
            'has_git_changes': diff_stats is not None and diff_stats.get('files_changed', 0) > 0
        }

        if diff_stats:
            metrics['files_changed'] = diff_stats.get('files_changed', 0)
            metrics['lines_changed'] = diff_stats.get('insertions', 0) + diff_stats.get('deletions', 0)

        # Extract custom metrics from response if available
        if 'metrics' in claude_result:
            metrics['custom'] = claude_result['metrics']

        return metrics

    def _compare_experiments(self, comparison_config: Dict) -> Optional[ExperimentComparison]:
        """Compare experiment results."""
        if len(self.experiments) < 2:
            print("⚠️  Need at least 2 experiments for comparison")
            return None

        # Use first as baseline
        baseline = self.experiments[0]
        variants = self.experiments[1:]

        print(f"📊 Baseline: {baseline.prompt_name}")
        print(f"🔬 Variants: {', '.join(e.prompt_name for e in variants)}\n")

        # Compare metrics
        metrics_comparison = {}

        for variant in variants:
            comparison = {
                'success_diff': variant.success != baseline.success,
                'duration_diff': variant.duration - baseline.duration,
                'duration_ratio': variant.duration / baseline.duration if baseline.duration > 0 else 0
            }

            if variant.metrics and baseline.metrics:
                comparison['metrics'] = {
                    'files_changed_diff': variant.metrics.get('files_changed', 0) - baseline.metrics.get('files_changed', 0),
                    'lines_changed_diff': variant.metrics.get('lines_changed', 0) - baseline.metrics.get('lines_changed', 0)
                }

            metrics_comparison[variant.prompt_name] = comparison

        # Determine winner (if configured)
        winner = None
        winner_reason = None

        criteria = comparison_config.get('criteria', 'success_and_speed')

        if criteria == 'success_and_speed':
            successful = [e for e in self.experiments if e.success]
            if successful:
                winner_exp = min(successful, key=lambda e: e.duration)
                winner = winner_exp.prompt_name
                winner_reason = f"Fastest successful experiment ({winner_exp.duration:.1f}s)"

        return ExperimentComparison(
            baseline_id=baseline.experiment_id,
            variants=[v.experiment_id for v in variants],
            winner=winner,
            winner_reason=winner_reason,
            metrics_comparison=metrics_comparison
        )

    def _save_experiment(self, experiment: PromptExperiment):
        """Save individual experiment log."""
        log_file = self.log_dir / f"{experiment.experiment_id}.json"

        with open(log_file, 'w') as f:
            json.dump(asdict(experiment), f, indent=2, default=str)

        print(f"💾 Saved: {log_file}")

    def _save_suite_summary(self, suite_result: Dict):
        """Save suite summary."""
        summary_file = self.log_dir / f"suite_{self.session_id}.json"

        with open(summary_file, 'w') as f:
            json.dump(suite_result, f, indent=2, default=str)

        print(f"\n💾 Suite summary: {summary_file}")

    def _print_summary(self, comparison: Optional[ExperimentComparison]):
        """Print comparison summary."""
        if not comparison:
            return

        print("\n📈 RESULTS SUMMARY\n")

        print(f"{'Prompt':<30} {'Success':<10} {'Duration':<12} {'Files':<8} {'Lines':<8}")
        print(f"{'-'*30} {'-'*10} {'-'*12} {'-'*8} {'-'*8}")

        for exp in self.experiments:
            success_mark = "✅" if exp.success else "❌"
            files = exp.metrics.get('files_changed', 0) if exp.metrics else 0
            lines = exp.metrics.get('lines_changed', 0) if exp.metrics else 0

            print(f"{exp.prompt_name:<30} {success_mark:<10} {exp.duration:>10.1f}s  {files:>6}  {lines:>6}")

        if comparison.winner:
            print(f"\n🏆 Winner: {comparison.winner}")
            print(f"   Reason: {comparison.winner_reason}")

        print(f"\n📊 Detailed comparison:")
        for variant_name, comp in comparison.metrics_comparison.items():
            print(f"\n   {variant_name} vs baseline:")
            print(f"      Duration: {comp['duration_diff']:+.1f}s ({comp['duration_ratio']:.1%})")
            if 'metrics' in comp:
                print(f"      Files: {comp['metrics']['files_changed_diff']:+d}")
                print(f"      Lines: {comp['metrics']['lines_changed_diff']:+d}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python prompt_engineer.py <experiment.yaml>")
        print("\nExample:")
        print("  python prompt_engineer.py config/experiments/test-creation.yaml")
        sys.exit(1)

    experiment_file = sys.argv[1]

    # Load experiment config
    try:
        with open(experiment_file, 'r') as f:
            suite_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Experiment file not found: {experiment_file}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing experiment file: {e}")
        sys.exit(1)

    # Load base config for wrapper settings
    base_config_path = suite_config.get('base_config', 'config/projects/money-making-app.yaml')
    try:
        with open(base_config_path, 'r') as f:
            base_config = yaml.safe_load(f)
    except:
        # Use minimal defaults
        base_config = {
            'wrapper': {
                'path': 'scripts/claude_wrapper.py',
                'python_executable': 'python'
            }
        }

    # Merge configs
    config = {**base_config, **suite_config.get('config', {})}

    # Run experiment suite
    engineer = PromptEngineer(config)
    result = engineer.run_experiment_suite(suite_config)

    # Exit with appropriate code
    sys.exit(0 if result.get('experiments_run', 0) > 0 else 1)


if __name__ == '__main__':
    main()
