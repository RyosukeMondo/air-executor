"""Tests for IAIClient interface compliance and implementations."""

from airflow_dags.autonomous_fixing.adapters.ai.claude_client import ClaudeClient
from airflow_dags.autonomous_fixing.adapters.ai.mock_ai_client import MockAIClient
from airflow_dags.autonomous_fixing.domain.interfaces import IAIClient


class TestAIClientInterfaceCompliance:
    """Test that all IAIClient implementations comply with the interface."""

    def test_claude_client_implements_interface(self):
        """Verify ClaudeClient implements IAIClient."""
        assert issubclass(ClaudeClient, IAIClient)

    def test_mock_ai_client_implements_interface(self):
        """Verify MockAIClient implements IAIClient."""
        assert issubclass(MockAIClient, IAIClient)

    def test_interface_has_required_methods(self):
        """Verify IAIClient defines required abstract methods."""
        required_methods = ["query", "query_simple"]
        interface_methods = [method for method in dir(IAIClient) if not method.startswith("_")]

        for method in required_methods:
            assert method in interface_methods, f"IAIClient missing required method: {method}"


class TestMockAIClient:
    """Test MockAIClient behavior."""

    def test_initialization_with_no_responses(self):
        """Test MockAIClient can be initialized without responses."""
        client = MockAIClient()
        assert client.responses == {}
        assert client.calls == []

    def test_initialization_with_responses(self):
        """Test MockAIClient can be initialized with custom responses."""
        responses = {"error": "fixed", "warning": "improved"}
        client = MockAIClient(responses=responses)
        assert client.responses == responses

    def test_query_returns_success_dict(self):
        """Test query method returns proper success dict."""
        client = MockAIClient()
        result = client.query(
            prompt="Fix this issue",
            project_path="/test/project",
            timeout=60,
            prompt_type="fix_error",
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "outcome" in result
        assert "events" in result

    def test_query_records_call(self):
        """Test query records call details."""
        client = MockAIClient()
        client.query(
            prompt="Fix this",
            project_path="/test/project",
            timeout=60,
            session_id="test-session",
            prompt_type="fix_error",
        )

        assert len(client.calls) == 1
        call = client.calls[0]
        assert call["prompt"] == "Fix this"
        assert call["project_path"] == "/test/project"
        assert call["timeout"] == 60
        assert call["session_id"] == "test-session"
        assert call["prompt_type"] == "fix_error"

    def test_query_uses_custom_responses(self):
        """Test query returns configured custom responses."""
        responses = {"syntax error": "fixed_syntax = True", "type error": "x: int = 5"}
        client = MockAIClient(responses=responses)

        # Exact match
        result = client.query("syntax error", "/test", prompt_type="fix_error")
        assert "fixed_syntax = True" in result["outcome"]

        # Substring match
        result = client.query("Found type error in code", "/test", prompt_type="fix_error")
        assert "x: int = 5" in result["outcome"]

    def test_query_returns_default_response(self):
        """Test query returns default response when no match found."""
        client = MockAIClient(responses={"specific": "specific fix"})
        result = client.query("unknown issue", "/test", prompt_type="fix_error")

        assert result["success"] is True
        assert "Fixed code" in result["outcome"]

    def test_query_simple_returns_bool(self):
        """Test query_simple returns boolean."""
        client = MockAIClient()
        result = client.query_simple("Fix this", "/test")

        assert isinstance(result, bool)
        assert result is True

    def test_get_call_count(self):
        """Test get_call_count returns correct count."""
        client = MockAIClient()
        assert client.get_call_count() == 0

        client.query("test1", "/test")
        assert client.get_call_count() == 1

        client.query("test2", "/test")
        assert client.get_call_count() == 2

    def test_get_last_call(self):
        """Test get_last_call returns most recent call."""
        client = MockAIClient()
        assert client.get_last_call() is None

        client.query("first", "/test", prompt_type="analysis")
        client.query("second", "/test", prompt_type="fix_error")

        last_call = client.get_last_call()
        assert last_call is not None
        assert last_call["prompt"] == "second"
        assert last_call["prompt_type"] == "fix_error"

    def test_get_calls_by_type(self):
        """Test get_calls_by_type filters calls correctly."""
        client = MockAIClient()
        client.query("analyze", "/test", prompt_type="analysis")
        client.query("fix1", "/test", prompt_type="fix_error")
        client.query("fix2", "/test", prompt_type="fix_error")
        client.query("test", "/test", prompt_type="fix_test")

        fix_calls = client.get_calls_by_type("fix_error")
        assert len(fix_calls) == 2
        assert all(call["prompt_type"] == "fix_error" for call in fix_calls)

        analysis_calls = client.get_calls_by_type("analysis")
        assert len(analysis_calls) == 1

    def test_reset_clears_calls(self):
        """Test reset clears call history."""
        client = MockAIClient()
        client.query("test1", "/test")
        client.query("test2", "/test")

        assert client.get_call_count() == 2

        client.reset()
        assert client.get_call_count() == 0
        assert client.calls == []


class TestClaudeClientInterfaceCompliance:
    """Test ClaudeClient implements IAIClient interface correctly."""

    def test_claude_client_has_query_method(self):
        """Verify ClaudeClient has query method with correct signature."""
        assert hasattr(ClaudeClient, "query")
        # Verify it's callable
        assert callable(getattr(ClaudeClient, "query"))

    def test_claude_client_has_query_simple_method(self):
        """Verify ClaudeClient has query_simple method."""
        assert hasattr(ClaudeClient, "query_simple")
        assert callable(getattr(ClaudeClient, "query_simple"))


class TestInterfaceConsistency:
    """Test that both implementations behave consistently with interface contract."""

    def test_query_returns_dict_with_success(self):
        """All implementations must return dict with 'success' key."""
        mock_client = MockAIClient()
        result = mock_client.query("test", "/test")

        assert isinstance(result, dict)
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_query_simple_returns_bool(self):
        """All implementations must return bool from query_simple."""
        mock_client = MockAIClient()
        result = mock_client.query_simple("test", "/test")

        assert isinstance(result, bool)

    def test_interface_method_signatures(self):
        """Verify all implementations have matching method signatures."""
        # Get interface method signatures
        import inspect

        interface_query_sig = inspect.signature(IAIClient.query)
        interface_query_simple_sig = inspect.signature(IAIClient.query_simple)

        # Check ClaudeClient
        claude_query_sig = inspect.signature(ClaudeClient.query)
        claude_query_simple_sig = inspect.signature(ClaudeClient.query_simple)

        # Check MockAIClient
        mock_query_sig = inspect.signature(MockAIClient.query)
        mock_query_simple_sig = inspect.signature(MockAIClient.query_simple)

        # Verify parameter names match (ignoring self)
        assert (
            list(interface_query_sig.parameters.keys())[1:]
            == list(claude_query_sig.parameters.keys())[1:]
        )
        assert (
            list(interface_query_sig.parameters.keys())[1:]
            == list(mock_query_sig.parameters.keys())[1:]
        )

        assert (
            list(interface_query_simple_sig.parameters.keys())[1:]
            == list(claude_query_simple_sig.parameters.keys())[1:]
        )
        assert (
            list(interface_query_simple_sig.parameters.keys())[1:]
            == list(mock_query_simple_sig.parameters.keys())[1:]
        )
