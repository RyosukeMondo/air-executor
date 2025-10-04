"""Mock AI Client for testing - deterministic responses without external dependencies."""

from typing import Any, Optional

from ...domain.interfaces.ai_client import IAIClient


class MockAIClient(IAIClient):
    """Deterministic AI client for testing.

    Provides configurable responses without calling external AI services.
    Records all calls for verification in tests.
    """

    def __init__(self, responses: Optional[dict[str, str]] = None):
        """
        Initialize mock AI client.

        Args:
            responses: Dict mapping issue messages/prompts to response strings.
                      If None, returns generic successful responses.
        """
        self.responses = responses or {}
        self.calls: list[dict[str, Any]] = []

    def query(
        self,
        prompt: str,
        project_path: str,
        timeout: int = 600,
        session_id: str | None = None,
        prompt_type: str = "generic",
    ) -> dict[str, Any]:
        """
        Return mocked response based on prompt.

        Args:
            prompt: Prompt text
            project_path: Project path
            timeout: Timeout (ignored)
            session_id: Session ID (ignored)
            prompt_type: Prompt type

        Returns:
            Dict with mocked success response
        """
        # Record call for test verification
        self.calls.append(
            {
                "prompt": prompt,
                "project_path": project_path,
                "timeout": timeout,
                "session_id": session_id,
                "prompt_type": prompt_type,
            }
        )

        # Find matching response based on prompt content
        response_text = self._find_response(prompt)

        return {
            "success": True,
            "outcome": response_text,
            "events": [{"event": "run_completed", "outcome": response_text}],
        }

    def query_simple(self, prompt: str, project_path: str, timeout: int = 600) -> bool:
        """
        Return True for simple query (always succeeds in mock).

        Args:
            prompt: Prompt text
            project_path: Project path
            timeout: Timeout (ignored)

        Returns:
            True (always successful in mock)
        """
        result = self.query(prompt, project_path, timeout)
        return result.get("success", False)

    def _find_response(self, prompt: str) -> str:
        """Find response for prompt from configured responses."""
        # Try exact match first
        if prompt in self.responses:
            return self.responses[prompt]

        # Try substring match (for issue messages in prompts)
        for key, response in self.responses.items():
            if key in prompt:
                return response

        # Default response
        return "# Fixed code\nThe issue has been resolved."

    def get_call_count(self) -> int:
        """Get number of calls made."""
        return len(self.calls)

    def get_last_call(self) -> Optional[dict[str, Any]]:
        """Get last call made."""
        return self.calls[-1] if self.calls else None

    def get_calls_by_type(self, prompt_type: str) -> list[dict[str, Any]]:
        """Get all calls of specific type."""
        return [call for call in self.calls if call["prompt_type"] == prompt_type]

    def reset(self):
        """Reset call history."""
        self.calls = []
