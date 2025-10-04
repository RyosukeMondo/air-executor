"""
Iteration Engine - Single Responsibility: Manage improvement iterations.

Clean, focused module that ONLY handles the iteration loop logic.
No analysis, no fixing, no scoring - just iteration coordination.
"""

from typing import TYPE_CHECKING, Optional

from .analysis_verifier import AnalysisVerifier
from .debug_logger import DebugLogger
from .hook_level_manager import HookLevelManager
from .setup_phase_runner import SetupPhaseRunner
from .setup_tracker import SetupTracker
from .time_gatekeeper import TimeGatekeeper
from .validators.preflight import PreflightValidator

if TYPE_CHECKING:
    from ..config import OrchestratorConfig
    from .analyzer import ProjectAnalyzer
    from .fixer import IssueFixer
    from .scorer import HealthScorer


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

    def __init__(
        self,
        config: "OrchestratorConfig | dict",
        analyzer: Optional["ProjectAnalyzer"] = None,
        fixer: Optional["IssueFixer"] = None,
        scorer: Optional["HealthScorer"] = None,
        hook_manager: Optional[HookLevelManager] = None,
        project_name: str = "multi-project",
    ):
        """
        Initialize iteration engine with optional dependency injection.

        Args:
            config: Configuration (OrchestratorConfig or dict for backward compatibility)
            analyzer: Optional ProjectAnalyzer instance (required, raise error if None)
            fixer: Optional IssueFixer instance (creates default if None)
            scorer: Optional HealthScorer instance (creates default if None)
            hook_manager: Optional HookLevelManager instance (creates default if None)
            project_name: Name for logging purposes

        Note:
            For backward compatibility with orchestrator, analyzer must be provided.
            Tests can inject all dependencies including mocks.
        """
        # Support both OrchestratorConfig and dict (backward compatibility)
        from ..config import OrchestratorConfig

        if isinstance(config, dict):
            self.orchestrator_config = OrchestratorConfig.from_dict(config)
            self.config = config
        else:
            self.orchestrator_config = config
            self.config = config.to_dict()

        self.max_iterations = self.config.get("execution", {}).get("max_iterations", 5)

        # Dependency injection with defaults
        # Note: analyzer requires language_adapters, so must be provided by caller
        if analyzer is None:
            raise ValueError(
                "ProjectAnalyzer must be provided. "
                "IterationEngine cannot create it without language_adapters."
            )
        self.analyzer: "ProjectAnalyzer" = analyzer

        # Create defaults for components that don't need extra dependencies
        from .fixer import IssueFixer
        from .scorer import HealthScorer

        self.fixer: "IssueFixer" = fixer or IssueFixer(self.config)
        self.scorer: "HealthScorer" = scorer or HealthScorer(self.config)
        self.hook_manager: HookLevelManager = hook_manager or HookLevelManager()

        # Initialize components (SRP: each has one job)
        self.debug_logger = DebugLogger(self.config, project_name)
        self.time_gate = TimeGatekeeper(self.config)
        self.verifier = AnalysisVerifier(self.config)

        # Setup optimization components
        setup_tracker = SetupTracker(self.config.get("state_manager"))
        validator = PreflightValidator(setup_tracker)
        self.setup_runner = SetupPhaseRunner(
            self.fixer, self.debug_logger, setup_tracker, validator
        )

        # Pass debug logger to fixer for wrapper call logging
        self.fixer.debug_logger = self.debug_logger
        self.fixer.claude.debug_logger = self.debug_logger

        # Circuit breaker for repeated test creation
        self.test_creation_attempts = {}  # project_path -> attempt_count

    def _run_static_analysis_phase(self, projects_by_language: dict, iteration: int) -> tuple:
        """Run P1 static analysis phase (SRP)"""
        print(f"\n{'='*80}")
        print("📍 PRIORITY 1: Fast Static Analysis")
        print(f"{'='*80}")

        p1_result = self.analyzer.analyze_static(projects_by_language)

        verification = self.verifier.verify_batch_results(p1_result.results_by_project)
        if not verification["all_valid"]:
            self.verifier.print_verification_report(verification)
            print("\n❌ ABORTING: Analysis verification failed")
            return None, None, False

        p1_score_data = self.scorer.score_static_analysis(p1_result)
        self._print_score(p1_score_data, p1_result.execution_time)

        return p1_result, p1_score_data, True

    def _handle_p1_gate_failure(self, p1_result, p1_score_data, iteration: int) -> dict:
        """Handle P1 gate failure - fix issues and check timing (SRP)"""
        print(
            f"\n⚠️  P1 score ({p1_score_data['score']:.1%}) < "
            f"threshold ({p1_score_data['threshold']:.0%})"
        )

        max_issues = self.config.get("execution", {}).get("max_issues_per_iteration", 10)
        fix_result = self.fixer.fix_static_issues(p1_result, iteration, max_issues=max_issues)

        self.debug_logger.log_fix_result(
            fix_type="static_issue",
            target="p1_analysis",
            success=fix_result.success,
            duration=p1_result.execution_time,
            details={"fixes_applied": getattr(fix_result, "fixes_applied", 0)},
        )

        if fix_result.success:
            print("\n✅ Fixes applied, re-running analysis in next iteration...")
        else:
            print("\n⚠️  No fixes could be applied")

        timing_result = self.time_gate.end_iteration(iteration)
        self.debug_logger.log_iteration_end(
            iteration=iteration,
            phase="p1_fix",
            duration=timing_result["duration"],
            success=fix_result.success,
            fixes_applied=getattr(fix_result, "fixes_applied", 0),
        )

        if timing_result["should_abort"]:
            print(f"\n❌ ABORT: Detected {self.time_gate.rapid_threshold} rapid iterations")
            self.debug_logger.log_session_end("rapid_iteration_abort")
            return {
                "success": False,
                "reason": "rapid_iteration_abort",
                "iterations_completed": iteration,
                "timing_summary": self.time_gate.get_timing_summary(),
            }

        self.time_gate.wait_if_needed(timing_result)
        return None  # Continue to next iteration

    def _upgrade_hooks_after_p1(self, projects_by_language: dict, p1_score_data: dict):
        """Upgrade hooks to level 1 after P1 gate passes (SRP)"""
        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                adapter = self.analyzer.adapters.get(lang_name)
                self.hook_manager.upgrade_after_gate_passed(
                    project_path,
                    lang_name,
                    "p1",
                    gate_passed=True,
                    score=p1_score_data["score"],
                    adapter=adapter,
                )

    def _run_test_analysis_phase(self, projects_by_language: dict, p1_score_data: dict) -> tuple:
        """Run P2 test analysis phase (SRP)"""
        print(f"\n{'='*80}")
        print("📍 PRIORITY 2: Strategic Unit Tests (Time-Aware)")
        print(f"{'='*80}")

        strategy = self.scorer.determine_test_strategy(p1_score_data["score"])
        print(
            f"📊 Test strategy: {strategy.upper()} "
            f"(based on P1 health: {p1_score_data['score']:.1%})"
        )

        p2_result = self.analyzer.analyze_tests(projects_by_language, strategy)

        verification = self.verifier.verify_batch_results(p2_result.results_by_project)
        if not verification["all_valid"]:
            self.verifier.print_verification_report(verification)
            print("\n⚠️  WARNING: Test analysis verification failed")

        p2_score_data = self.scorer.score_tests(p2_result)
        self._print_score(p2_score_data, p2_result.execution_time)

        return p2_result, p2_score_data, strategy

    def _check_test_creation_circuit_breaker(self, p2_result, iteration: int) -> dict:
        """Check if circuit breaker should stop test creation. Returns abort_result or None."""
        for project_key in p2_result.results_by_project.keys():
            _, project_path = project_key.split(":", 1)
            attempts = self.test_creation_attempts.get(project_path, 0)

            if attempts >= 2:
                print(
                    f"\n❌ ABORT: Project {project_path} has had {attempts} test creation attempts"
                )
                self.debug_logger.log_session_end("test_creation_loop_detected")
                return {
                    "success": False,
                    "reason": "test_creation_loop",
                    "iterations_completed": iteration,
                    "project": project_path,
                }

            self.test_creation_attempts[project_path] = attempts + 1

        return None

    def _reset_test_creation_circuit_breaker(self, p2_result):
        """Reset circuit breaker after successful test creation."""
        for project_key in p2_result.results_by_project.keys():
            _, project_path = project_key.split(":", 1)
            if project_path in self.test_creation_attempts:
                del self.test_creation_attempts[project_path]

    def _handle_test_creation(
        self, p2_result, iteration: int, projects_by_language: dict, strategy: str
    ) -> tuple:
        """Handle test creation when no tests exist (SRP)"""
        print("\n⚠️  CRITICAL: No tests found - delegating test creation")

        # Check circuit breaker
        abort_result = self._check_test_creation_circuit_breaker(p2_result, iteration)
        if abort_result:
            return None, abort_result

        fix_result = self.fixer.create_tests(p2_result, iteration)
        self.debug_logger.log_test_creation(
            project="multi-project",
            success=fix_result.success,
            tests_created=getattr(fix_result, "tests_created", 0),
        )

        if fix_result.success:
            print("\n✅ Tests created, re-running test analysis...")
            p2_recheck = self.analyzer.analyze_tests(projects_by_language, strategy)
            p2_recheck_score = self.scorer.score_tests(p2_recheck)

            if p2_recheck_score["passed_gate"]:
                self._reset_test_creation_circuit_breaker(p2_result)

        return fix_result, None

    def _fix_p2_issues(
        self, p2_result, p2_score_data, iteration: int, projects_by_language: dict, strategy: str
    ) -> tuple:
        """
        Fix P2 issues - either create tests or fix failures.
        Returns (fix_result, abort_result).
        """
        if p2_score_data.get("needs_test_creation", False):
            return self._handle_test_creation(p2_result, iteration, projects_by_language, strategy)

        fix_result = self.fixer.fix_test_failures(p2_result, iteration)
        self.debug_logger.log_fix_result(
            fix_type="test_failure",
            target="p2_tests",
            success=fix_result.success,
            duration=p2_result.execution_time,
            details={"fixes_applied": getattr(fix_result, "fixes_applied", 0)},
        )

        if fix_result.success:
            print("\n✅ Fixes applied, re-running analysis in next iteration...")
        else:
            print("\n⚠️  No fixes could be applied")

        return fix_result, None

    def _check_timing_abort(self, iteration: int, fix_result) -> dict:
        """Check if timing should abort iteration. Returns abort_result or None."""
        timing_result = self.time_gate.end_iteration(iteration)
        self.debug_logger.log_iteration_end(
            iteration=iteration,
            phase="p2_fix",
            duration=timing_result["duration"],
            success=fix_result.success if fix_result else False,
            fixes_applied=getattr(fix_result, "fixes_applied", 0) if fix_result else 0,
            tests_created=getattr(fix_result, "tests_created", 0) if fix_result else 0,
        )

        if timing_result["should_abort"]:
            print(f"\n❌ ABORT: Detected {self.time_gate.rapid_threshold} rapid iterations")
            self.debug_logger.log_session_end("rapid_iteration_abort")
            return {
                "success": False,
                "reason": "rapid_iteration_abort",
                "iterations_completed": iteration,
            }

        self.time_gate.wait_if_needed(timing_result)
        return None

    def _handle_p2_gate_failure(
        self, p2_result, p2_score_data, iteration: int, projects_by_language: dict, strategy: str
    ) -> dict:
        """Handle P2 gate failure - create or fix tests (SRP)"""
        print(
            f"\n⚠️  P2 score ({p2_score_data['score']:.1%}) < "
            f"threshold ({p2_score_data['threshold']:.0%})"
        )

        fix_result, abort_result = self._fix_p2_issues(
            p2_result, p2_score_data, iteration, projects_by_language, strategy
        )
        if abort_result:
            return abort_result

        return self._check_timing_abort(iteration, fix_result)

    def _upgrade_hooks_after_p2(self, projects_by_language: dict, p2_score_data: dict):
        """Upgrade hooks to level 2 after P2 gate passes (SRP)"""
        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                adapter = self.analyzer.adapters.get(lang_name)
                self.hook_manager.upgrade_after_gate_passed(
                    project_path,
                    lang_name,
                    "p2",
                    gate_passed=True,
                    score=p2_score_data["score"],
                    adapter=adapter,
                )

    def _run_setup_phases(self, projects_by_language: dict):
        """Run all setup phases and print summary (delegated to SetupPhaseRunner)."""
        self.setup_runner.run_setup_phases(projects_by_language)

    def _process_p1_gate(self, projects_by_language: dict, iteration: int) -> tuple:
        """Process P1 gate. Returns (p1_score_data, abort_result, should_continue)."""
        p1_result, p1_score_data, valid = self._run_static_analysis_phase(
            projects_by_language, iteration
        )
        if not valid:
            return None, {"success": False, "reason": "analysis_verification_failed"}, False

        if not p1_score_data["passed_gate"]:
            abort_result = self._handle_p1_gate_failure(p1_result, p1_score_data, iteration)
            if abort_result:
                return None, abort_result, False
            return None, None, True  # Continue to next iteration

        print(
            f"\n✅ P1 gate PASSED ({p1_score_data['score']:.1%} >= "
            f"{p1_score_data['threshold']:.0%})"
        )
        self._upgrade_hooks_after_p1(projects_by_language, p1_score_data)
        return p1_score_data, None, False

    def _process_p2_gate(
        self, projects_by_language: dict, p1_score_data: dict, iteration: int
    ) -> tuple:
        """Process P2 gate. Returns (p2_score_data, abort_result, should_continue)."""
        p2_result, p2_score_data, strategy = self._run_test_analysis_phase(
            projects_by_language, p1_score_data
        )

        if not p2_score_data["passed_gate"]:
            abort_result = self._handle_p2_gate_failure(
                p2_result, p2_score_data, iteration, projects_by_language, strategy
            )
            if abort_result:
                return None, abort_result, False
            return None, None, True  # Continue to next iteration

        print(
            f"\n✅ P2 gate PASSED ({p2_score_data['score']:.1%} >= "
            f"{p2_score_data['threshold']:.0%})"
        )
        self._upgrade_hooks_after_p2(projects_by_language, p2_score_data)
        return p2_score_data, None, False

    def _build_success_result(
        self, iteration: int, p1_score_data: dict, p2_score_data: dict
    ) -> dict:
        """Build success result dictionary."""
        timing_result = self.time_gate.end_iteration(iteration)
        self.debug_logger.log_iteration_end(
            iteration=iteration, phase="success", duration=timing_result["duration"], success=True
        )
        self.debug_logger.log_session_end("all_gates_passed")

        return {
            "success": True,
            "iterations_completed": iteration,
            "p1_score": p1_score_data["score"],
            "p2_score": p2_score_data["score"],
            "overall_health": self.scorer.calculate_overall_health(
                p1_score_data["score"], p2_score_data["score"]
            ),
            "timing_summary": self.time_gate.get_timing_summary(),
            "metrics": self.debug_logger.get_metrics(),
        }

    def _run_single_iteration(self, projects_by_language: dict, iteration: int) -> dict:
        """Run a single iteration. Returns result dict if done, None to continue."""
        print(f"\n{'='*80}")
        print(f"🔁 ITERATION {iteration}/{self.max_iterations}")
        print(f"{'='*80}")

        self.time_gate.start_iteration(iteration)
        self.debug_logger.log_iteration_start(iteration, "p1_analysis")

        # Process P1 gate
        p1_score_data, abort_result, should_continue = self._process_p1_gate(
            projects_by_language, iteration
        )
        if abort_result:
            return abort_result
        if should_continue:
            return None

        # Process P2 gate
        p2_score_data, abort_result, should_continue = self._process_p2_gate(
            projects_by_language, p1_score_data, iteration
        )
        if abort_result:
            return abort_result
        if should_continue:
            return None

        # Both gates passed!
        print(f"\n🎉 All priority gates passed in iteration {iteration}!")
        return self._build_success_result(iteration, p1_score_data, p2_score_data)

    def run_improvement_loop(self, projects_by_language: dict) -> dict:
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
        self._run_setup_phases(projects_by_language)
        print(f"\n🔄 Starting improvement iterations (max: {self.max_iterations})")

        for iteration in range(1, self.max_iterations + 1):
            result = self._run_single_iteration(projects_by_language, iteration)
            if result:
                return result

        # Max iterations reached without passing gates
        print(f"\n⚠️  Reached maximum iterations ({self.max_iterations}) without passing all gates")
        self.debug_logger.log_session_end("max_iterations_reached")

        return {
            "success": False,
            "reason": "max_iterations_reached",
            "iterations_completed": self.max_iterations,
            "timing_summary": self.time_gate.get_timing_summary(),
            "metrics": self.debug_logger.get_metrics(),
        }

    def _print_score(self, score_data: dict, execution_time: float):
        """Print score summary."""
        print("\n📊 Phase Result:")
        print(f"   Score: {score_data['score']:.1%}")
        print(f"   Time: {execution_time:.1f}s")
