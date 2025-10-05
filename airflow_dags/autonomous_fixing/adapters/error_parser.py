"""
Error Parser - Single Responsibility: Parse linter/compiler error output

SOLID Principles:
- Single Responsibility: ONLY parses error messages, nothing else
- Open/Closed: Open for new parsers, closed for modification
- Liskov Substitution: All parsers return same ErrorList interface
- Interface Segregation: Simple, focused interface
- Dependency Inversion: Depends on abstractions, not implementations

KISS: Simple strategy pattern with fallback
SSOT: Single source of truth for error parsing logic
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedError:
    """Parsed error - SSOT for error structure."""

    file: str
    line: int
    column: int
    severity: str  # 'error' | 'warning' | 'info'
    message: str
    code: str | None = None


class ErrorParser(ABC):
    """Abstract base for error parsers."""

    @abstractmethod
    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """
        Parse error output and return structured errors.

        Args:
            output: Raw command output (stdout + stderr)
            phase: 'static' | 'tests' | 'coverage' | 'e2e'
            output_file: Optional path to structured output file (JSON)

        Returns:
            List of ParsedError if parsing successful, empty list otherwise
        """
        pass


# =============================================================================
# JavaScript/TypeScript Parsers
# =============================================================================


class ESLintJSONParser(ErrorParser):
    """Parse ESLint JSON output - PREFERRED."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse ESLint --format json output."""
        errors = []

        try:
            # Try file first
            if _output_file and _output_file.exists():
                with open(_output_file, encoding="utf-8") as f:
                    data = json.load(f)
            else:
                # Try parsing JSON from output
                data = json.loads(output)

            # ESLint JSON: [{ filePath, messages: [{ line, column, severity, message, ruleId }] }]
            for file_result in data:
                file_path = file_result.get("filePath", "")
                for msg in file_result.get("messages", []):
                    errors.append(
                        ParsedError(
                            file=file_path,
                            line=msg.get("line", 0),
                            column=msg.get("column", 0),
                            severity="error" if msg.get("severity") == 2 else "warning",
                            message=msg.get("message", ""),
                            code=msg.get("ruleId"),
                        )
                    )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


class ESLintTextParser(ErrorParser):
    """Parse ESLint text output - FALLBACK."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse ESLint stylish/compact format."""
        errors = []

        try:
            # ESLint format: /path/file.js:10:5: message (rule-name)
            pattern = r"(.+?):(\d+):(\d+):\s*(error|warning)\s+(.+?)(?:\s+\((.+?)\))?$"

            for match in re.finditer(pattern, output, re.MULTILINE):
                errors.append(
                    ParsedError(
                        file=match.group(1),
                        line=int(match.group(2)),
                        column=int(match.group(3)),
                        severity=match.group(4),
                        message=match.group(5).strip(),
                        code=match.group(6) if match.group(6) else None,
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


class TypeScriptParser(ErrorParser):
    """Parse TypeScript compiler (tsc) output."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse tsc error format."""
        errors = []

        try:
            # TSC format: file.ts(10,5): error TS2304: message
            pattern = r"(.+?)\((\d+),(\d+)\):\s*(error|warning)\s+TS(\d+):\s*(.+?)$"

            for match in re.finditer(pattern, output, re.MULTILINE):
                errors.append(
                    ParsedError(
                        file=match.group(1),
                        line=int(match.group(2)),
                        column=int(match.group(3)),
                        severity=match.group(4),
                        message=match.group(6).strip(),
                        code=f"TS{match.group(5)}",
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


class JestTestErrorParser(ErrorParser):
    """Parse Jest/Vitest test failures."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse Jest test failure output."""
        errors = []

        try:
            # Jest format: FAIL src/file.test.js
            pattern = r"FAIL\s+(.+\.(?:test|spec)\.[jt]sx?)"

            for match in re.finditer(pattern, output):
                errors.append(
                    ParsedError(
                        file=match.group(1),
                        line=0,
                        column=0,
                        severity="error",
                        message="Test suite failed",
                        code=None,
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


# =============================================================================
# Python Parsers
# =============================================================================


class PylintJSONParser(ErrorParser):
    """Parse pylint JSON output - PREFERRED."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse pylint --output-format=json."""
        errors = []

        try:
            if _output_file and _output_file.exists():
                with open(_output_file, encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(output)

            # Pylint JSON: [{ path, line, column, type, message, symbol }]
            for item in data:
                severity = "error" if item.get("type") in ("error", "fatal") else "warning"
                errors.append(
                    ParsedError(
                        file=item.get("path", ""),
                        line=item.get("line", 0),
                        column=item.get("column", 0),
                        severity=severity,
                        message=item.get("message", ""),
                        code=item.get("symbol"),
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


class PylintTextParser(ErrorParser):
    """Parse pylint text output - FALLBACK."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse pylint parseable format."""
        errors = []

        try:
            # Pylint format: file.py:10: [E0001(syntax-error), ] message
            pattern = r"(.+?):(\d+):\s*\[([EWRCIF])(\d+)\((.+?)\).*?\]\s*(.+?)$"

            for match in re.finditer(pattern, output, re.MULTILINE):
                severity_map = {
                    "E": "error",
                    "F": "error",
                    "W": "warning",
                    "R": "info",
                    "C": "info",
                    "I": "info",
                }
                errors.append(
                    ParsedError(
                        file=match.group(1),
                        line=int(match.group(2)),
                        column=0,
                        severity=severity_map.get(match.group(3), "warning"),
                        message=match.group(6).strip(),
                        code=match.group(5),
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


class MypyParser(ErrorParser):
    """Parse mypy type checker output."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse mypy error format."""
        errors = []

        try:
            # Mypy format: file.py:10: error: message [error-code]
            pattern = r"(.+?):(\d+):\s*(error|warning|note):\s*(.+?)(?:\s+\[(.+?)\])?$"

            for match in re.finditer(pattern, output, re.MULTILINE):
                errors.append(
                    ParsedError(
                        file=match.group(1),
                        line=int(match.group(2)),
                        column=0,
                        severity=match.group(3) if match.group(3) != "note" else "info",
                        message=match.group(4).strip(),
                        code=match.group(5) if match.group(5) else None,
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


class PytestErrorParser(ErrorParser):
    """Parse pytest test failures."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse pytest failure output."""
        errors = []

        try:
            # Pytest format: test_file.py::test_name FAILED
            pattern = r"(.+\.py)::(.+?)\s+FAILED"

            for match in re.finditer(pattern, output):
                errors.append(
                    ParsedError(
                        file=match.group(1),
                        line=0,
                        column=0,
                        severity="error",
                        message=f"Test failed: {match.group(2)}",
                        code=None,
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


# =============================================================================
# Go Parsers
# =============================================================================


class GoVetParser(ErrorParser):
    """Parse go vet output."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse go vet error format."""
        errors = []

        try:
            # Go vet format: file.go:10:5: message
            pattern = r"(.+\.go):(\d+):(\d+):\s*(.+?)$"

            for match in re.finditer(pattern, output, re.MULTILINE):
                errors.append(
                    ParsedError(
                        file=match.group(1),
                        line=int(match.group(2)),
                        column=int(match.group(3)),
                        severity="error",
                        message=match.group(4).strip(),
                        code=None,
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


class GoTestErrorParser(ErrorParser):
    """Parse go test failures."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse go test error format."""
        errors = []

        try:
            # Go test format: --- FAIL: TestName (0.00s)
            pattern = r"--- FAIL:\s+(\w+)"

            for match in re.finditer(pattern, output):
                errors.append(
                    ParsedError(
                        file="",
                        line=0,
                        column=0,
                        severity="error",
                        message=f"Test failed: {match.group(1)}",
                        code=None,
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


# =============================================================================
# Flutter/Dart Parsers
# =============================================================================


class FlutterAnalyzeParser(ErrorParser):
    """Parse flutter analyze output."""

    def parse(
        self, output: str, _phase: str, _output_file: Path | None = None
    ) -> list[ParsedError]:
        """Parse flutter analyze format."""
        errors = []

        try:
            # Flutter analyze format: error • message • file:line:col • error_code
            pattern = r"(error|warning|info)\s*•\s*(.+?)\s*•\s*(.+?):(\d+):(\d+)\s*•\s*(\w+)?"

            for match in re.finditer(pattern, output):
                errors.append(
                    ParsedError(
                        file=match.group(3).strip(),
                        line=int(match.group(4)),
                        column=int(match.group(5)),
                        severity=match.group(1),
                        message=match.group(2).strip(),
                        code=match.group(6) if match.group(6) else None,
                    )
                )

            return errors

        except Exception:  # noqa: BLE001 - Parsing errors should not break analysis
            # If parsing fails for any reason, return empty list (no errors found)
            return []


# =============================================================================
# Parser Strategy - SSOT for Parser Selection
# =============================================================================


class ErrorParserStrategy:
    """
    Strategy for parsing errors with fallback.

    SOLID: Strategy pattern for parser selection
    KISS: Simple try-preferred-then-fallback logic
    SSOT: Single place to configure parsers per language/phase
    """

    # Parser configuration - SSOT
    PARSERS = {
        "javascript": {
            "static": {
                "eslint_json": ESLintJSONParser(),
                "eslint_text": ESLintTextParser(),
                "typescript": TypeScriptParser(),
            },
            "tests": {"jest": JestTestErrorParser()},
        },
        "typescript": {
            "static": {
                "eslint_json": ESLintJSONParser(),
                "eslint_text": ESLintTextParser(),
                "typescript": TypeScriptParser(),
            },
            "tests": {"jest": JestTestErrorParser()},
        },
        "python": {
            "static": {
                "pylint_json": PylintJSONParser(),
                "pylint_text": PylintTextParser(),
                "mypy": MypyParser(),
            },
            "tests": {"pytest": PytestErrorParser()},
        },
        "go": {"static": {"go_vet": GoVetParser()}, "tests": {"go_test": GoTestErrorParser()}},
        "flutter": {"static": {"flutter_analyze": FlutterAnalyzeParser()}},
    }

    @classmethod
    def parse(
        cls, language: str, output: str, phase: str, output_file: Path | None = None
    ) -> list[dict]:
        """
        Parse error output using all available parsers.

        Args:
            language: Project language (javascript, python, go, flutter)
            output: Raw command output (stdout + stderr)
            phase: 'static' | 'tests' | 'coverage' | 'e2e'
            output_file: Optional path to structured output file

        Returns:
            List of error dicts (converted from ParsedError for compatibility)
        """
        parsers = cls.PARSERS.get(language.lower(), {}).get(phase, {})
        if not parsers:
            return []

        all_errors = []

        # Try all parsers and collect results
        for parser_name, parser in parsers.items():
            try:
                errors = parser.parse(output, phase, output_file)
                all_errors.extend(errors)
            except Exception:
                continue

        # Convert ParsedError to dict for compatibility
        return [
            {
                "file": err.file,
                "line": err.line,
                "column": err.column,
                "severity": err.severity,
                "message": err.message,
                "code": err.code,
            }
            for err in all_errors
        ]

    @classmethod
    def register_parser(cls, language: str, phase: str, name: str, parser: ErrorParser):
        """
        Register custom parser for a language/phase.

        Allows extending without modifying existing code (Open/Closed Principle).
        """
        if language not in cls.PARSERS:
            cls.PARSERS[language] = {}
        if phase not in cls.PARSERS[language]:
            cls.PARSERS[language][phase] = {}

        cls.PARSERS[language][phase][name] = parser
