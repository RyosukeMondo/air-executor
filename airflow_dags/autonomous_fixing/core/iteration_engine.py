"""
Iteration Engine - Single Responsibility: Manage improvement iterations.

Clean, focused module that ONLY handles the iteration loop logic.
No analysis, no fixing, no scoring - just iteration coordination.
"""

from typing import Dict
from .debug_logger import DebugLogger
from .time_gatekeeper import TimeGatekeeper
from .analysis_verifier import AnalysisVerifier


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

        # Pass debug logger to fixer for wrapper call logging
        self.fixer.debug_logger = self.debug_logger
        self.fixer.claude.debug_logger = self.debug_logger

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
        # === SETUP PHASE: Test Discovery (runs once) ===
        print(f"\n{'='*80}")
        print("🔧 SETUP PHASE: Test Configuration Discovery")
        print(f"{'='*80}")

        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                self.fixer.discover_test_config(project_path, lang_name)

        print(f"\n🔄 Starting improvement iterations (max: {self.max_iterations})")

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*80}")
            print(f"🔁 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'='*80}")

            # Start iteration timing
            iteration_start = self.time_gate.start_iteration(iteration)
            self.debug_logger.log_iteration_start(iteration, 'p1_analysis')

            # === PHASE 1: Static Analysis ===
            print(f"\n{'='*80}")
            print("📍 PRIORITY 1: Fast Static Analysis")
            print(f"{'='*80}")

            p1_result = self.analyzer.analyze_static(projects_by_language)

            # Verify analysis results (detect silent failures)
            verification = self.verifier.verify_batch_results(p1_result.results_by_project)
            if not verification['all_valid']:
                self.verifier.print_verification_report(verification)
                print("\n❌ ABORTING: Analysis verification failed - cannot trust results")
                return {
                    'success': False,
                    'reason': 'analysis_verification_failed',
                    'verification_report': verification
                }

            p1_score_data = self.scorer.score_static_analysis(p1_result)

            self._print_score(p1_score_data, p1_result.execution_time)

            # Check P1 gate
            if not p1_score_data['passed_gate']:
                print(f"\n⚠️  P1 score ({p1_score_data['score']:.1%}) < threshold ({p1_score_data['threshold']:.0%})")

                # Fix P1 issues (limit from config)
                max_issues = self.config.get('execution', {}).get('max_issues_per_iteration', 10)
                fix_result = self.fixer.fix_static_issues(p1_result, iteration, max_issues=max_issues)

                # Log fix results
                self.debug_logger.log_fix_result(
                    fix_type='static_issue',
                    target='p1_analysis',
                    success=fix_result.success,
                    duration=p1_result.execution_time,
                    details={'fixes_applied': getattr(fix_result, 'fixes_applied', 0)}
                )

                if fix_result.success:
                    print(f"\n✅ Fixes applied, re-running analysis in next iteration...")
                else:
                    print(f"\n⚠️  No fixes could be applied")

                # End iteration timing and check gates
                timing_result = self.time_gate.end_iteration(iteration)
                self.debug_logger.log_iteration_end(
                    iteration=iteration,
                    phase='p1_fix',
                    duration=timing_result['duration'],
                    success=fix_result.success,
                    fixes_applied=getattr(fix_result, 'fixes_applied', 0)
                )

                # Check if we should abort due to rapid iterations
                if timing_result['should_abort']:
                    print(f"\n❌ ABORT: Detected {self.time_gate.rapid_threshold} rapid iterations within {self.time_gate.rapid_window}s")
                    print(f"   This indicates the system is stuck in a wasteful loop.")
                    print(f"   Timing summary: {self.time_gate.get_timing_summary()}")

                    self.debug_logger.log_session_end('rapid_iteration_abort')
                    return {
                        'success': False,
                        'reason': 'rapid_iteration_abort',
                        'iterations_completed': iteration,
                        'timing_summary': self.time_gate.get_timing_summary()
                    }

                # Wait if iteration was too fast
                self.time_gate.wait_if_needed(timing_result)

                continue  # Re-run analysis in next iteration

            # P1 gate passed!
            print(f"\n✅ P1 gate PASSED ({p1_score_data['score']:.1%} >= {p1_score_data['threshold']:.0%})")

            # === PHASE 2: Tests ===
            print(f"\n{'='*80}")
            print("📍 PRIORITY 2: Strategic Unit Tests (Time-Aware)")
            print(f"{'='*80}")

            # Determine test strategy based on P1 health
            strategy = self.scorer.determine_test_strategy(p1_score_data['score'])
            print(f"📊 Test strategy: {strategy.upper()} (based on P1 health: {p1_score_data['score']:.1%})")

            p2_result = self.analyzer.analyze_tests(projects_by_language, strategy)

            # Verify test analysis results
            verification = self.verifier.verify_batch_results(p2_result.results_by_project)
            if not verification['all_valid']:
                self.verifier.print_verification_report(verification)
                print("\n⚠️  WARNING: Test analysis verification failed - results may be unreliable")
                # Continue anyway since tests are less critical than static analysis

            p2_score_data = self.scorer.score_tests(p2_result)

            self._print_score(p2_score_data, p2_result.execution_time)

            # Check P2 gate
            if not p2_score_data['passed_gate']:
                print(f"\n⚠️  P2 score ({p2_score_data['score']:.1%}) < threshold ({p2_score_data['threshold']:.0%})")

                # Check if this is a "no tests" situation (critical failure)
                if p2_score_data.get('needs_test_creation', False):
                    print("\n⚠️  CRITICAL: No tests found - delegating test creation to claude_wrapper")

                    # Create tests using LLM-as-a-judge
                    fix_result = self.fixer.create_tests(p2_result, iteration)

                    # Log test creation
                    self.debug_logger.log_test_creation(
                        project='multi-project',
                        success=fix_result.success,
                        tests_created=getattr(fix_result, 'tests_created', 0)
                    )

                    if fix_result.success:
                        print(f"\n✅ Tests created, re-running analysis in next iteration...")
                    else:
                        print(f"\n⚠️  Test creation failed")

                else:
                    # Fix P2 issues (failing tests)
                    fix_result = self.fixer.fix_test_failures(p2_result, iteration)

                    # Log fix results
                    self.debug_logger.log_fix_result(
                        fix_type='test_failure',
                        target='p2_tests',
                        success=fix_result.success,
                        duration=p2_result.execution_time,
                        details={'fixes_applied': getattr(fix_result, 'fixes_applied', 0)}
                    )

                    if fix_result.success:
                        print(f"\n✅ Fixes applied, re-running analysis in next iteration...")
                    else:
                        print(f"\n⚠️  No fixes could be applied")

                # End iteration timing and check gates
                timing_result = self.time_gate.end_iteration(iteration)
                self.debug_logger.log_iteration_end(
                    iteration=iteration,
                    phase='p2_fix',
                    duration=timing_result['duration'],
                    success=fix_result.success,
                    fixes_applied=getattr(fix_result, 'fixes_applied', 0),
                    tests_created=getattr(fix_result, 'tests_created', 0)
                )

                # Check if we should abort due to rapid iterations
                if timing_result['should_abort']:
                    print(f"\n❌ ABORT: Detected {self.time_gate.rapid_threshold} rapid iterations within {self.time_gate.rapid_window}s")
                    print(f"   This indicates the system is stuck in a wasteful loop.")
                    print(f"   Timing summary: {self.time_gate.get_timing_summary()}")

                    self.debug_logger.log_session_end('rapid_iteration_abort')
                    return {
                        'success': False,
                        'reason': 'rapid_iteration_abort',
                        'iterations_completed': iteration,
                        'timing_summary': self.time_gate.get_timing_summary()
                    }

                # Wait if iteration was too fast
                self.time_gate.wait_if_needed(timing_result)

                continue  # Re-run analysis in next iteration

            # Both gates passed!
            print(f"\n✅ P2 gate PASSED ({p2_score_data['score']:.1%} >= {p2_score_data['threshold']:.0%})")
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
        print(f"\n📊 Phase Result:")
        print(f"   Score: {score_data['score']:.1%}")
        print(f"   Time: {execution_time:.1f}s")
