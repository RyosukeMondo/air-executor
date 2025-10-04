"""
State Repository Interface - Abstract interface for project state management.

Defines the contract for state persistence implementations, enabling in-memory
testing and alternative storage backends.
"""

from abc import ABC, abstractmethod
from typing import Any


class IStateRepository(ABC):
    """
    Interface for project state management.

    Implementations must provide:
    - State persistence (save_state)
    - Reconfiguration detection (should_reconfigure)
    - Configuration change tracking
    """

    @abstractmethod
    def should_reconfigure(self, phase: str) -> tuple[bool, str]:
        """
        Check if reconfiguration is needed for a phase.

        Args:
            phase: Setup phase name ('hooks' or 'tests')

        Returns:
            (should_reconfigure, reason): Boolean and explanation string
                - (True, reason): Reconfiguration needed
                - (False, reason): Can skip reconfiguration
        """

    @abstractmethod
    def save_state(self, phase: str, data: dict[str, Any]) -> None:
        """
        Save state for a phase.

        Args:
            phase: Setup phase name ('hooks' or 'tests')
            data: State data to persist (configuration, metadata)
        """

    @abstractmethod
    def get_state(self, phase: str) -> dict[str, Any] | None:
        """
        Get saved state for a phase.

        Args:
            phase: Setup phase name ('hooks' or 'tests')

        Returns:
            State data dict if exists, None if no state found
        """
