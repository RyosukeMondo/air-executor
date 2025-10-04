"""Domain enumerations for type-safe string replacements.

This module provides enums to replace fragile string matching patterns
throughout the codebase, improving type safety and maintainability.
"""

from enum import Enum


class TaskType(Enum):
    """Task execution types."""

    CLEANUP = "cleanup"
    LOCATION = "location"
    FIX_ERROR = "fix_error"
    FIX_COMPLEXITY = "fix_complexity"
    FIX_BUILD = "fix_build"
    CREATE_TEST = "create_test"

    def __str__(self) -> str:
        """Return the string value for backward compatibility."""
        return self.value


class AnalysisStatus(Enum):
    """Analysis phase status."""

    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"
    SKIPPED = "skipped"

    def __str__(self) -> str:
        """Return the string value for backward compatibility."""
        return self.value


class IssueType(Enum):
    """Issue categorization."""

    ERROR = "error"
    COMPLEXITY = "complexity"
    FILE_SIZE = "file_size"
    STYLE = "style"
    TEST_FAILURE = "test_failure"

    def __str__(self) -> str:
        """Return the string value for backward compatibility."""
        return self.value


class Phase(Enum):
    """Analysis and execution phases."""

    HOOKS = "hooks"
    STATIC = "static"
    TESTS = "tests"
    COVERAGE = "coverage"
    E2E = "e2e"

    def is_hooks(self) -> bool:
        """Check if this phase is hooks phase."""
        return self == Phase.HOOKS

    def __str__(self) -> str:
        """Return the string value for backward compatibility."""
        return self.value


class Severity(Enum):
    """Error severity levels."""

    ERROR = 2
    WARNING = 1
    INFO = 0

    def __str__(self) -> str:
        """Return the severity name in lowercase."""
        return self.name.lower()
