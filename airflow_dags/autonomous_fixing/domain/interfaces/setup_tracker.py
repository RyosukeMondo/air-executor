"""Setup Tracker Interface - Abstract interface for tracking setup completion."""

from abc import ABC, abstractmethod


class ISetupTracker(ABC):
    """
    Interface for tracking setup phase completion.

    Implementations can use Redis, filesystem markers, or in-memory storage
    to track which setup phases have been completed for each project.
    """

    @abstractmethod
    def mark_setup_complete(self, project: str, phase: str) -> None:
        """
        Mark a setup phase as complete for a project.

        Args:
            project: Project identifier (typically absolute path)
            phase: Phase name (e.g., 'hooks', 'tests', 'complexity')

        Example:
            >>> tracker.mark_setup_complete("/path/to/project", "hooks")
        """
        pass

    @abstractmethod
    def is_setup_complete(self, project: str, phase: str) -> bool:
        """
        Check if a setup phase is complete for a project.

        Args:
            project: Project identifier (typically absolute path)
            phase: Phase name (e.g., 'hooks', 'tests', 'complexity')

        Returns:
            True if setup is complete and not stale, False otherwise

        Example:
            >>> if tracker.is_setup_complete("/path/to/project", "hooks"):
            ...     print("Hooks already configured")
        """
        pass

    @abstractmethod
    def clear_setup_state(self, project: str, phase: str) -> None:
        """
        Clear setup completion state for a specific phase.

        Useful for testing or when forcing reconfiguration.

        Args:
            project: Project identifier (typically absolute path)
            phase: Phase name (e.g., 'hooks', 'tests', 'complexity')

        Example:
            >>> tracker.clear_setup_state("/path/to/project", "hooks")
        """
        pass
