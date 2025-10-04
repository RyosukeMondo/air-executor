"""
Setup Phase Runner - Extract setup logic from IterationEngine.

Single Responsibility: Manage hook and test setup phases.
"""

from pathlib import Path

from ..domain.interfaces import ISetupTracker
from .debug_logger import DebugLogger
from .state_manager import ProjectStateManager
from .validators.preflight import PreflightValidator


class SetupPhaseRunner:
    """
    Manages hook and test setup phases.

    Responsibilities:
    - Run hook configuration phase
    - Run test discovery phase
    - Track setup progress and optimization
    - Print setup summaries

    Does NOT:
    - Analyze code
    - Fix issues
    - Score health
    """

    def __init__(
        self,
        fixer,
        debug_logger: DebugLogger,
        setup_tracker: ISetupTracker,
        validator: PreflightValidator,
    ):
        """
        Initialize setup phase runner.

        Args:
            fixer: IssueFixer instance for running setup operations
            debug_logger: Debug logger for logging
            setup_tracker: Setup tracker for marking completion
            validator: Preflight validator for skip logic
        """
        self.fixer = fixer
        self.debug_logger = debug_logger
        self.setup_tracker = setup_tracker
        self.validator = validator

    def _save_project_state_safe(self, project_path: str, phase: str, lang_name: str, **kwargs):
        """Safely save project state without failing on error."""
        try:
            state_manager = ProjectStateManager(Path(project_path))
            state_data = {"phase": phase, "language": lang_name, **kwargs}
            state_manager.save_state(phase, state_data)
        except Exception as e:
            print(f"   ⚠️  Failed to save project state for {Path(project_path).name}: {e}")

    def _process_hook_setup_for_project(
        self, project_path: str, lang_name: str
    ) -> tuple[bool, float, float]:
        """
        Process hook setup for a single project.

        Returns (skipped, time_saved, cost_saved).
        """
        can_skip, reason = self.validator.can_skip_hook_config(Path(project_path))
        if can_skip:
            print(f"   ⏭️  {Path(project_path).name}: {reason}")
            return True, 60.0, 0.50

        success = self.fixer.configure_precommit_hooks(project_path, lang_name)
        if success:
            self.setup_tracker.mark_setup_complete(project_path, "hooks")
            self._save_project_state_safe(project_path, "hooks", lang_name, configured=True)

        return False, 0.0, 0.0

    def _run_hook_setup_phase(self, projects_by_language: dict) -> tuple:
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
                skipped, time_saved, cost_saved = self._process_hook_setup_for_project(
                    project_path, lang_name
                )
                if skipped:
                    hooks_skipped += 1
                    hooks_time_saved += time_saved
                    hooks_cost_saved += cost_saved

        if hooks_skipped > 0:
            print(f"\n   ⏭️  Skipped hook setup for {hooks_skipped}/{hooks_total} projects")
            print(f"   💰 Savings: {hooks_time_saved:.0f}s + ${hooks_cost_saved:.2f}")
            self.debug_logger.log_setup_skip_stats(
                phase="hooks",
                skipped=hooks_skipped,
                total=hooks_total,
                time_saved=hooks_time_saved,
                cost_saved=hooks_cost_saved,
            )

        return hooks_skipped, hooks_time_saved, hooks_cost_saved

    def _process_test_discovery_for_project(
        self, project_path: str, lang_name: str
    ) -> tuple[bool, float, float]:
        """
        Process test discovery for a single project.

        Returns (skipped, time_saved, cost_saved).
        """
        can_skip, reason = self.validator.can_skip_test_discovery(Path(project_path))
        if can_skip:
            print(f"   ⏭️  {Path(project_path).name}: {reason}")
            return True, 90.0, 0.60

        result = self.fixer.discover_test_config(project_path, lang_name)
        if result.success:
            self.setup_tracker.mark_setup_complete(project_path, "tests")
            self._save_project_state_safe(project_path, "tests", lang_name, discovered=True)

        return False, 0.0, 0.0

    def _run_test_discovery_phase(self, projects_by_language: dict) -> tuple:
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
                skipped, time_saved, cost_saved = self._process_test_discovery_for_project(
                    project_path, lang_name
                )
                if skipped:
                    tests_skipped += 1
                    tests_time_saved += time_saved
                    tests_cost_saved += cost_saved

        if tests_skipped > 0:
            print(f"\n   ⏭️  Skipped test discovery for {tests_skipped}/{tests_total} projects")
            print(f"   💰 Savings: {tests_time_saved:.0f}s + ${tests_cost_saved:.2f}")
            self.debug_logger.log_setup_skip_stats(
                phase="tests",
                skipped=tests_skipped,
                total=tests_total,
                time_saved=tests_time_saved,
                cost_saved=tests_cost_saved,
            )

        return tests_skipped, tests_time_saved, tests_cost_saved

    def print_setup_summary(self, hooks_stats: tuple, tests_stats: tuple, total_projects: int):
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
            print(f"   ⏭️  Total skipped: {total_skipped}/{total_projects * 2} operations")
            print(f"   💰 Total savings: {total_time_saved:.0f}s + ${total_cost_saved:.2f}")
            print(f"{'='*80}")

    def run_setup_phases(self, projects_by_language: dict):
        """
        Run both setup phases (hooks + tests).

        Returns tuple of (hooks_stats, tests_stats, total_projects).
        """
        total_projects = sum(len(projects) for projects in projects_by_language.values())

        hooks_stats = self._run_hook_setup_phase(projects_by_language)
        tests_stats = self._run_test_discovery_phase(projects_by_language)
        self.print_setup_summary(hooks_stats, tests_stats, total_projects)

        return hooks_stats, tests_stats, total_projects
