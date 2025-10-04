"""
Issue Fixer - Single Responsibility: Fix detected issues.

Clean, focused module that ONLY handles calling claude_wrapper to fix issues.
No analysis, no scoring, no iteration logic - just fixing.
"""

from typing import TYPE_CHECKING, Optional

from ..adapters.ai.claude_client import ClaudeClient
from ..domain.enums import IssueType
from ..domain.models import FixResult
from .analysis_delegate import AnalysisDelegate
from .commit_verifier import CommitVerifier
from .issue_extractor import IssueExtractor
from .prompt_manager import PromptManager

if TYPE_CHECKING:
    from ..config.orchestrator_config import OrchestratorConfig
    from ..domain.interfaces import IAIClient


class IssueFixer:
    """
    Fixes issues using claude_wrapper.

    Responsibilities:
    - Extract top issues from analysis results
    - Call claude_wrapper with appropriate prompts
    - Track success/failure of fixes
    - Return fix results

    Does NOT:
    - Analyze code (that's ProjectAnalyzer's job)
    - Calculate scores (that's HealthScorer's job)
    - Manage iterations (that's IterationEngine's job)
    """

    def __init__(
        self,
        config: "OrchestratorConfig | dict",
        debug_logger=None,
        ai_client: Optional["IAIClient"] = None,
    ):
        """
        Args:
            config: OrchestratorConfig or dict with wrapper settings
            debug_logger: Optional DebugLogger instance
            ai_client: Optional AI client implementing IAIClient. If None, creates default ClaudeClient.
        """
        # Support both OrchestratorConfig and dict
        if isinstance(config, dict):
            from ..config.orchestrator_config import OrchestratorConfig

            self.orchestrator_config = OrchestratorConfig.from_dict(config)
            self.config = config
        else:
            self.orchestrator_config = config
            self.config = config.to_dict()

        self.debug_logger = debug_logger

        # Initialize helpers
        self.prompt_manager = PromptManager()
        self.commit_verifier = CommitVerifier()
        self.issue_extractor = IssueExtractor()

        # Initialize Claude client (use injected or create default)
        self.claude: "IAIClient" = ai_client or self._create_claude_client()

        # Initialize analysis delegate
        self.analysis_delegate = AnalysisDelegate(self.config, debug_logger)

    def _create_claude_client(self) -> ClaudeClient:
        """Create default Claude client from config.

        Returns:
            ClaudeClient configured with wrapper settings from config.
        """
        wrapper_path = self.config.get("wrapper", {}).get("path", "scripts/claude_wrapper.py")
        python_exec = self.config.get("wrapper", {}).get("python_executable", "python")

        return ClaudeClient(wrapper_path, python_exec, self.debug_logger, self.config)

    def fix_static_issues(self, analysis_result, iteration: int, max_issues: int = 10) -> FixResult:
        """
        Fix static analysis issues (P1).

        Args:
            analysis_result: AnalysisResult from ProjectAnalyzer
            iteration: Current iteration number (for logging)
            max_issues: Maximum issues to fix per iteration

        Returns: FixResult with stats
        """
        print(f"\n🔧 Fixing P1 issues (iteration {iteration})...")

        # Collect issues using extractor
        all_issues = self.issue_extractor.extract_static_issues(
            analysis_result.results_by_project, max_issues
        )

        if not all_issues:
            print("   No issues to fix")
            return FixResult(success=False)

        print(f"   Selected {len(all_issues)} issues to fix")

        # Fix each issue
        fixes_applied = 0
        for idx, issue in enumerate(all_issues, 1):
            print(f"\n   [{idx}/{len(all_issues)}] Fixing {issue['type']} in {issue['file']}")

            if self._fix_single_issue(issue):
                print("      ✓ Fixed successfully")
                fixes_applied += 1
            else:
                print("      ✗ Fix failed")

        print(f"\n   Applied {fixes_applied}/{len(all_issues)} fixes")

        return FixResult(
            fixes_applied=fixes_applied, fixes_attempted=len(all_issues), success=fixes_applied > 0
        )

    def fix_test_failures(
        self, analysis_result, iteration: int, max_projects: int = 5
    ) -> FixResult:
        """
        Fix test failures (P2).

        Args:
            analysis_result: AnalysisResult from ProjectAnalyzer
            iteration: Current iteration number (for logging)
            max_projects: Maximum projects to fix per iteration

        Returns: FixResult with stats
        """
        print(f"\n🔧 Fixing P2 test failures (iteration {iteration})...")

        # Collect failing tests using extractor
        failing_tests = self.issue_extractor.extract_test_failures(
            analysis_result.results_by_project, max_projects
        )

        if not failing_tests:
            print("   No failing tests to fix")
            return FixResult(success=False)

        print(f"   Found {len(failing_tests)} projects with test failures")

        # Fix each project
        fixes_applied = 0
        for test_info in failing_tests:
            print(
                f"\n   Fixing {test_info['failed']} failing tests in {test_info['project'].split('/')[-1]}"
            )

            if self._fix_failing_tests(test_info):
                print("      ✓ Fixed successfully")
                fixes_applied += 1
            else:
                print("      ✗ Fix failed")

        print(f"\n   Applied fixes to {fixes_applied}/{len(failing_tests)} projects")

        return FixResult(
            fixes_applied=fixes_applied,
            fixes_attempted=len(failing_tests),
            success=fixes_applied > 0,
        )

    def _fix_single_issue(self, issue: dict) -> bool:
        """Fix a single static issue using claude_wrapper."""
        # Get HEAD commit before fix
        before_commit = self.commit_verifier.get_head_commit(issue["project"])

        # Build prompt using prompt manager
        if issue["type"] == str(IssueType.ERROR):
            prompt = self.prompt_manager.build_error_prompt(issue)
            prompt_type = "fix_error"
        elif issue["type"] == str(IssueType.COMPLEXITY):
            prompt = self.prompt_manager.build_complexity_prompt(issue)
            prompt_type = "fix_complexity"
        else:
            return False

        # Get timeout from prompt manager
        timeout = self.prompt_manager.get_timeout("fix_static_issue")

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, issue["project"], timeout, prompt_type=prompt_type)

        # Verify commit was made
        if result.get("success", False):
            return self.commit_verifier.verify_fix_committed(
                issue["project"], before_commit, f"fixing {issue['type']}"
            )

        return False

    def _fix_failing_tests(self, test_info: dict) -> bool:
        """Fix failing tests for a project using claude_wrapper."""
        # Get HEAD commit before fix
        before_commit = self.commit_verifier.get_head_commit(test_info["project"])

        # Build prompt using prompt manager
        prompt = self.prompt_manager.build_test_failure_prompt(test_info)

        # Get timeout from prompt manager
        timeout = self.prompt_manager.get_timeout("fix_test_failure")

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, test_info["project"], timeout, prompt_type="fix_test")

        # Verify commit was made
        if result.get("success", False):
            return self.commit_verifier.verify_fix_committed(
                test_info["project"], before_commit, "fixing tests"
            )

        return False

    def analyze_static(self, project_path: str, language: str) -> dict:
        """
        ANALYSIS PHASE: Static code quality analysis via claude_wrapper.

        Delegates to AnalysisDelegate.
        """
        return self.analysis_delegate.analyze_static(project_path, language)

    def configure_precommit_hooks(self, project_path: str, language: str) -> bool:
        """
        SETUP PHASE: Configure pre-commit hooks for quality enforcement.

        Delegates to AnalysisDelegate.
        """
        return self.analysis_delegate.configure_precommit_hooks(project_path, language)

    def discover_test_config(self, project_path: str, language: str) -> FixResult:
        """
        SETUP PHASE: Discover how to run tests for this project.

        Delegates to AnalysisDelegate.
        """
        return self.analysis_delegate.discover_test_config(project_path, language)

    def create_tests(self, analysis_result, iteration: int) -> FixResult:
        """
        Create tests for projects with no tests (P2 critical failure).

        Delegates to claude_wrapper to:
        1. Find/install appropriate test framework
        2. Create meaningful tests based on code analysis
        3. Set up test infrastructure if needed

        Args:
            analysis_result: AnalysisResult from ProjectAnalyzer
            iteration: Current iteration number (for logging)

        Returns: FixResult with stats
        """
        print(f"\n🧪 Creating tests (iteration {iteration})...")

        # Extract projects needing tests using extractor
        projects_needing_tests = self.issue_extractor.extract_projects_needing_tests(
            analysis_result.results_by_project
        )

        if not projects_needing_tests:
            print("   All projects have sufficient tests")
            return FixResult(success=False)

        print(f"   Found {len(projects_needing_tests)} projects needing tests")

        # Create tests for each project
        tests_created = 0
        for project_info in projects_needing_tests:
            project_name = project_info["project"].split("/")[-1]
            reason = project_info.get("reason", "unknown")
            print(f"\n   Creating tests for {project_name} ({project_info['language']}) - {reason}")

            if self._create_tests_for_project(project_info):
                print("      ✓ Tests created successfully")
                tests_created += 1
            else:
                print("      ✗ Test creation failed")

        print(f"\n   Created tests for {tests_created}/{len(projects_needing_tests)} projects")

        return FixResult(
            fixes_applied=tests_created,
            fixes_attempted=len(projects_needing_tests),
            success=tests_created > 0,
        )

    def _create_tests_for_project(self, project_info: dict) -> bool:
        """Create tests for a single project using claude_wrapper."""
        # Get HEAD commit before test creation
        before_commit = self.commit_verifier.get_head_commit(project_info["project"])

        # Build prompt using prompt manager
        prompt = self.prompt_manager.build_create_tests_prompt(project_info)

        # Get timeout from prompt manager
        timeout = self.prompt_manager.get_timeout("create_tests")

        # Call Claude via JSON protocol
        result = self.claude.query(
            prompt, project_info["project"], timeout, prompt_type="create_test"
        )

        # Verify commit was made
        if result.get("success", False):
            if not self.commit_verifier.verify_fix_committed(
                project_info["project"], before_commit, "creating tests"
            ):
                print("      This indicates tests were not actually created.")
                return False

            # CRITICAL: Verify tests actually pass after creation
            print("      🔍 Validating created tests...")
            adapter = self._get_adapter(project_info["language"])
            if adapter:
                # Run tests to verify they work
                test_result = adapter.run_tests(project_info["project"], strategy="minimal")

                if not test_result.success:
                    print("      ⚠️  Warning: Created tests are failing!")
                    print(
                        f"         Failed: {test_result.tests_failed}, Passed: {test_result.tests_passed}"
                    )
                    print("         Consider running fix_failing_tests phase")
                    # Still return True - tests exist, they just need fixing
                    return True
                print(f"      ✅ Tests validated: {test_result.tests_passed} passing")
                return True

            return True

        return False

    def _get_adapter(self, language: str):
        """Get language adapter instance for running tests."""
        try:
            if language == "python":
                from ..adapters.languages.python_adapter import PythonAdapter

                return PythonAdapter({})
            if language == "javascript":
                from ..adapters.languages.javascript_adapter import JavaScriptAdapter

                return JavaScriptAdapter({})
            if language == "flutter":
                from ..adapters.languages.flutter_adapter import FlutterAdapter

                return FlutterAdapter({})
            if language == "go":
                from ..adapters.languages.go_adapter import GoAdapter

                return GoAdapter({})
        except ImportError:
            print(f"      ⚠️  Could not import {language} adapter for test validation")
            return None
