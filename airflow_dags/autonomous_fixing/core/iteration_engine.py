"""
Iteration Engine - Single Responsibility: Manage improvement iterations.

Clean, focused module that ONLY handles the iteration loop logic.
No analysis, no fixing, no scoring - just iteration coordination.
"""

from pathlib import Path
from typing import Dict

from .analysis_verifier import AnalysisVerifier
from .debug_logger import DebugLogger
from .hook_level_manager import HookLevelManager
from .setup_tracker import SetupTracker
from .state_manager import ProjectStateManager
from .time_gatekeeper import TimeGatekeeper
from .validators.preflight import PreflightValidator


class IterationEngine:
    """
    Manages the iterative improvement loop.

    Responsibilities:
    - Loop up to max_iterations
    - Track iteration progress
    - Determine when to stop (gates passed or max reached)
    - Coordinate analyzer, fixer, scorer

    Does NOT:
    - Analyze code (delegates to ProjectAnalyzer)
    - Fix issues (delegates to IssueFixer)
    - Calculate scores (delegates to HealthScorer)
    """

    def __init__(self, analyzer, fixer, scorer, config: Dict, project_name: str = "multi-project"):
        """
        Args:
            analyzer: ProjectAnalyzer instance
            fixer: IssueFixer instance
            scorer: HealthScorer instance
            config: Configuration dict with max_iterations
            project_name: Name for logging purposes
        """
        self.analyzer = analyzer
        self.fixer = fixer
        self.scorer = scorer
        self.config = config
        self.max_iterations = config.get('execution', {}).get('max_iterations', 5)

        # Initialize components (SRP: each has one job)
        self.debug_logger = DebugLogger(config, project_name)
        self.time_gate = TimeGatekeeper(config)
        self.verifier = AnalysisVerifier(config)
        self.hook_manager = HookLevelManager()  # Progressive hook enforcement

        # Setup optimization components
        self.setup_tracker = SetupTracker(config.get('state_manager'))
        self.validator = PreflightValidator(self.setup_tracker)

        # Pass debug logger to fixer for wrapper call logging
        self.fixer.debug_logger = self.debug_logger
        self.fixer.claude.debug_logger = self.debug_logger

        # Circuit breaker for repeated test creation
        self.test_creation_attempts = {}  # project_path -> attempt_count

    def _run_hook_setup_phase(self, projects_by_language: Dict) -> tuple:
        """Run pre-commit hook setup phase (SRP)"""
        print(f"\n{'='*80}")
        print("🔧 SETUP PHASE 0: Pre-Commit Hook Configuration")
        print(f"{'='*80}")

        hooks_total = sum(len(project_list) for project_list in projects_by_language.values())
        hooks_skipped = 0
        hooks_time_saved = 0.0
        hooks_cost_saved = 0.0

        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                can_skip, reason = self.validator.can_skip_hook_config(Path(project_path))
                if can_skip:
                    print(f"   ⏭️  {Path(project_path).name}: {reason}")
                    hooks_skipped += 1
                    hooks_time_saved += 60.0
                    hooks_cost_saved += 0.50
                    continue

                success = self.fixer.configure_precommit_hooks(project_path, lang_name)
                if success:
                    self.setup_tracker.mark_setup_complete(project_path, 'hooks')
                    # Save project state after successful hook configuration
                    try:
                        state_manager = ProjectStateManager(Path(project_path))
                        state_data = {
                            'phase': 'hooks',
                            'language': lang_name,
                            'configured': True
                        }
                        state_manager.save_state('hooks', state_data)
                    except Exception as e:
                        # Log error but don't fail setup tracking
                        print(f"   ⚠️  Failed to save project state for {Path(project_path).name}: {e}")

        if hooks_skipped > 0:
            print(f"\n   ⏭️  Skipped hook setup for {hooks_skipped}/{hooks_total} projects")
            print(f"   💰 Savings: {hooks_time_saved:.0f}s + ${hooks_cost_saved:.2f}")
            self.debug_logger.log_setup_skip_stats(
                phase='hooks',
                skipped=hooks_skipped,
                total=hooks_total,
                time_saved=hooks_time_saved,
                cost_saved=hooks_cost_saved
            )

        return hooks_skipped, hooks_time_saved, hooks_cost_saved

    def _run_test_discovery_phase(self, projects_by_language: Dict) -> tuple:
        """Run test discovery phase (SRP)"""
        print(f"\n{'='*80}")
        print("🔧 SETUP PHASE 1: Test Configuration Discovery")
        print(f"{'='*80}")

        tests_total = sum(len(project_list) for project_list in projects_by_language.values())
        tests_skipped = 0
        tests_time_saved = 0.0
        tests_cost_saved = 0.0

        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                can_skip, reason = self.validator.can_skip_test_discovery(Path(project_path))
                if can_skip:
                    print(f"   ⏭️  {Path(project_path).name}: {reason}")
                    tests_skipped += 1
                    tests_time_saved += 90.0
                    tests_cost_saved += 0.60
                    continue

                result = self.fixer.discover_test_config(project_path, lang_name)
                if result.success:
                    self.setup_tracker.mark_setup_complete(project_path, 'tests')
                    # Save project state after successful test discovery
                    try:
                        state_manager = ProjectStateManager(Path(project_path))
                        state_data = {
                            'phase': 'tests',
                            'language': lang_name,
                            'discovered': True
                        }
                        state_manager.save_state('tests', state_data)
                    except Exception as e:
                        # Log error but don't fail setup tracking
                        print(f"   ⚠️  Failed to save project state for {Path(project_path).name}: {e}")

        if tests_skipped > 0:
            print(f"\n   ⏭️  Skipped test discovery for {tests_skipped}/{tests_total} projects")
            print(f"   💰 Savings: {tests_time_saved:.0f}s + ${tests_cost_saved:.2f}")
            self.debug_logger.log_setup_skip_stats(
                phase='tests',
                skipped=tests_skipped,
                total=tests_total,
                time_saved=tests_time_saved,
                cost_saved=tests_cost_saved
            )

        return tests_skipped, tests_time_saved, tests_cost_saved

    def _print_setup_summary(self, hooks_stats: tuple, tests_stats: tuple, total_projects: int):
        """Print combined setup optimization summary (SRP)"""
        hooks_skipped, hooks_time_saved, hooks_cost_saved = hooks_stats
        tests_skipped, tests_time_saved, tests_cost_saved = tests_stats

        total_skipped = hooks_skipped + tests_skipped
        total_time_saved = hooks_time_saved + tests_time_saved
        total_cost_saved = hooks_cost_saved + tests_cost_saved

        if total_skipped > 0:
            print(f"\n{'='*80}")
            print("📊 SETUP OPTIMIZATION SUMMARY")
            print(f"{'='*80}")
            print(f"   ⏭️  Total skipped: {total_skipped}/{total_projects * 2} setup operations")
            print(f"   💰 Total savings: {total_time_saved:.0f}s + ${total_cost_saved:.2f}")
            print(f"{'='*80}")

    def _run_static_analysis_phase(self, projects_by_language: Dict, iteration: int) -> tuple:
        """Run P1 static analysis phase (SRP)"""
        print(f"\n{'='*80}")
        print("📍 PRIORITY 1: Fast Static Analysis")
        print(f"{'='*80}")

        p1_result = self.analyzer.analyze_static(projects_by_language)

        verification = self.verifier.verify_batch_results(p1_result.results_by_project)
        if not verification['all_valid']:
            self.verifier.print_verification_report(verification)
            print("\n❌ ABORTING: Analysis verification failed")
            return None, None, False

        p1_score_data = self.scorer.score_static_analysis(p1_result)
        self._print_score(p1_score_data, p1_result.execution_time)

        return p1_result, p1_score_data, True

    def _handle_p1_gate_failure(self, p1_result, p1_score_data, iteration: int) -> dict:
        """Handle P1 gate failure - fix issues and check timing (SRP)"""
        print(f"\n⚠️  P1 score ({p1_score_data['score']:.1%}) < threshold ({p1_score_data['threshold']:.0%})")

        max_issues = self.config.get('execution', {}).get('max_issues_per_iteration', 10)
        fix_result = self.fixer.fix_static_issues(p1_result, iteration, max_issues=max_issues)

        self.debug_logger.log_fix_result(
            fix_type='static_issue',
            target='p1_analysis',
            success=fix_result.success,
            duration=p1_result.execution_time,
            details={'fixes_applied': getattr(fix_result, 'fixes_applied', 0)}
        )

        if fix_result.success:
            print("\n✅ Fixes applied, re-running analysis in next iteration...")
        else:
            print("\n⚠️  No fixes could be applied")

        timing_result = self.time_gate.end_iteration(iteration)
        self.debug_logger.log_iteration_end(
            iteration=iteration,
            phase='p1_fix',
            duration=timing_result['duration'],
            success=fix_result.success,
            fixes_applied=getattr(fix_result, 'fixes_applied', 0)
        )

        if timing_result['should_abort']:
            print(f"\n❌ ABORT: Detected {self.time_gate.rapid_threshold} rapid iterations")
            self.debug_logger.log_session_end('rapid_iteration_abort')
            return {
                'success': False,
                'reason': 'rapid_iteration_abort',
                'iterations_completed': iteration,
                'timing_summary': self.time_gate.get_timing_summary()
            }

        self.time_gate.wait_if_needed(timing_result)
        return None  # Continue to next iteration

    def _upgrade_hooks_after_p1(self, projects_by_language: Dict, p1_score_data: dict):
        """Upgrade hooks to level 1 after P1 gate passes (SRP)"""
        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                adapter = self.analyzer._get_adapter(lang_name)
                self.hook_manager.upgrade_after_gate_passed(
                    project_path, lang_name, 'p1',
                    gate_passed=True,
                    score=p1_score_data['score'],
                    adapter=adapter
                )

    def _run_test_analysis_phase(self, projects_by_language: Dict, p1_score_data: dict) -> tuple:
        """Run P2 test analysis phase (SRP)"""
        print(f"\n{'='*80}")
        print("📍 PRIORITY 2: Strategic Unit Tests (Time-Aware)")
        print(f"{'='*80}")

        strategy = self.scorer.determine_test_strategy(p1_score_data['score'])
        print(f"📊 Test strategy: {strategy.upper()} (based on P1 health: {p1_score_data['score']:.1%})")

        p2_result = self.analyzer.analyze_tests(projects_by_language, strategy)

        verification = self.verifier.verify_batch_results(p2_result.results_by_project)
        if not verification['all_valid']:
            self.verifier.print_verification_report(verification)
            print("\n⚠️  WARNING: Test analysis verification failed")

        p2_score_data = self.scorer.score_tests(p2_result)
        self._print_score(p2_score_data, p2_result.execution_time)

        return p2_result, p2_score_data, strategy

    def _handle_test_creation(self, p2_result, iteration: int, projects_by_language: Dict, strategy: str) -> tuple:
        """Handle test creation when no tests exist (SRP)"""
        print("\n⚠️  CRITICAL: No tests found - delegating test creation")

        # Check circuit breaker
        for project_key in p2_result.results_by_project.keys():
            _, project_path = project_key.split(':', 1)
            attempts = self.test_creation_attempts.get(project_path, 0)

            if attempts >= 2:
                print(f"\n❌ ABORT: Project {project_path} has had {attempts} test creation attempts")
                self.debug_logger.log_session_end('test_creation_loop_detected')
                return None, {
                    'success': False,
                    'reason': 'test_creation_loop',
                    'iterations_completed': iteration,
                    'project': project_path
                }

            self.test_creation_attempts[project_path] = attempts + 1

        fix_result = self.fixer.create_tests(p2_result, iteration)
        self.debug_logger.log_test_creation(
            project='multi-project',
            success=fix_result.success,
            tests_created=getattr(fix_result, 'tests_created', 0)
        )

        if fix_result.success:
            print("\n✅ Tests created, re-running test analysis...")
            p2_recheck = self.analyzer.analyze_tests(projects_by_language, strategy)
            p2_recheck_score = self.scorer.score_tests(p2_recheck)

            if p2_recheck_score['passed_gate']:
                # Reset circuit breaker on success
                for project_key in p2_result.results_by_project.keys():
                    _, project_path = project_key.split(':', 1)
                    if project_path in self.test_creation_attempts:
                        del self.test_creation_attempts[project_path]

        return fix_result, None

    def _handle_p2_gate_failure(self, p2_result, p2_score_data, iteration: int,
                                projects_by_language: Dict, strategy: str) -> dict:
        """Handle P2 gate failure - create or fix tests (SRP)"""
        print(f"\n⚠️  P2 score ({p2_score_data['score']:.1%}) < threshold ({p2_score_data['threshold']:.0%})")

        if p2_score_data.get('needs_test_creation', False):
            fix_result, abort_result = self._handle_test_creation(
                p2_result, iteration, projects_by_language, strategy
            )
            if abort_result:
                return abort_result
        else:
            fix_result = self.fixer.fix_test_failures(p2_result, iteration)
            self.debug_logger.log_fix_result(
                fix_type='test_failure',
                target='p2_tests',
                success=fix_result.success,
                duration=p2_result.execution_time,
                details={'fixes_applied': getattr(fix_result, 'fixes_applied', 0)}
            )

            if fix_result.success:
                print("\n✅ Fixes applied, re-running analysis in next iteration...")
            else:
                print("\n⚠️  No fixes could be applied")

        timing_result = self.time_gate.end_iteration(iteration)
        self.debug_logger.log_iteration_end(
            iteration=iteration,
            phase='p2_fix',
            duration=timing_result['duration'],
            success=fix_result.success if fix_result else False,
            fixes_applied=getattr(fix_result, 'fixes_applied', 0) if fix_result else 0,
            tests_created=getattr(fix_result, 'tests_created', 0) if fix_result else 0
        )

        if timing_result['should_abort']:
            print(f"\n❌ ABORT: Detected {self.time_gate.rapid_threshold} rapid iterations")
            self.debug_logger.log_session_end('rapid_iteration_abort')
            return {
                'success': False,
                'reason': 'rapid_iteration_abort',
                'iterations_completed': iteration
            }

        self.time_gate.wait_if_needed(timing_result)
        return None

    def _upgrade_hooks_after_p2(self, projects_by_language: Dict, p2_score_data: dict):
        """Upgrade hooks to level 2 after P2 gate passes (SRP)"""
        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                adapter = self.analyzer._get_adapter(lang_name)
                self.hook_manager.upgrade_after_gate_passed(
                    project_path, lang_name, 'p2',
                    gate_passed=True,
                    score=p2_score_data['score'],
                    adapter=adapter
                )

    def run_improvement_loop(self, projects_by_language: Dict) -> Dict:
        """
        Run the improvement loop until gates pass or max iterations reached.

        Algorithm:
        0. SETUP: Discover test configuration (runs once, cached)
        1. Analyze (P1 static)
        2. Score
        3. If score < threshold: Fix → repeat
        4. If score >= threshold: Analyze (P2 tests)
        5. If score < threshold: Fix → repeat
        6. If both gates passed: Success!

        Returns: Dict with final results and iteration stats
        """
        # Run setup phases
        hooks_stats = self._run_hook_setup_phase(projects_by_language)
        tests_stats = self._run_test_discovery_phase(projects_by_language)

        total_projects = sum(len(project_list) for project_list in projects_by_language.values())
        self._print_setup_summary(hooks_stats, tests_stats, total_projects)

        print(f"\n🔄 Starting improvement iterations (max: {self.max_iterations})")

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*80}")
            print(f"🔁 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'='*80}")

            self.time_gate.start_iteration(iteration)
            self.debug_logger.log_iteration_start(iteration, 'p1_analysis')

            # Run P1 static analysis
            p1_result, p1_score_data, valid = self._run_static_analysis_phase(projects_by_language, iteration)
            if not valid:
                return {'success': False, 'reason': 'analysis_verification_failed'}

            # Check P1 gate
            if not p1_score_data['passed_gate']:
                abort_result = self._handle_p1_gate_failure(p1_result, p1_score_data, iteration)
                if abort_result:
                    return abort_result
                continue  # Re-run analysis in next iteration

            # P1 gate passed!
            print(f"\n✅ P1 gate PASSED ({p1_score_data['score']:.1%} >= {p1_score_data['threshold']:.0%})")

            self._upgrade_hooks_after_p1(projects_by_language, p1_score_data)

            # Run P2 test analysis
            p2_result, p2_score_data, strategy = self._run_test_analysis_phase(projects_by_language, p1_score_data)

            # Check P2 gate
            if not p2_score_data['passed_gate']:
                abort_result = self._handle_p2_gate_failure(
                    p2_result, p2_score_data, iteration, projects_by_language, strategy
                )
                if abort_result:
                    return abort_result
                continue  # Re-run analysis in next iteration

            # Both gates passed!
            print(f"\n✅ P2 gate PASSED ({p2_score_data['score']:.1%} >= {p2_score_data['threshold']:.0%})")

            self._upgrade_hooks_after_p2(projects_by_language, p2_score_data)

            print(f"\n🎉 All priority gates passed in iteration {iteration}!")

            # End iteration timing
            timing_result = self.time_gate.end_iteration(iteration)
            self.debug_logger.log_iteration_end(
                iteration=iteration,
                phase='success',
                duration=timing_result['duration'],
                success=True
            )

            # Log session end with success
            self.debug_logger.log_session_end('all_gates_passed')

            return {
                'success': True,
                'iterations_completed': iteration,
                'p1_score': p1_score_data['score'],
                'p2_score': p2_score_data['score'],
                'overall_health': self.scorer.calculate_overall_health(
                    p1_score_data['score'],
                    p2_score_data['score']
                ),
                'timing_summary': self.time_gate.get_timing_summary(),
                'metrics': self.debug_logger.get_metrics()
            }

        # Max iterations reached without passing gates
        print(f"\n⚠️  Reached maximum iterations ({self.max_iterations}) without passing all gates")

        # Log session end with max iterations
        self.debug_logger.log_session_end('max_iterations_reached')

        return {
            'success': False,
            'reason': 'max_iterations_reached',
            'iterations_completed': self.max_iterations,
            'timing_summary': self.time_gate.get_timing_summary(),
            'metrics': self.debug_logger.get_metrics()
        }

    def _print_score(self, score_data: Dict, execution_time: float):
        """Print score summary."""
        print("\n📊 Phase Result:")
        print(f"   Score: {score_data['score']:.1%}")
        print(f"   Time: {execution_time:.1f}s")
