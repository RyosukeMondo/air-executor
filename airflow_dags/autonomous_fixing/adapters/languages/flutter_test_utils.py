"""Flutter test execution utilities."""

import re
import shutil
from pathlib import Path
from typing import Dict


class FlutterTestUtils:
    """Utilities for Flutter test execution and discovery."""

    @staticmethod
    def extract_test_counts(output: str) -> Dict[str, int]:
        """Extract test pass/fail counts from output."""
        # Flutter test output: "All tests passed!" or "Some tests failed."
        # Also: "+5 passed, -2 failed"
        passed = 0
        failed = 0

        # Look for summary line
        if match := re.search(r"\+(\d+)", output):
            passed = int(match.group(1))
        if match := re.search(r"-(\d+)", output):
            failed = int(match.group(1))

        # Fallback: count individual test results
        if passed == 0 and failed == 0:
            passed = output.count("✓")
            failed = output.count("✗")

        return {"passed": passed, "failed": failed}

    @staticmethod
    def find_flutter_executable() -> str:
        """Find Flutter executable, handling PATH issues."""
        # Try which flutter
        flutter_path = shutil.which("flutter")
        if flutter_path:
            return flutter_path

        # Try common locations
        common_paths = [
            Path.home() / "flutter" / "bin" / "flutter",
            Path.home() / "development" / "flutter" / "bin" / "flutter",
            Path("/opt/flutter/bin/flutter"),
            Path("/usr/local/flutter/bin/flutter"),
        ]

        for path in common_paths:
            if path.exists() and path.is_file():
                return str(path)

        return None

    @staticmethod
    def count_test_files_directly(project_path: str) -> int:
        """
        Count test files directly from filesystem.
        Fallback when flutter test doesn't work.
        """
        test_dir = Path(project_path) / "test"
        if not test_dir.exists():
            return 0

        # Count *_test.dart files
        test_files = list(test_dir.rglob("*_test.dart"))
        return len(test_files)
