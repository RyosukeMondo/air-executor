"""In-memory setup tracker for fast testing without Redis or filesystem."""

from airflow_dags.autonomous_fixing.domain.interfaces.setup_tracker import ISetupTracker


class MemorySetupTracker(ISetupTracker):
    """
    In-memory implementation of ISetupTracker for testing.

    Provides fast, isolated setup tracking without Redis or filesystem dependencies.
    State is lost when instance is destroyed (ideal for test isolation).

    Example:
        >>> tracker = MemorySetupTracker()
        >>> tracker.mark_setup_complete("/project", "hooks")
        >>> assert tracker.is_setup_complete("/project", "hooks") is True
        >>> assert tracker.is_setup_complete("/project", "tests") is False
    """

    def __init__(self):
        """Initialize empty in-memory storage."""
        # Set of (project, phase) tuples representing completed setups
        self.completions: set[tuple[str, str]] = set()

    def mark_setup_complete(self, project: str, phase: str) -> None:
        """
        Mark setup phase as complete by adding to in-memory set.

        Args:
            project: Project identifier
            phase: Phase name
        """
        self.completions.add((project, phase))

    def is_setup_complete(self, project: str, phase: str) -> bool:
        """
        Check if setup phase is complete by checking in-memory set.

        Args:
            project: Project identifier
            phase: Phase name

        Returns:
            True if (project, phase) tuple exists in completions set
        """
        return (project, phase) in self.completions

    def clear_setup_state(self, project: str, phase: str) -> None:
        """
        Clear setup completion state for a specific phase.

        Args:
            project: Project identifier
            phase: Phase name
        """
        self.completions.discard((project, phase))

    def clear_all(self) -> None:
        """Clear all completion state (useful for test cleanup)."""
        self.completions.clear()
