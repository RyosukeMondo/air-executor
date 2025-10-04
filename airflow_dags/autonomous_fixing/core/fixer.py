"""
Issue Fixer - Single Responsibility: Fix detected issues.

Clean, focused module that ONLY handles calling claude_wrapper to fix issues.
No analysis, no scoring, no iteration logic - just fixing.
"""

from pathlib import Path
from typing import Dict, List

import yaml

from ..adapters.ai.claude_client import ClaudeClient
from ..adapters.git.git_verifier import GitVerifier
from ..domain.models import FixResult


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

    def __init__(self, config: Dict, debug_logger=None):
        """
        Args:
            config: Configuration dict with wrapper settings
            debug_logger: Optional DebugLogger instance
        """
        self.config = config
        self.wrapper_path = config.get('wrapper', {}).get('path', 'scripts/claude_wrapper.py')
        self.python_exec = config.get('wrapper', {}).get('python_executable', 'python')
        self.debug_logger = debug_logger

        # Load prompts from centralized config
        self.prompts = self._load_prompts()

        # Initialize Claude client with debug logger
        self.claude = ClaudeClient(self.wrapper_path, self.python_exec, debug_logger)

        # Initialize Git verifier for commit validation
        self.git_verifier = GitVerifier()

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

        # Collect issues
        all_issues = self._extract_static_issues(analysis_result.results_by_project, max_issues)

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
            fixes_applied=fixes_applied,
            fixes_attempted=len(all_issues),
            success=fixes_applied > 0
        )

    def fix_test_failures(self, analysis_result, iteration: int, max_projects: int = 5) -> FixResult:
        """
        Fix test failures (P2).

        Args:
            analysis_result: AnalysisResult from ProjectAnalyzer
            iteration: Current iteration number (for logging)
            max_projects: Maximum projects to fix per iteration

        Returns: FixResult with stats
        """
        print(f"\n🔧 Fixing P2 test failures (iteration {iteration})...")

        # Collect failing tests
        failing_tests = self._extract_test_failures(analysis_result.results_by_project, max_projects)

        if not failing_tests:
            print("   No failing tests to fix")
            return FixResult(success=False)

        print(f"   Found {len(failing_tests)} projects with test failures")

        # Fix each project
        fixes_applied = 0
        for test_info in failing_tests:
            print(f"\n   Fixing {test_info['failed']} failing tests in {test_info['project'].split('/')[-1]}")

            if self._fix_failing_tests(test_info):
                print("      ✓ Fixed successfully")
                fixes_applied += 1
            else:
                print("      ✗ Fix failed")

        print(f"\n   Applied fixes to {fixes_applied}/{len(failing_tests)} projects")

        return FixResult(
            fixes_applied=fixes_applied,
            fixes_attempted=len(failing_tests),
            success=fixes_applied > 0
        )

    def _extract_static_issues(self, results_by_project: Dict, max_issues: int) -> List[Dict]:
        """Extract top static issues from analysis results."""
        all_issues = []

        for project_key, analysis in results_by_project.items():
            lang_name, project_path = project_key.split(':', 1)

            # Add errors (top 5 per project)
            for error in analysis.errors[:5]:
                all_issues.append({
                    'project': project_path,
                    'language': lang_name,
                    'type': 'error',
                    'file': error.get('file', ''),
                    'line': error.get('line', 0),
                    'message': error.get('message', '')
                })

            # Add complexity violations (top 3 per project)
            for violation in analysis.complexity_violations[:3]:
                all_issues.append({
                    'project': project_path,
                    'language': lang_name,
                    'type': 'complexity',
                    'file': violation.get('file', ''),
                    'complexity': violation.get('complexity', 0),
                    'threshold': violation.get('threshold', 0)
                })

        return all_issues[:max_issues]

    def _extract_test_failures(self, results_by_project: Dict, max_projects: int) -> List[Dict]:
        """Extract failing tests from analysis results."""
        failing_tests = []

        for project_key, analysis in results_by_project.items():
            lang_name, project_path = project_key.split(':', 1)

            if analysis.tests_failed > 0:
                failing_tests.append({
                    'project': project_path,
                    'language': lang_name,
                    'failed': analysis.tests_failed,
                    'total': analysis.tests_passed + analysis.tests_failed
                })

        return failing_tests[:max_projects]

    def _fix_single_issue(self, issue: Dict) -> bool:
        """Fix a single static issue using claude_wrapper."""
        # Get HEAD commit before fix
        before_commit = self.git_verifier.get_head_commit(issue['project'])

        # Build prompt from config template
        if issue['type'] == 'error':
            template = self.prompts['static_issues']['error']['template']
            prompt = template.format(
                language=issue['language'],
                file=issue['file'],
                message=issue['message']
            )
        elif issue['type'] == 'complexity':
            template = self.prompts['static_issues']['complexity']['template']
            prompt = template.format(
                file=issue['file'],
                complexity=issue['complexity'],
                threshold=issue['threshold']
            )
        else:
            return False

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('fix_static_issue', 300)

        # Determine prompt type for logging
        prompt_type = 'fix_error' if issue['type'] == 'error' else 'fix_complexity'

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, issue['project'], timeout, prompt_type=prompt_type)

        # Verify commit was made
        if result.get('success', False):
            verification = self.git_verifier.verify_commit_made(
                issue['project'],
                before_commit,
                f"fixing {issue['type']}"
            )

            if not verification['verified']:
                print("      ❌ ABORT: Claude said success but no commit detected!")
                print(f"      {verification['message']}")
                print("      This indicates a problem with claude_wrapper or the fix.")
                return False

            print(f"      ✅ Verified: {verification['message']}")
            return True

        return False

    def _fix_failing_tests(self, test_info: Dict) -> bool:
        """Fix failing tests for a project using claude_wrapper."""
        # Get HEAD commit before fix
        before_commit = self.git_verifier.get_head_commit(test_info['project'])

        # Build prompt from config template
        template = self.prompts['tests']['fix_failures']['template']
        prompt = template.format(
            language=test_info['language'],
            failed=test_info['failed'],
            total=test_info['total']
        )

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('fix_test_failure', 600)

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, test_info['project'], timeout, prompt_type='fix_test')

        # Verify commit was made
        if result.get('success', False):
            verification = self.git_verifier.verify_commit_made(
                test_info['project'],
                before_commit,
                "fixing tests"
            )

            if not verification['verified']:
                print("      ❌ ABORT: Claude said success but no commit detected!")
                print(f"      {verification['message']}")
                return False

            print(f"      ✅ Verified: {verification['message']}")
            return True

        return False

    def analyze_static(self, project_path: str, language: str) -> Dict:
        """
        ANALYSIS PHASE: Static code quality analysis via claude_wrapper.

        Delegates to claude_wrapper to:
        1. Run linters/analyzers (eslint, pylint, flutter analyze, etc.)
        2. Analyze errors, warnings, complexity, file sizes
        3. Assess overall health with reasoning
        4. Save structured report to config/analysis-cache/

        Args:
            project_path: Path to project
            language: Project language

        Returns: Dict with analysis results (from YAML)
        """
        project_name = Path(project_path).name
        cache_path = Path('config/analysis-cache') / f'{project_name}-static.yaml'

        # Check if recently analyzed (< 5 min old)
        if cache_path.exists():
            import time
            age_seconds = time.time() - cache_path.stat().st_mtime
            if age_seconds < 300:  # 5 minutes
                print(f"   ✓ Using cached analysis ({int(age_seconds)}s old)")
                import yaml
                with open(cache_path) as f:
                    return yaml.safe_load(f)

        print(f"\n🔍 Analyzing {project_name} static code quality...")

        # Build prompt from config template
        template = self.prompts['analysis']['static_analysis']['template']
        prompt = template.format(
            language=language,
            project_name=project_name,
            timestamp="$(date -Iseconds)"
        )

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('analyze_static', 300)

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, project_path, timeout, prompt_type='analysis')

        if result['success'] and cache_path.exists():
            print(f"   ✓ Analysis complete, saved to {cache_path}")
            import yaml
            with open(cache_path) as f:
                return yaml.safe_load(f)
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"   ✗ Analysis failed: {error_msg}")
            # Return empty analysis
            return {
                'health': {'overall_score': 0.0},
                'errors': {'count': 0},
                'warnings': {'count': 0}
            }

    def configure_precommit_hooks(self, project_path: str, language: str) -> bool:
        """
        SETUP PHASE: Configure pre-commit hooks for quality enforcement.

        This shifts quality gates from AI prompts to enforced tooling:
        - AI configures hooks once
        - Hooks enforce quality on every commit
        - AI cannot bypass hooks (must fix issues)

        Args:
            project_path: Path to project
            language: Project language

        Returns: True if hooks configured successfully
        """
        project_name = Path(project_path).name
        cache_path = Path('config/precommit-cache') / f'{project_name}-hooks.yaml'

        # Ensure cache directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if already configured (< 7 days old)
        if cache_path.exists():
            import time
            age_seconds = time.time() - cache_path.stat().st_mtime
            if age_seconds < 604800:  # 7 days
                print(f"   ✓ Pre-commit hooks already configured ({int(age_seconds/86400)} days ago)")
                import yaml
                with open(cache_path) as f:
                    config = yaml.safe_load(f)
                    return config.get('hook_framework', {}).get('installed', False)

        print(f"\n🔧 Configuring pre-commit hooks for {project_name}...")

        # Build prompt from config template
        template = self.prompts['setup']['configure_precommit_hooks']['template']
        prompt = template.format(
            language=language,
            project_name=project_name
        )

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('configure_hooks', 600)

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, project_path, timeout, prompt_type='configure_hooks')

        if result['success'] and cache_path.exists():
            print(f"   ✓ Pre-commit hooks configured and saved to {cache_path}")
            return True
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"   ⚠️  Hook configuration failed: {error_msg}")
            print("   Continuing without pre-commit enforcement (less robust)")
            return False

    def discover_test_config(self, project_path: str, language: str) -> FixResult:
        """
        SETUP PHASE: Discover how to run tests for this project.

        Delegates to claude_wrapper to:
        1. Analyze project structure
        2. Detect package manager, test framework, test locations
        3. Try running tests to verify
        4. Save discovered config to config/test-cache/

        Args:
            project_path: Path to project
            language: Project language

        Returns: FixResult with stats
        """
        project_name = Path(project_path).name
        cache_path = Path('config/test-cache') / f'{project_name}-tests.yaml'

        # Check if already discovered
        if cache_path.exists():
            print(f"   ✓ Test config already exists: {cache_path}")
            return FixResult(success=False)  # No discovery needed

        print(f"\n🔍 SETUP: Discovering test configuration for {project_name}...")

        # Build prompt from config template
        template = self.prompts['setup']['discover_tests']['template']
        prompt = template.format(
            language=language,
            project_name=project_name,
            project_path=project_path,
            timestamp="$(date -Iseconds)"
        )

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('discover_tests', 600)

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, project_path, timeout, prompt_type='discover_tests')

        if result['success'] and cache_path.exists():
            print(f"   ✓ Test config discovered and saved to {cache_path}")
            return FixResult(fixes_applied=1, fixes_attempted=1, success=True)
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"   ✗ Test discovery failed: {error_msg}")
            return FixResult(fixes_applied=0, fixes_attempted=1, success=False)

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

        # Find projects with 0 tests OR low coverage
        projects_needing_tests = []
        for project_key, analysis in analysis_result.results_by_project.items():
            lang_name, project_path = project_key.split(':', 1)
            total_tests = analysis.tests_passed + analysis.tests_failed

            # Check if project needs tests
            needs_tests = False
            reason = ""

            if total_tests == 0:
                needs_tests = True
                reason = "no tests"
            elif hasattr(analysis, 'coverage_percentage') and analysis.coverage_percentage:
                # If coverage exists and is below threshold (e.g., 60%)
                if analysis.coverage_percentage < 60.0:
                    needs_tests = True
                    reason = f"low coverage ({analysis.coverage_percentage:.1f}%)"

            if needs_tests:
                projects_needing_tests.append({
                    'project': project_path,
                    'language': lang_name,
                    'reason': reason
                })

        if not projects_needing_tests:
            print("   All projects have sufficient tests")
            return FixResult(success=False)

        print(f"   Found {len(projects_needing_tests)} projects needing tests")

        # Create tests for each project
        tests_created = 0
        for project_info in projects_needing_tests:
            project_name = project_info['project'].split('/')[-1]
            reason = project_info.get('reason', 'unknown')
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
            success=tests_created > 0
        )

    def _create_tests_for_project(self, project_info: Dict) -> bool:
        """Create tests for a single project using claude_wrapper."""
        # Get HEAD commit before test creation
        before_commit = self.git_verifier.get_head_commit(project_info['project'])

        # Build prompt from config template
        template = self.prompts['tests']['create_tests']['template']
        prompt = template.format(language=project_info['language'])

        # Check for language-specific framework hints
        lang_overrides = self.prompts.get('language_overrides', {}).get(project_info['language'], {})
        if 'create_tests' in lang_overrides and 'framework_hint' in lang_overrides['create_tests']:
            prompt += f"\n\nFramework tip: {lang_overrides['create_tests']['framework_hint']}"

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('create_tests', 900)

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, project_info['project'], timeout, prompt_type='create_test')

        # Verify commit was made
        if result.get('success', False):
            verification = self.git_verifier.verify_commit_made(
                project_info['project'],
                before_commit,
                "creating tests"
            )

            if not verification['verified']:
                print("      ❌ ABORT: Claude said success but no commit detected!")
                print(f"      {verification['message']}")
                print("      This indicates tests were not actually created.")
                return False

            print(f"      ✅ Verified: {verification['message']}")

            # CRITICAL: Verify tests actually pass after creation
            print("      🔍 Validating created tests...")
            adapter = self._get_adapter(project_info['language'])
            if adapter:
                # Run tests to verify they work
                test_result = adapter.run_tests(project_info['project'], strategy='minimal')

                if not test_result.success:
                    print("      ⚠️  Warning: Created tests are failing!")
                    print(f"         Failed: {test_result.tests_failed}, Passed: {test_result.tests_passed}")
                    print("         Consider running fix_failing_tests phase")
                    # Still return True - tests exist, they just need fixing
                    return True
                else:
                    print(f"      ✅ Tests validated: {test_result.tests_passed} passing")
                    return True

            return True

        return False

    def _get_adapter(self, language: str):
        """Get language adapter instance for running tests."""
        try:
            if language == 'python':
                from ..adapters.languages.python_adapter import PythonAdapter
                return PythonAdapter({})
            elif language == 'javascript':
                from ..adapters.languages.javascript_adapter import JavaScriptAdapter
                return JavaScriptAdapter({})
            elif language == 'flutter':
                from ..adapters.languages.flutter_adapter import FlutterAdapter
                return FlutterAdapter({})
            elif language == 'go':
                from ..adapters.languages.go_adapter import GoAdapter
                return GoAdapter({})
        except ImportError:
            print(f"      ⚠️  Could not import {language} adapter for test validation")
            return None

    def _load_prompts(self) -> Dict:
        """Load prompts from centralized config file."""
        # Try to find prompts.yaml in config directory
        possible_paths = [
            Path(__file__).parent.parent.parent / 'config' / 'prompts.yaml',  # From core/
            Path('config/prompts.yaml'),  # From project root
            Path(__file__).parent.parent / 'config' / 'prompts.yaml',  # Alternative
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, 'r') as f:
                    return yaml.safe_load(f)

        # Fallback: return minimal default prompts if config not found
        print("⚠️  Warning: prompts.yaml not found, using fallback prompts")
        return {
            'static_issues': {
                'error': {'template': 'Fix this {language} error in {file}:\n{message}'},
                'complexity': {'template': 'Refactor {file} to reduce complexity from {complexity} to below {threshold}'}
            },
            'tests': {
                'fix_failures': {'template': 'Fix failing {language} tests. {failed}/{total} tests failing.'},
                'create_tests': {'template': 'This {language} project has NO TESTS. Create initial test suite.'}
            },
            'timeouts': {
                'fix_static_issue': 300,
                'fix_test_failure': 600,
                'create_tests': 900
            }
        }
