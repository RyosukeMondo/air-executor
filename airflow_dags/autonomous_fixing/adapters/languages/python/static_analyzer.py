"""Python static analysis (linting, complexity)."""

import subprocess
import json
import re
from typing import List, Dict
from pathlib import Path
from .detector import PythonProjectDetector
from ....domain.models import AnalysisResult


class PythonStaticAnalyzer:
    """Runs static analysis on Python code (pylint, mypy)."""

    def __init__(self, config: Dict):
        self.config = config
        self.complexity_threshold = config.get('complexity_threshold', 10)
        self.max_file_lines = config.get('max_file_lines', 500)
        self.detector = PythonProjectDetector()

    def analyze(self, project_path: str) -> AnalysisResult:
        """
        Run static analysis (linting, complexity, file sizes).

        Args:
            project_path: Path to project

        Returns:
            AnalysisResult with static analysis data
        """
        import time
        start_time = time.time()

        result = AnalysisResult(
            language='python',
            phase='static',
            project_path=project_path
        )

        try:
            errors = []

            # Run linters in parallel
            linters = self.config.get('linters', ['pylint', 'mypy'])

            if 'pylint' in linters:
                errors.extend(self._run_pylint(project_path))

            if 'mypy' in linters:
                errors.extend(self._run_mypy(project_path))

            result.errors = errors
            result.file_size_violations = self._check_file_sizes(project_path)
            result.complexity_violations = self._check_complexity(project_path)

            result.success = len(result.errors) == 0
            result.execution_time = time.time() - start_time

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def _run_pylint(self, project_path: str) -> List[Dict]:
        """Run pylint and parse errors."""
        try:
            result = subprocess.run(
                ['pylint', '.', '--output-format=json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse JSON output
            if result.stdout:
                lint_results = json.loads(result.stdout)
                return [
                    {
                        'severity': item.get('type', 'error'),
                        'file': item.get('path', ''),
                        'line': item.get('line', 0),
                        'column': item.get('column', 0),
                        'message': item.get('message', ''),
                        'code': item.get('symbol', '')
                    }
                    for item in lint_results
                    if item.get('type') in ('error', 'fatal')
                ]

        except Exception:
            pass

        return []

    def _run_mypy(self, project_path: str) -> List[Dict]:
        """Run mypy and parse errors."""
        try:
            result = subprocess.run(
                ['mypy', '.', '--show-error-codes'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            errors = []
            # Mypy format: file.py:line: error: message [error-code]
            pattern = r'(.+\.py):(\d+):\s*(error|warning):\s*(.+?)\s*\[(.+?)\]'
            for match in re.finditer(pattern, result.stdout):
                errors.append({
                    'severity': match.group(3),
                    'file': match.group(1),
                    'line': int(match.group(2)),
                    'column': 0,
                    'message': match.group(4),
                    'code': match.group(5)
                })

            return errors

        except Exception:
            pass

        return []

    def _check_file_sizes(self, project_path: str) -> List[Dict]:
        """Check for files exceeding max_file_lines threshold."""
        violations = []
        project = Path(project_path)

        for file_path in self.detector.get_source_files(project):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)

                if line_count > self.max_file_lines:
                    violations.append({
                        'file': str(file_path),
                        'lines': line_count,
                        'threshold': self.max_file_lines,
                        'message': f'File has {line_count} lines (max: {self.max_file_lines})'
                    })
            except Exception:
                continue

        return violations

    def _check_complexity(self, project_path: str) -> List[Dict]:
        """Check for high complexity files."""
        violations = []
        project = Path(project_path)

        for file_path in self.detector.get_source_files(project):
            complexity = self._calculate_complexity(str(file_path))
            if complexity > self.complexity_threshold:
                violations.append({
                    'file': str(file_path),
                    'complexity': complexity,
                    'threshold': self.complexity_threshold,
                    'message': f'Complexity {complexity} exceeds threshold {self.complexity_threshold}'
                })

        return violations

    def _calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using radon."""
        try:
            # Use radon for accurate complexity
            result = subprocess.run(
                ['radon', 'cc', file_path, '-s', '-n', 'A'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parse radon output: "A 1:0 ClassName.method_name - A (1)"
            max_complexity = 0
            for match in re.finditer(r'\((\d+)\)', result.stdout):
                complexity = int(match.group(1))
                max_complexity = max(max_complexity, complexity)

            return max_complexity

        except Exception:
            # Fallback to simple heuristic
            return self._simple_complexity(file_path)

    def _simple_complexity(self, file_path: str) -> int:
        """Simple complexity heuristic (fallback)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            complexity = 1
            complexity += content.count(' if ')
            complexity += content.count(' for ')
            complexity += content.count(' while ')
            complexity += content.count(' and ')
            complexity += content.count(' or ')
            complexity += content.count('except ')

            return complexity

        except Exception:
            return 0
