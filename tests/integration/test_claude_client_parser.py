"""
Integration tests for ClaudeClient with ResponseParser.

Tests real wrapper response handling and backward compatibility.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest

from airflow_dags.autonomous_fixing.adapters.ai.claude_client import ClaudeClient


class TestClaudeClientParserIntegration:
    """Test ClaudeClient integration with ResponseParser."""

    @pytest.fixture
    def mock_client(self, tmp_path):
        """Create ClaudeClient with mocked dependencies."""
        wrapper_path = str(tmp_path / "wrapper.py")
        python_exec = "python3"
        return ClaudeClient(wrapper_path, python_exec, debug_logger=None)

    def test_success_with_deprecation_warnings_in_stderr(self, mock_client):
        """Test that success + deprecation warnings = success (false negative fix)."""
        # Simulate wrapper response with deprecation warnings
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.pid = 12345

        # stderr with only noise (deprecation warnings)
        stderr = """(node:12345) [DEP0040] DeprecationWarning: The `punycode` module is deprecated.
Use URL polyfill instead.
ExperimentalWarning: stream/web is an experimental feature
"""

        # Mock process behavior
        event_lines = ['{"event": "run_completed", "outcome": "Hook configured"}\n', ""]
        mock_process.stdout.readline = Mock(side_effect=event_lines)
        mock_process.stderr.read = Mock(return_value=stderr)
        mock_process.stdin = Mock()
        mock_process.wait = Mock()

        with patch("subprocess.Popen", return_value=mock_process):
            result = mock_client.query(
                prompt="Configure hooks",
                project_path="/test/project",
                prompt_type="configure_hooks",
            )

        # Should be marked as success (not failure due to deprecation warnings)
        assert result["success"] is True
        assert result.get("status") == "completed"

    def test_failure_with_real_error_in_stderr(self, mock_client):
        """Test that real errors in stderr are detected when no explicit error event."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.pid = 12345

        stderr = """Error: Failed to parse .pre-commit-config.yaml
Invalid YAML syntax at line 15
"""

        event_lines = [""]  # No events
        mock_process.stdout.readline = Mock(side_effect=event_lines)
        mock_process.stderr.read = Mock(return_value=stderr)
        mock_process.stdin = Mock()
        mock_process.wait = Mock()

        with patch("subprocess.Popen", return_value=mock_process):
            result = mock_client.query(
                prompt="Configure hooks",
                project_path="/test/project",
                prompt_type="configure_hooks",
            )

        # Should detect real error from stderr
        assert result["success"] is False
        assert "error_message" in result
        assert "Failed to parse .pre-commit-config.yaml" in result["error_message"]
        assert "[configure_hooks]" in result["error_message"]

    def test_mixed_noise_and_errors(self, mock_client):
        """Test that errors are found even with noise present."""
        mock_process = Mock()
        mock_process.returncode = 0  # Exit code 0 but has real errors
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.pid = 12345

        stderr = """DeprecationWarning: punycode deprecated
PASSED tests/test_one.py
FAILED tests/test_two.py::test_feature - AssertionError: Expected 5 but got 3
ExperimentalWarning: Some feature
"""

        event_lines = ['{"event": "run_completed", "outcome": "Test run completed"}\n', ""]
        mock_process.stdout.readline = Mock(side_effect=event_lines)
        mock_process.stderr.read = Mock(return_value=stderr)
        mock_process.stdin = Mock()
        mock_process.wait = Mock()

        with patch("subprocess.Popen", return_value=mock_process):
            result = mock_client.query(
                prompt="Run tests", project_path="/test/project", prompt_type="run_tests"
            )

        # Should detect FAILED despite noise and success event
        assert result["success"] is False
        assert "FAILED" in result["error_message"]

    def test_backward_compatibility_with_old_format(self, mock_client):
        """Test backward compatibility when response has simple success boolean."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.pid = 12345

        event_lines = ['{"event": "run_completed", "outcome": "Success"}\n', ""]
        mock_process.stdout.readline = Mock(side_effect=event_lines)
        mock_process.stderr.read = Mock(return_value="")
        mock_process.stdin = Mock()
        mock_process.wait = Mock()

        with patch("subprocess.Popen", return_value=mock_process):
            result = mock_client.query(
                prompt="Test", project_path="/test/project", prompt_type="generic"
            )

        # Should handle old format
        assert result["success"] is True

    def test_operation_type_included_in_errors(self, mock_client):
        """Test that operation type is included in error messages for context."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.pid = 12345

        stderr = "Error: Test discovery failed"

        event_lines = [""]
        mock_process.stdout.readline = Mock(side_effect=event_lines)
        mock_process.stderr.read = Mock(return_value=stderr)
        mock_process.stdin = Mock()
        mock_process.wait = Mock()

        with patch("subprocess.Popen", return_value=mock_process):
            result = mock_client.query(
                prompt="Discover tests", project_path="/test/project", prompt_type="discover_tests"
            )

        # Error message should include operation type
        assert result["success"] is False
        assert "[discover_tests]" in result["error_message"]

    def test_events_preserved_in_response(self, mock_client):
        """Test that events are preserved in final response."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.pid = 12345

        event_lines = [
            '{"event": "stream", "payload": {}}\n',
            '{"event": "run_completed", "outcome": "Done"}\n',
            "",
        ]
        mock_process.stdout.readline = Mock(side_effect=event_lines)
        mock_process.stderr.read = Mock(return_value="")
        mock_process.stdin = Mock()
        mock_process.wait = Mock()

        with patch("subprocess.Popen", return_value=mock_process):
            result = mock_client.query(
                prompt="Test", project_path="/test/project", prompt_type="generic"
            )

        # Events should be preserved
        assert "events" in result
        assert len(result["events"]) == 2

    def test_timeout_handling(self, mock_client):
        """Test that timeouts are handled correctly."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.kill = Mock()
            mock_popen.return_value = mock_process

            # Simulate timeout
            mock_process.stdin.write = Mock(side_effect=subprocess.TimeoutExpired("cmd", 10))

            result = mock_client.query(
                prompt="Test", project_path="/test/project", timeout=10, prompt_type="generic"
            )

            assert result["success"] is False
            assert "Timeout" in result.get("error", "")
