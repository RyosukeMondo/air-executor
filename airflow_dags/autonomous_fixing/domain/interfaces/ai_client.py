"""AI Client Interface for dependency injection and testing."""

from abc import ABC, abstractmethod
from typing import Any


class IAIClient(ABC):
    """Interface for AI language model interactions."""

    @abstractmethod
    def query(
        self,
        prompt: str,
        project_path: str,
        timeout: int = 600,
        session_id: str | None = None,
        prompt_type: str = "generic",
    ) -> dict[str, Any]:
        """
        Send prompt to AI model.

        Args:
            prompt: Prompt text for the AI model
            project_path: Project working directory
            timeout: Timeout in seconds
            session_id: Optional session ID for continuity
            prompt_type: Type of prompt for logging (analysis, fix_error, fix_test, create_test)

        Returns:
            Dict with result containing at minimum:
            - success: bool indicating if query succeeded
            - error: Optional[str] error message if failed
            - outcome: Optional[str] result text if successful
            - events: list of events (implementation-specific)
        """
        pass

    @abstractmethod
    def query_simple(self, prompt: str, project_path: str, timeout: int = 600) -> bool:
        """
        Simplified query that returns True/False.

        Args:
            prompt: Prompt text for the AI model
            project_path: Project working directory
            timeout: Timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        pass
