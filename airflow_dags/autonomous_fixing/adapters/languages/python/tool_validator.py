"""Python tool validation."""

import subprocess
import shutil
import re
from typing import List
from pathlib import Path
from ....domain.models import ToolValidationResult


class PythonToolValidator:
    """Validates Python toolchain availability."""

    def __init__(self, config: dict):
        self.config = config

    def validate_tools(self) -> List[ToolValidationResult]:
        """
        Validate all required tools are available.

        Returns:
            List of ToolValidationResult for each required tool
        """
        results = []

        # 1. Python itself
        results.append(self._validate_python())

        # 2. Linters (from config)
        linters = self.config.get('linters', ['pylint', 'mypy'])
        for linter in linters:
            results.append(self._validate_tool(
                linter,
                version_flag='--version',
                fix_suggestion=f'Install {linter}: pip install {linter}'
            ))

        # 3. Test runner
        test_runner = self.config.get('test_runner', 'pytest')
        results.append(self._validate_tool(
            test_runner,
            version_flag='--version',
            fix_suggestion=f'Install {test_runner}: pip install {test_runner}'
        ))

        # 4. Coverage tool (optional)
        results.append(self._validate_tool(
            'coverage',
            version_flag='--version',
            fix_suggestion='Install coverage: pip install coverage',
            optional=True
        ))

        return results

    def _validate_python(self) -> ToolValidationResult:
        """Validate Python installation."""
        python_cmd = shutil.which('python') or shutil.which('python3')

        if not python_cmd:
            return ToolValidationResult(
                tool_name='python',
                available=False,
                error_message='Python not found in PATH',
                fix_suggestion='Install Python: https://python.org/downloads'
            )

        try:
            result = subprocess.run(
                [python_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            version_match = re.search(r'Python ([\d.]+)', result.stdout + result.stderr)
            version = version_match.group(1) if version_match else 'unknown'

            return ToolValidationResult(
                tool_name='python',
                available=True,
                version=version,
                path=python_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name='python',
                available=False,
                path=python_cmd,
                error_message=f'Python found but failed to run: {e}'
            )

    def _validate_tool(self, tool_name: str, version_flag: str, fix_suggestion: str, optional: bool = False) -> ToolValidationResult:
        """Generic tool validation."""
        # First check PATH
        tool_cmd = shutil.which(tool_name)

        # If not in PATH, check if running in venv and look there
        if not tool_cmd:
            import sys
            if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
                # We're in a venv, check venv bin directory
                venv_bin = Path(sys.prefix) / 'bin' / tool_name
                if venv_bin.exists():
                    tool_cmd = str(venv_bin)

        if not tool_cmd:
            return ToolValidationResult(
                tool_name=tool_name,
                available=False,
                error_message=f'{tool_name} not found in PATH' if not optional else f'{tool_name} not found (optional)',
                fix_suggestion=fix_suggestion if not optional else None
            )

        try:
            result = subprocess.run(
                [tool_cmd, version_flag],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Try to extract version from output
            output = result.stdout + result.stderr
            # Match version patterns like "1.2.3" or "version 1.2.3"
            version_match = re.search(r'(?:version\s+)?(\d+\.\d+(?:\.\d+)?)', output, re.IGNORECASE)
            version = version_match.group(1) if version_match else 'unknown'

            return ToolValidationResult(
                tool_name=tool_name,
                available=True,
                version=version,
                path=tool_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name=tool_name,
                available=False,
                path=tool_cmd,
                error_message=f'{tool_name} found but failed to run: {e}'
            )
