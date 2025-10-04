"""Issue discovery interface."""

from abc import ABC, abstractmethod

from ..models import Task


class IIssueDiscoverer(ABC):
    """
    Interface for discovering issues.

    Implementations analyze project state and generate fix tasks.
    """

    @abstractmethod
    def discover_build_issues(self) -> list[Task]:
        """
        Discover build/compilation issues.

        Returns:
            List of tasks for build fixes
        """
        pass

    @abstractmethod
    def discover_test_failures(self) -> list[Task]:
        """
        Discover test failures.

        Returns:
            List of tasks for test fixes
        """
        pass

    @abstractmethod
    def discover_lint_issues(self) -> list[Task]:
        """
        Discover linting/style issues.

        Returns:
            List of tasks for lint fixes
        """
        pass

    @abstractmethod
    def discover_coverage_gaps(self) -> list[Task]:
        """
        Discover test coverage gaps.

        Returns:
            List of tasks for coverage improvement
        """
        pass
