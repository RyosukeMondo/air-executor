"""
E2E test validating false negative fix.

Tests that the ResponseParser correctly handles real-world scenarios
where operations succeed but produce deprecation warnings in stderr.
"""

from airflow_dags.autonomous_fixing.adapters.ai.response_parser import ResponseParser


class TestFalseNegativesFix:
    """E2E validation that false negatives are eliminated."""

    def test_real_world_node_punycode_warning(self):
        """
        Test real-world scenario: Node.js punycode deprecation warning.

        This was the original false negative that triggered this spec.
        Hook configuration completes successfully but stderr contains
        deprecation warning, which should NOT be marked as failure.
        """
        parser = ResponseParser()

        # Real stderr from Node.js with punycode warning
        real_stderr = """(node:87403) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
"""

        # Wrapper returns success status
        response = {
            "success": True,
            "stderr": real_stderr,
            "events": [{"event": "run_completed", "outcome": "Hook configuration completed"}],
        }

        result = parser.parse(response, "configure_hooks")

        # CRITICAL: Should be marked as SUCCESS (not failure)
        assert result["success"] is True
        assert result.get("status") == "completed"
        assert "error_message" not in result

    def test_real_world_experimental_warning(self):
        """Test ExperimentalWarning doesn't cause false failures."""
        parser = ResponseParser()

        stderr = """ExperimentalWarning: stream/web is an experimental feature. This feature could change at any time
"""

        response = {"success": True, "stderr": stderr}
        result = parser.parse(response, "test_operation")

        assert result["success"] is True

    def test_combined_warnings_still_success(self):
        """Test multiple types of warnings together don't trigger failure."""
        parser = ResponseParser()

        stderr = """(node:12345) DeprecationWarning: crypto.DEFAULT_ENCODING is deprecated.
ExperimentalWarning: The Fetch API is experimental
Skipping files: node_modules/
"""

        response = {"success": True, "stderr": stderr}
        result = parser.parse(response, "configure_hooks")

        assert result["success"] is True

    def test_real_error_still_caught(self):
        """Verify real errors are still detected (no false positives)."""
        parser = ResponseParser()

        stderr = """DeprecationWarning: punycode deprecated
Error: ENOENT: no such file or directory, open '.pre-commit-config.yaml'
"""

        response = {"success": True, "stderr": stderr}
        result = parser.parse(response, "configure_hooks")

        # Real error should still be caught
        assert result["success"] is False
        assert "ENOENT" in result["error_message"]

    def test_custom_patterns_via_config(self, tmp_path):
        """Test that custom noise patterns work end-to-end."""
        import yaml

        # Create custom config with additional noise pattern
        config_file = tmp_path / "custom_patterns.yaml"
        config_data = {
            "noise_patterns": [
                "punycode",
                "CUSTOM_WARNING:",  # Custom pattern
                "ExperimentalWarning",
            ],
            "error_indicators": ["Error:", "FAILED:"],
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        parser = ResponseParser(config_path=str(config_file))

        stderr = "CUSTOM_WARNING: This is a custom warning that should be ignored"
        response = {"success": True, "stderr": stderr}
        result = parser.parse(response, "test_operation")

        # Custom pattern should be filtered out
        assert result["success"] is True

    def test_multiple_errors_extracted_correctly(self):
        """Test that multiple real errors are all captured."""
        parser = ResponseParser()

        stderr = """DeprecationWarning: something deprecated
Error: First real error
Some info log
Error: Second real error
FAILED: Third error
ExperimentalWarning: ignore this
"""

        response = {"success": False, "stderr": stderr}
        result = parser.parse(response, "test_operation")

        assert result["success"] is False
        assert len(result["errors"]) == 3
        assert "First real error" in result["errors"][0]
        assert "Second real error" in result["errors"][1]
        assert "Third error" in result["errors"][2]

    def test_edge_case_empty_stderr(self):
        """Test edge case: empty stderr with success flag."""
        parser = ResponseParser()

        response = {"success": True, "stderr": ""}
        result = parser.parse(response, "test_operation")

        assert result["success"] is True

    def test_edge_case_only_whitespace_stderr(self):
        """Test edge case: stderr with only whitespace."""
        parser = ResponseParser()

        response = {"success": True, "stderr": "\n\n   \n"}
        result = parser.parse(response, "test_operation")

        assert result["success"] is True

    def test_unicode_in_warnings(self):
        """Test that unicode characters in warnings are handled correctly."""
        parser = ResponseParser()

        stderr = "DeprecationWarning: 日本語の警告メッセージ"
        response = {"success": True, "stderr": stderr}
        result = parser.parse(response, "test_operation")

        assert result["success"] is True

    def test_end_to_end_workflow_success_scenario(self):
        """
        Simulate complete workflow: wrapper returns success + warnings.

        This represents the full autonomous fixing scenario where:
        1. Wrapper executes successfully (exit code 0)
        2. Stderr contains only deprecation warnings
        3. Parser should mark as success (not failure)
        """
        parser = ResponseParser()

        # Simulate wrapper response
        wrapper_response = {
            "success": True,
            "events": [
                {"event": "stream", "payload": {"text": "Configuring hooks..."}},
                {"event": "run_completed", "outcome": "Hooks configured successfully"},
            ],
            "stderr": """(node:12345) [DEP0040] DeprecationWarning: The `punycode` module is deprecated.
(node:12345) ExperimentalWarning: The Fetch API is an experimental feature
Skipping files in .git/
""",
        }

        result = parser.parse(wrapper_response, "configure_hooks")

        # Complete workflow should succeed
        assert result["success"] is True
        assert result["status"] == "completed"
        assert "events" not in result  # Events not part of parser output
        assert "error_message" not in result

    def test_end_to_end_workflow_failure_scenario(self):
        """
        Simulate complete workflow: wrapper fails with real error.

        This ensures real errors are still caught after fixing false negatives.
        """
        parser = ResponseParser()

        wrapper_response = {
            "success": False,
            "events": [{"event": "run_failed", "error": "Configuration failed"}],
            "stderr": """Error: Failed to install pre-commit hooks
FAILED: Hook installation exited with code 1
""",
        }

        result = parser.parse(wrapper_response, "configure_hooks")

        # Should correctly identify as failure
        assert result["success"] is False
        assert "Failed to install pre-commit hooks" in result["error_message"]
        assert len(result["errors"]) == 2
