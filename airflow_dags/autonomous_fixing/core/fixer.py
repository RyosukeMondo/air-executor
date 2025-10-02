"""
Issue Fixer - Single Responsibility: Fix detected issues.

Clean, focused module that ONLY handles calling claude_wrapper to fix issues.
No analysis, no scoring, no iteration logic - just fixing.
"""

import subprocess
import yaml
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class FixResult:
    """Result from fixing issues."""
    fixes_applied: int = 0
    fixes_attempted: int = 0
    success: bool = False


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

    def __init__(self, config: Dict):
        """
        Args:
            config: Configuration dict with wrapper settings
        """
        self.config = config
        self.wrapper_path = config.get('wrapper', {}).get('path', 'scripts/claude_wrapper.py')
        self.python_exec = config.get('wrapper', {}).get('python_executable', 'python')

        # Load prompts from centralized config
        self.prompts = self._load_prompts()

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
                print(f"      ✓ Fixed successfully")
                fixes_applied += 1
            else:
                print(f"      ✗ Fix failed")

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
                print(f"      ✓ Fixed successfully")
                fixes_applied += 1
            else:
                print(f"      ✗ Fix failed")

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

        try:
            result = subprocess.run(
                [self.python_exec, self.wrapper_path, '--prompt', prompt, '--project', issue['project']],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0
        except Exception:
            return False

    def _fix_failing_tests(self, test_info: Dict) -> bool:
        """Fix failing tests for a project using claude_wrapper."""
        # Build prompt from config template
        template = self.prompts['tests']['fix_failures']['template']
        prompt = template.format(
            language=test_info['language'],
            failed=test_info['failed'],
            total=test_info['total']
        )

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('fix_test_failure', 600)

        try:
            result = subprocess.run(
                [self.python_exec, self.wrapper_path, '--prompt', prompt, '--project', test_info['project']],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0
        except Exception:
            return False

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

        # Find projects with 0 tests
        projects_needing_tests = []
        for project_key, analysis in analysis_result.results_by_project.items():
            lang_name, project_path = project_key.split(':', 1)
            total_tests = analysis.tests_passed + analysis.tests_failed

            if total_tests == 0:
                projects_needing_tests.append({
                    'project': project_path,
                    'language': lang_name
                })

        if not projects_needing_tests:
            print("   All projects have tests")
            return FixResult(success=False)

        print(f"   Found {len(projects_needing_tests)} projects needing tests")

        # Create tests for each project
        tests_created = 0
        for project_info in projects_needing_tests:
            print(f"\n   Creating tests for {project_info['project'].split('/')[-1]} ({project_info['language']})")

            if self._create_tests_for_project(project_info):
                print(f"      ✓ Tests created successfully")
                tests_created += 1
            else:
                print(f"      ✗ Test creation failed")

        print(f"\n   Created tests for {tests_created}/{len(projects_needing_tests)} projects")

        return FixResult(
            fixes_applied=tests_created,
            fixes_attempted=len(projects_needing_tests),
            success=tests_created > 0
        )

    def _create_tests_for_project(self, project_info: Dict) -> bool:
        """Create tests for a single project using claude_wrapper."""
        # Build prompt from config template
        template = self.prompts['tests']['create_tests']['template']
        prompt = template.format(language=project_info['language'])

        # Check for language-specific framework hints
        lang_overrides = self.prompts.get('language_overrides', {}).get(project_info['language'], {})
        if 'create_tests' in lang_overrides and 'framework_hint' in lang_overrides['create_tests']:
            prompt += f"\n\nFramework tip: {lang_overrides['create_tests']['framework_hint']}"

        # Get timeout from config
        timeout = self.prompts.get('timeouts', {}).get('create_tests', 900)

        try:
            result = subprocess.run(
                [self.python_exec, self.wrapper_path, '--prompt', prompt, '--project', project_info['project']],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0
        except Exception:
            return False

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
