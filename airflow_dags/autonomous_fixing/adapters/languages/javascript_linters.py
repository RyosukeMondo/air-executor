"""JavaScript/TypeScript linter execution utilities."""

import subprocess
from typing import Dict, List

from ..error_parser import ErrorParserStrategy


class JavaScriptLinters:
    """Handles execution of JavaScript/TypeScript linting tools."""

    @staticmethod
    def run_eslint(project_path: str) -> List[Dict]:
        """Run ESLint and parse errors using centralized parser."""
        try:
            result = subprocess.run(
                ["npx", "eslint", ".", "--format", "json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Use centralized error parser (SOLID: Single Responsibility)
            return ErrorParserStrategy.parse(
                language="javascript", output=result.stdout, phase="static"
            )

        except Exception:
            return []

    @staticmethod
    def run_tsc(project_path: str) -> List[Dict]:
        """Run TypeScript compiler and parse errors using centralized parser."""
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Use centralized error parser (SOLID: Single Responsibility)
            return ErrorParserStrategy.parse(
                language="typescript", output=result.stdout, phase="static"
            )

        except Exception:
            return []
