"""
In-Memory State Repository - Fast state storage for testing.

Provides IStateRepository implementation using in-memory dict,
enabling fast, isolated tests without filesystem I/O.
"""

from typing import Any

from ...domain.interfaces.state_repository import IStateRepository


class MemoryStateRepository(IStateRepository):
    """
    In-memory state repository for fast, isolated testing.

    Features:
    - No filesystem I/O
    - Instant state persistence and retrieval
    - Isolated per-instance (no cross-test pollution)
    - Simple state validation logic

    Use for:
    - Unit tests requiring state management
    - Integration tests needing fast execution
    - CI/CD environments prioritizing speed
    """

    def __init__(self):
        """Initialize empty in-memory state storage."""
        self.states: dict[str, dict[str, Any]] = {}

    def should_reconfigure(self, phase: str) -> tuple[bool, str]:
        """
        Check if reconfiguration needed for phase.

        Simple logic:
        - State exists → can skip (False, "cached in memory")
        - State missing → must reconfigure (True, "no state in memory")

        Args:
            phase: Setup phase name

        Returns:
            (should_reconfigure, reason) tuple
        """
        if phase not in self.states:
            return (True, f"no {phase} state in memory")
        return (False, f"{phase} cached in memory")

    def save_state(self, phase: str, data: dict[str, Any]) -> None:
        """
        Save state in memory.

        Args:
            phase: Setup phase name
            data: State data to store
        """
        self.states[phase] = data

    def get_state(self, phase: str) -> dict[str, Any] | None:
        """
        Get saved state for phase.

        Args:
            phase: Setup phase name

        Returns:
            State data if exists, None otherwise
        """
        return self.states.get(phase)

    def clear_state(self, phase: str | None = None) -> None:
        """
        Clear state for testing.

        Args:
            phase: Phase to clear, or None to clear all
        """
        if phase is None:
            self.states.clear()
        elif phase in self.states:
            del self.states[phase]
