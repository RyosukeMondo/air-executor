"""Unit tests for adapter interface compliance.

These tests verify that all language adapters properly implement the ILanguageAdapter interface
and that methods are called correctly across the codebase.
"""

import inspect

import pytest

from airflow_dags.autonomous_fixing.adapters.languages.base import LanguageAdapter
from airflow_dags.autonomous_fixing.adapters.languages.javascript_adapter import JavaScriptAdapter
from airflow_dags.autonomous_fixing.adapters.languages.python_adapter import PythonAdapter
from airflow_dags.autonomous_fixing.domain.interfaces.language_adapter import ILanguageAdapter
from airflow_dags.autonomous_fixing.domain.models import AnalysisResult


class TestAdapterInterfaceCompliance:
    """Test that all adapters implement the required interface methods."""

    @pytest.fixture
    def adapters(self):
        """Get all adapter classes to test."""
        return [JavaScriptAdapter, PythonAdapter]

    def test_all_adapters_inherit_from_base(self, adapters):
        """All adapters must inherit from LanguageAdapter."""
        for adapter_class in adapters:
            assert issubclass(
                adapter_class, LanguageAdapter
            ), f"{adapter_class.__name__} must inherit from LanguageAdapter"

    def test_all_adapters_implement_interface(self, adapters):
        """All adapters must implement ILanguageAdapter."""
        for adapter_class in adapters:
            assert issubclass(
                adapter_class, ILanguageAdapter
            ), f"{adapter_class.__name__} must implement ILanguageAdapter"

    def test_required_methods_exist(self, adapters):
        """All adapters must have required methods from interface."""
        required_methods = [
            "language_name",
            "project_markers",
            "detect_projects",
            "static_analysis",
            "run_tests",
            "analyze_coverage",
            "run_e2e_tests",
            "validate_tools",
            "parse_errors",
            "calculate_complexity",
            "run_type_check",  # Added after discovering mismatch
            "run_build",  # Added after discovering mismatch
        ]

        for adapter_class in adapters:
            adapter_methods = dir(adapter_class)
            for method in required_methods:
                assert (
                    method in adapter_methods
                ), f"{adapter_class.__name__} missing required method: {method}"

    def test_method_signatures_match_interface(self, adapters):
        """Method signatures must match the interface definition."""
        interface_methods = {
            name: method
            for name, method in inspect.getmembers(ILanguageAdapter, predicate=inspect.isfunction)
            if not name.startswith("_")
        }

        for adapter_class in adapters:
            for method_name, interface_method in interface_methods.items():
                if hasattr(adapter_class, method_name):
                    adapter_method = getattr(adapter_class, method_name)

                    # Get signatures
                    interface_sig = inspect.signature(interface_method)
                    adapter_sig = inspect.signature(adapter_method)

                    # Compare parameter names (excluding 'self')
                    interface_params = [p for p in interface_sig.parameters.keys() if p != "self"]
                    adapter_params = [p for p in adapter_sig.parameters.keys() if p != "self"]

                    assert interface_params == adapter_params, (
                        f"{adapter_class.__name__}.{method_name} signature mismatch. "
                        f"Expected: {interface_params}, Got: {adapter_params}"
                    )

    def test_type_check_returns_analysis_result(self, adapters):
        """run_type_check must return AnalysisResult."""
        for adapter_class in adapters:
            method = getattr(adapter_class, "run_type_check")
            sig = inspect.signature(method)
            return_annotation = sig.return_annotation

            assert (
                return_annotation == AnalysisResult or str(return_annotation) == "AnalysisResult"
            ), f"{adapter_class.__name__}.run_type_check must return AnalysisResult"

    def test_build_returns_analysis_result(self, adapters):
        """run_build must return AnalysisResult."""
        for adapter_class in adapters:
            method = getattr(adapter_class, "run_build")
            sig = inspect.signature(method)
            return_annotation = sig.return_annotation

            assert (
                return_annotation == AnalysisResult or str(return_annotation) == "AnalysisResult"
            ), f"{adapter_class.__name__}.run_build must return AnalysisResult"

    def test_adapter_instantiation(self, adapters):
        """Adapters can be instantiated with config dict."""
        for adapter_class in adapters:
            try:
                adapter = adapter_class({})
                assert isinstance(adapter, ILanguageAdapter)
            except Exception as e:
                pytest.fail(f"{adapter_class.__name__} failed to instantiate: {e}")

    def test_adapters_not_abstract(self, adapters):
        """Adapters must not be abstract - all abstract methods must be implemented."""
        for adapter_class in adapters:
            # Check if any abstract methods remain unimplemented
            abstract_methods = {
                name
                for name in dir(adapter_class)
                if getattr(getattr(adapter_class, name, None), "__isabstractmethod__", False)
            }

            assert (
                not abstract_methods
            ), f"{adapter_class.__name__} has unimplemented abstract methods: {abstract_methods}"

    def test_imported_adapter_matches_file_adapter(self):
        """Ensure __init__.py imports the correct PythonAdapter from python_adapter.py."""
        # Import from __init__.py (the way orchestrator does it)
        from airflow_dags.autonomous_fixing.adapters.languages import PythonAdapter as InitPythonAdapter

        # Import directly from file
        from airflow_dags.autonomous_fixing.adapters.languages.python_adapter import (
            PythonAdapter as FilePythonAdapter,
        )

        # They should be the same class
        assert (
            InitPythonAdapter is FilePythonAdapter
        ), "PythonAdapter from __init__.py doesn't match python_adapter.py - wrong import path!"

        # Both should be instantiable
        try:
            adapter1 = InitPythonAdapter({})
            adapter2 = FilePythonAdapter({})
            assert isinstance(adapter1, ILanguageAdapter)
            assert isinstance(adapter2, ILanguageAdapter)
        except TypeError as e:
            pytest.fail(f"PythonAdapter cannot be instantiated: {e}")


class TestAnalysisResultCompliance:
    """Test that AnalysisResult has required attributes."""

    def test_analysis_result_has_success_attribute(self):
        """AnalysisResult must have a 'success' attribute."""
        result = AnalysisResult(language="test", phase="test", project_path="/test")
        assert hasattr(result, "success"), "AnalysisResult missing 'success' attribute"
        assert isinstance(result.success, bool), "'success' must be a boolean"

    def test_analysis_result_has_errors_attribute(self):
        """AnalysisResult must have an 'errors' attribute."""
        result = AnalysisResult(language="test", phase="test", project_path="/test")
        assert hasattr(result, "errors"), "AnalysisResult missing 'errors' attribute"
        assert isinstance(result.errors, list), "'errors' must be a list"

    def test_analysis_result_supports_error_message(self):
        """AnalysisResult must support error_message for build failures."""
        result = AnalysisResult(language="test", phase="build", project_path="/test")
        result.error_message = "Build failed"
        assert hasattr(result, "error_message"), "AnalysisResult should support error_message"


class TestComponentInterfaceCompliance:
    """Test that components use adapters correctly."""

    def test_iteration_engine_uses_analyzer_adapters(self):
        """IterationEngine should use self.analyzer.adapters dict."""

        # Check the source code for correct usage
        import airflow_dags.autonomous_fixing.core.iteration_engine as engine_module

        source = inspect.getsource(engine_module)

        # Should NOT have self.analyzer._get_adapter
        assert (
            "self.analyzer._get_adapter" not in source
        ), "IterationEngine incorrectly calls self.analyzer._get_adapter - should use self.analyzer.adapters"

        # Should have self.analyzer.adapters
        assert (
            "self.analyzer.adapters" in source
        ), "IterationEngine should use self.analyzer.adapters to access adapters"

    def test_hook_manager_uses_adapter_methods(self):
        """HookLevelManager should call run_type_check and run_build on adapters."""

        import airflow_dags.autonomous_fixing.core.hook_level_manager as hook_module

        source = inspect.getsource(hook_module)

        # Must call run_type_check
        assert "run_type_check" in source, "HookLevelManager should call adapter.run_type_check"

        # Must call run_build
        assert "run_build" in source, "HookLevelManager should call adapter.run_build"

    def test_no_get_adapter_method_on_analyzer(self):
        """ProjectAnalyzer should NOT have a _get_adapter method."""
        from airflow_dags.autonomous_fixing.core.analyzer import ProjectAnalyzer

        assert not hasattr(
            ProjectAnalyzer, "_get_adapter"
        ), "ProjectAnalyzer should not have _get_adapter method - use .adapters dict instead"

    def test_analyzer_has_adapters_dict(self):
        """ProjectAnalyzer should have an 'adapters' attribute."""
        from airflow_dags.autonomous_fixing.core.analyzer import ProjectAnalyzer

        # Check __init__ signature
        init_source = inspect.getsource(ProjectAnalyzer.__init__)
        assert "self.adapters" in init_source, "ProjectAnalyzer.__init__ should set self.adapters"
