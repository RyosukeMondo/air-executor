"""
Unit tests for ResponseParser - intelligent error detection.

Tests noise filtering, error detection, config loading, and edge cases.
"""

import yaml

from airflow_dags.autonomous_fixing.adapters.ai.response_parser import (
    DEFAULT_ERROR_INDICATORS,
    DEFAULT_NOISE_PATTERNS,
    ResponseParser,
)


class TestResponseParser:
    """Test ResponseParser class."""

    def test_parse_success_with_clean_stderr(self):
        """Test successful response with no stderr."""
        parser = ResponseParser()
        response = {"success": True, "stderr": ""}
        result = parser.parse(response, "test_operation")

        assert result["success"] is True
        assert result["status"] == "completed"

    def test_parse_success_with_noise_only(self):
        """Test successful response with only noise in stderr (false negative fix)."""
        parser = ResponseParser()
        stderr = """(node:12345) [DEP0040] DeprecationWarning: The `punycode` module is deprecated.
ExperimentalWarning: Feature is experimental
Skipping files in .gitignore
"""
        response = {"success": True, "stderr": stderr}
        result = parser.parse(response, "configure_hooks")

        assert result["success"] is True
        assert result["status"] == "completed"

    def test_parse_failure_with_real_errors(self):
        """Test failure detection with real errors in stderr."""
        parser = ResponseParser()
        stderr = """Some info message
Error: Failed to parse configuration
Details: Invalid YAML syntax
"""
        response = {"success": False, "stderr": stderr}
        result = parser.parse(response, "test_operation")

        assert result["success"] is False
        assert "error_message" in result
        assert "Error: Failed to parse configuration" in result["error_message"]
        assert result["errors"] == ["Error: Failed to parse configuration"]

    def test_parse_failure_with_mixed_content(self):
        """Test that real errors are detected even with noise present."""
        parser = ResponseParser()
        stderr = """DeprecationWarning: punycode is deprecated
ExperimentalWarning: Some feature
Error: Configuration validation failed
FAILED: Test suite crashed
Some more noise here
"""
        response = {"success": True, "stderr": stderr}  # Success flag but has real errors
        result = parser.parse(response, "test_operation")

        assert result["success"] is False
        assert len(result["errors"]) == 2
        assert "Error: Configuration validation failed" in result["errors"]
        assert "FAILED: Test suite crashed" in result["errors"]

    def test_extract_real_errors_filters_noise(self):
        """Test _extract_real_errors filters out noise patterns."""
        parser = ResponseParser()
        stderr = """punycode module deprecated
ExperimentalWarning: feature
Regular log message
"""
        errors = parser._extract_real_errors(stderr)
        assert errors == []

    def test_extract_real_errors_finds_errors(self):
        """Test _extract_real_errors finds error indicators."""
        parser = ResponseParser()
        stderr = """Info message
Error: Something went wrong
Exception in module.py
Traceback (most recent call last)
"""
        errors = parser._extract_real_errors(stderr)
        assert len(errors) == 3
        assert "Error: Something went wrong" in errors
        assert "Exception in module.py" in errors
        assert "Traceback (most recent call last)" in errors

    def test_is_noise_detects_patterns(self):
        """Test _is_noise correctly identifies noise patterns."""
        parser = ResponseParser()
        assert parser._is_noise("The punycode module is deprecated") is True
        assert parser._is_noise("ExperimentalWarning: feature") is True
        assert parser._is_noise("Skipping files in directory") is True
        assert parser._is_noise("Error: Something failed") is False
        assert parser._is_noise("Regular log message") is False

    def test_config_loading_from_file(self, tmp_path):
        """Test loading patterns from YAML config file."""
        config_file = tmp_path / "error_patterns.yaml"
        config_data = {
            "noise_patterns": ["custom_noise", "another_warning"],
            "error_indicators": ["CUSTOM_ERROR:", "FAIL:"],
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        parser = ResponseParser(config_path=str(config_file))

        assert parser.noise_patterns == ["custom_noise", "another_warning"]
        assert parser.error_indicators == ["CUSTOM_ERROR:", "FAIL:"]

    def test_config_missing_file_uses_defaults(self, tmp_path):
        """Test that missing config file falls back to defaults."""
        parser = ResponseParser(config_path=str(tmp_path / "nonexistent.yaml"))

        assert parser.noise_patterns == DEFAULT_NOISE_PATTERNS
        assert parser.error_indicators == DEFAULT_ERROR_INDICATORS

    def test_config_invalid_yaml_uses_defaults(self, tmp_path):
        """Test that invalid YAML falls back to defaults."""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [broken")

        parser = ResponseParser(config_path=str(config_file))

        assert parser.noise_patterns == DEFAULT_NOISE_PATTERNS
        assert parser.error_indicators == DEFAULT_ERROR_INDICATORS

    def test_config_empty_file_uses_defaults(self, tmp_path):
        """Test that empty config file falls back to defaults."""
        config_file = tmp_path / "empty.yaml"
        config_file.touch()

        parser = ResponseParser(config_path=str(config_file))

        assert parser.noise_patterns == DEFAULT_NOISE_PATTERNS
        assert parser.error_indicators == DEFAULT_ERROR_INDICATORS

    def test_config_partial_uses_defaults_for_missing(self, tmp_path):
        """Test partial config uses defaults for missing sections."""
        config_file = tmp_path / "partial.yaml"
        config_data = {"noise_patterns": ["custom_only"]}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        parser = ResponseParser(config_path=str(config_file))

        assert parser.noise_patterns == ["custom_only"]
        assert parser.error_indicators == DEFAULT_ERROR_INDICATORS

    def test_error_message_truncation(self):
        """Test that error lines are truncated at 500 chars."""
        parser = ResponseParser()
        long_error = "Error: " + "x" * 600
        stderr = long_error

        errors = parser._extract_real_errors(stderr)

        assert len(errors) == 1
        assert len(errors[0]) <= 500

    def test_unicode_handling(self):
        """Test that parser handles unicode in stderr correctly."""
        parser = ResponseParser()
        stderr = "Error: Unicode characters: 日本語 🎯 Ñoño"
        response = {"success": False, "stderr": stderr}

        result = parser.parse(response, "test_operation")

        assert result["success"] is False
        assert "日本語" in result["error_message"]

    def test_operation_type_in_error_message(self):
        """Test that operation type is included in error messages."""
        parser = ResponseParser()
        stderr = "Error: Test failed"
        response = {"success": False, "stderr": stderr}

        result = parser.parse(response, "run_tests")

        assert result["success"] is False
        assert "[run_tests]" in result["error_message"]

    def test_first_three_errors_in_message(self):
        """Test that error_message contains first 3 error lines."""
        parser = ResponseParser()
        stderr = """Error: First error
Error: Second error
Error: Third error
Error: Fourth error
Error: Fifth error
"""
        response = {"success": False, "stderr": stderr}

        result = parser.parse(response, "test_operation")

        assert result["success"] is False
        assert result["error_message"].count("Error:") == 3
        assert "First error" in result["error_message"]
        assert "Third error" in result["error_message"]
        assert "Fourth error" not in result["error_message"]

    def test_backward_compatibility_with_bool_success(self):
        """Test backward compatibility with old response format (success: bool)."""
        parser = ResponseParser()
        response = {"success": True}

        result = parser.parse(response, "test_operation")

        assert result["success"] is True
        assert result["status"] == "completed"

    def test_explicit_error_in_response(self):
        """Test handling of explicit error field in response."""
        parser = ResponseParser()
        response = {"error": "Timeout occurred", "success": False}

        result = parser.parse(response, "test_operation")

        assert result["success"] is False
        assert "[test_operation]" in result["error_message"]
        assert "Timeout occurred" in result["error_message"]

    def test_no_stderr_no_success_flag(self):
        """Test fail-safe behavior when no stderr and unclear success."""
        parser = ResponseParser()
        response = {}  # No clear success indicator

        result = parser.parse(response, "test_operation")

        assert result["success"] is False
        assert "Unknown error" in result["error_message"]
