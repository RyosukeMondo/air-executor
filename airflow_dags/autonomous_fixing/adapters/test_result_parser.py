"""
Test Result Parser - Single Responsibility: Parse test framework output

SOLID Principles:
- Single Responsibility: ONLY parses test results, nothing else
- Open/Closed: Open for new parsers, closed for modification
- Liskov Substitution: All parsers return same TestCounts interface
- Interface Segregation: Simple, focused interface
- Dependency Inversion: Depends on abstractions, not implementations

KISS: Simple strategy pattern with fallback
SSOT: Single source of truth for test result parsing logic
"""

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol
from abc import ABC, abstractmethod


@dataclass
class TestCounts:
    """Test result counts - SSOT for test statistics."""
    passed: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.total > 0


class TestResultParser(ABC):
    """Abstract base for test result parsers."""

    @abstractmethod
    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """
        Parse test output and return counts.

        Args:
            output: Raw test output (stdout + stderr)
            output_file: Optional path to structured output file (JSON/XML)

        Returns:
            TestCounts if parsing successful, None otherwise
        """
        pass


# =============================================================================
# JavaScript/TypeScript Parsers
# =============================================================================

class JestJSONParser(TestResultParser):
    """Parse Jest JSON output - PREFERRED."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse Jest --json output."""
        try:
            # Try file first (cleanest)
            if output_file and output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
                return self._parse_json_data(data)

            # Try finding JSON in output (last line usually)
            for line in reversed(output.splitlines()):
                try:
                    data = json.loads(line)
                    return self._parse_json_data(data)
                except json.JSONDecodeError:
                    continue

            return None

        except Exception:
            return None

    def _parse_json_data(self, data: dict) -> TestCounts:
        """Extract counts from Jest JSON structure."""
        return TestCounts(
            passed=data.get('numPassedTests', 0),
            failed=data.get('numFailedTests', 0),
            skipped=data.get('numPendingTests', 0)
        )


class JestTextParser(TestResultParser):
    """Parse Jest text output - FALLBACK."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse Jest text summary with regex."""
        try:
            # Jest final summary: "Tests: 28 failed, 5 skipped, 64 passed, 97 total"
            # Use findall to get all matches, take last (final summary)

            passed_matches = re.findall(r'(\d+) passed', output)
            failed_matches = re.findall(r'(\d+) failed', output)
            skipped_matches = re.findall(r'(\d+) skipped', output)

            if not (passed_matches or failed_matches):
                return None  # No test output found

            return TestCounts(
                passed=int(passed_matches[-1]) if passed_matches else 0,
                failed=int(failed_matches[-1]) if failed_matches else 0,
                skipped=int(skipped_matches[-1]) if skipped_matches else 0
            )

        except Exception:
            return None


class VitestJSONParser(TestResultParser):
    """Parse Vitest JSON output."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse Vitest --reporter=json output."""
        try:
            if output_file and output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
            else:
                # Find JSON in output
                data = json.loads(output)

            results = data.get('testResults', {})
            return TestCounts(
                passed=results.get('numPassedTests', 0),
                failed=results.get('numFailedTests', 0),
                skipped=results.get('numPendingTests', 0)
            )

        except Exception:
            return None


# =============================================================================
# Python Parsers
# =============================================================================

class PytestJUnitXMLParser(TestResultParser):
    """Parse pytest JUnit XML output - PREFERRED."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse pytest --junitxml output."""
        try:
            if not output_file or not output_file.exists():
                return None

            tree = ET.parse(output_file)
            root = tree.getroot()

            total = int(root.attrib.get('tests', 0))
            failures = int(root.attrib.get('failures', 0))
            errors = int(root.attrib.get('errors', 0))
            skipped = int(root.attrib.get('skipped', 0))

            passed = total - failures - errors - skipped

            return TestCounts(
                passed=passed,
                failed=failures + errors,
                skipped=skipped
            )

        except Exception:
            return None


class PytestTextParser(TestResultParser):
    """Parse pytest text output - FALLBACK."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse pytest text summary."""
        try:
            # pytest: "= 42 passed, 3 failed, 1 skipped in 1.23s ="
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            skipped_match = re.search(r'(\d+) skipped', output)

            if not (passed_match or failed_match):
                return None

            return TestCounts(
                passed=int(passed_match.group(1)) if passed_match else 0,
                failed=int(failed_match.group(1)) if failed_match else 0,
                skipped=int(skipped_match.group(1)) if skipped_match else 0
            )

        except Exception:
            return None


# =============================================================================
# Go Parsers
# =============================================================================

class GoTestJSONParser(TestResultParser):
    """Parse Go test -json output - PREFERRED."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse go test -json output (NDJSON format)."""
        try:
            passed = 0
            failed = 0
            skipped = 0

            # Parse newline-delimited JSON
            for line in output.splitlines():
                try:
                    event = json.loads(line)
                    action = event.get('Action')

                    # Only count test-level events
                    if 'Test' in event and not event['Test'].startswith('Test'):
                        continue  # Skip sub-tests

                    if action == 'pass':
                        passed += 1
                    elif action == 'fail':
                        failed += 1
                    elif action == 'skip':
                        skipped += 1

                except json.JSONDecodeError:
                    continue

            if passed + failed + skipped == 0:
                return None

            return TestCounts(passed=passed, failed=failed, skipped=skipped)

        except Exception:
            return None


class GoTestTextParser(TestResultParser):
    """Parse Go test text output - FALLBACK."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse go test text output."""
        try:
            # Count PASS/FAIL lines
            passed = len(re.findall(r'^PASS', output, re.MULTILINE))
            failed = len(re.findall(r'^FAIL', output, re.MULTILINE))

            if passed + failed == 0:
                return None

            return TestCounts(passed=passed, failed=failed, skipped=0)

        except Exception:
            return None


# =============================================================================
# Flutter/Dart Parsers
# =============================================================================

class FlutterTestJSONParser(TestResultParser):
    """Parse Flutter test --machine output - PREFERRED."""

    def parse(self, output: str, output_file: Optional[Path] = None) -> Optional[TestCounts]:
        """Parse flutter test --machine output."""
        try:
            passed = 0
            failed = 0
            skipped = 0

            # Flutter outputs NDJSON
            for line in output.splitlines():
                try:
                    event = json.loads(line)
                    event_type = event.get('type')

                    if event_type == 'testDone':
                        result = event.get('result')
                        if result == 'success':
                            passed += 1
                        elif result == 'failure' or result == 'error':
                            failed += 1

                    elif event_type == 'testSkipped':
                        skipped += 1

                except json.JSONDecodeError:
                    continue

            if passed + failed + skipped == 0:
                return None

            return TestCounts(passed=passed, failed=failed, skipped=skipped)

        except Exception:
            return None


# =============================================================================
# Parser Strategy - SSOT for Parser Selection
# =============================================================================

class TestResultParserStrategy:
    """
    Strategy for parsing test results with fallback.

    SOLID: Strategy pattern for parser selection
    KISS: Simple try-preferred-then-fallback logic
    SSOT: Single place to configure parsers per language
    """

    # Parser configuration - SSOT
    PARSERS = {
        'javascript': {
            'preferred': JestJSONParser(),
            'fallback': JestTextParser()
        },
        'typescript': {
            'preferred': JestJSONParser(),
            'fallback': JestTextParser()
        },
        'vitest': {
            'preferred': VitestJSONParser(),
            'fallback': JestTextParser()  # Similar format
        },
        'python': {
            'preferred': PytestJUnitXMLParser(),
            'fallback': PytestTextParser()
        },
        'go': {
            'preferred': GoTestJSONParser(),
            'fallback': GoTestTextParser()
        },
        'flutter': {
            'preferred': FlutterTestJSONParser(),
            'fallback': JestTextParser()  # Similar format
        }
    }

    @classmethod
    def parse(cls, language: str, output: str,
              output_file: Optional[Path] = None) -> TestCounts:
        """
        Parse test output using best available parser.

        Args:
            language: Project language (javascript, python, go, flutter)
            output: Raw test output (stdout + stderr)
            output_file: Optional path to structured output file

        Returns:
            TestCounts with parsed results (or zeros if parsing failed)
        """
        parsers = cls.PARSERS.get(language.lower())
        if not parsers:
            # Unknown language - try text parsers
            parsers = {'fallback': JestTextParser()}

        # Try preferred parser first (structured output)
        if 'preferred' in parsers:
            result = parsers['preferred'].parse(output, output_file)
            if result:
                return result

        # Fallback to text parser (regex)
        if 'fallback' in parsers:
            result = parsers['fallback'].parse(output, output_file)
            if result:
                return result

        # No parsing successful - return zeros
        return TestCounts()

    @classmethod
    def register_parser(cls, language: str, parser: TestResultParser,
                       preferred: bool = True):
        """
        Register custom parser for a language.

        Allows extending without modifying existing code (Open/Closed Principle).
        """
        if language not in cls.PARSERS:
            cls.PARSERS[language] = {}

        key = 'preferred' if preferred else 'fallback'
        cls.PARSERS[language][key] = parser
