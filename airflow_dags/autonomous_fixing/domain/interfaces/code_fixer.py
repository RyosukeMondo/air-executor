"""Code fixer interface."""

from abc import ABC, abstractmethod
from ..models import Task, FixResult


class ICodeFixer(ABC):
    """
    Interface for fixing code issues.

    Implementations interact with AI services (Claude, etc.) to fix issues.
    """

    @abstractmethod
    def fix_task(self, task: Task, context: dict = None) -> FixResult:
        """
        Fix a single task.

        Args:
            task: Task to fix
            context: Optional context (previous session summary, etc.)

        Returns:
            FixResult with success/failure info
        """
        pass

    @abstractmethod
    def validate_fix(self, task: Task, before_commit: str, after_commit: str) -> bool:
        """
        Validate that a fix was actually applied.

        Args:
            task: Task that was fixed
            before_commit: Git commit hash before fix
            after_commit: Git commit hash after fix

        Returns:
            True if fix was validated
        """
        pass
