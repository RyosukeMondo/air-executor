"""Python linter execution utilities."""

import json
import re
import shutil
import subprocess
from pathlib import Path


class PythonLinters:
    """Handles execution of Python linting tools."""

    @staticmethod
    def run_ruff(project_path: str) -> list[dict]:
        """Run ruff and parse errors."""
        try:
            # Find ruff executable (may be in venv)
            ruff_cmd = shutil.which("ruff")
            if not ruff_cmd:
                # Try venv location
                import sys

                if hasattr(sys, "prefix"):
                    venv_ruff = Path(sys.prefix) / "bin" / "ruff"
                    if venv_ruff.exists():
                        ruff_cmd = str(venv_ruff)

            if not ruff_cmd:
                return []  # Ruff not available

            result = subprocess.run(
                [ruff_cmd, "check", ".", "--output-format=json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Parse JSON output (ruff returns non-zero if errors found)
            if result.stdout:
                lint_results = json.loads(result.stdout)
                return [
                    {
                        "severity": "error",
                        "file": item.get("filename", ""),
                        "line": item.get("location", {}).get("row", 0),
                        "column": item.get("location", {}).get("column", 0),
                        "message": item.get("message", ""),
                        "code": item.get("code", ""),
                    }
                    for item in lint_results
                ]

        except Exception:
            pass

        return []

    @staticmethod
    def run_pylint(project_path: str) -> list[dict]:
        """Run pylint and parse errors."""
        try:
            result = subprocess.run(
                ["pylint", ".", "--output-format=json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Parse JSON output
            if result.stdout:
                lint_results = json.loads(result.stdout)
                return [
                    {
                        "severity": item.get("type", "error"),
                        "file": item.get("path", ""),
                        "line": item.get("line", 0),
                        "column": item.get("column", 0),
                        "message": item.get("message", ""),
                        "code": item.get("symbol", ""),
                    }
                    for item in lint_results
                    if item.get("type") in ("error", "fatal")
                ]

        except Exception:
            pass

        return []

    @staticmethod
    def run_mypy(project_path: str) -> list[dict]:
        """Run mypy and parse errors."""
        try:
            result = subprocess.run(
                ["mypy", ".", "--show-error-codes"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            errors = []
            # Mypy format: file.py:line: error: message [error-code]
            pattern = r"(.+\.py):(\d+):\s*(error|warning):\s*(.+?)\s*\[(.+?)\]"
            for match in re.finditer(pattern, result.stdout):
                errors.append(
                    {
                        "severity": match.group(3),
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "column": 0,
                        "message": match.group(4),
                        "code": match.group(5),
                    }
                )

            return errors

        except Exception:
            pass

        return []
