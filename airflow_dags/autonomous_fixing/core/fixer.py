"""
Issue Fixer - Single Responsibility: Fix detected issues.

Clean, focused module that ONLY handles calling claude_wrapper to fix issues.
No analysis, no scoring, no iteration logic - just fixing.
"""

import subprocess
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
        # Build prompt based on issue type
        if issue['type'] == 'error':
            prompt = f"Fix this {issue['language']} error in {issue['file']}:\n{issue['message']}"
        elif issue['type'] == 'complexity':
            prompt = f"Refactor {issue['file']} to reduce complexity from {issue['complexity']} to below {issue['threshold']}"
        else:
            return False

        try:
            result = subprocess.run(
                [self.python_exec, self.wrapper_path, '--prompt', prompt, '--project', issue['project']],
                capture_output=True,
                text=True,
                timeout=300  # 5 min per fix
            )
            return result.returncode == 0
        except Exception:
            return False

    def _fix_failing_tests(self, test_info: Dict) -> bool:
        """Fix failing tests for a project using claude_wrapper."""
        prompt = (
            f"Fix failing {test_info['language']} tests. "
            f"{test_info['failed']} tests are failing. "
            f"Run tests and fix the code until all tests pass."
        )

        try:
            result = subprocess.run(
                [self.python_exec, self.wrapper_path, '--prompt', prompt, '--project', test_info['project']],
                capture_output=True,
                text=True,
                timeout=600  # 10 min per project
            )
            return result.returncode == 0
        except Exception:
            return False
