"""E2E tests for orchestrator adapter flow.

These tests verify the complete flow from orchestrator through iteration engine,
analyzer, fixer, and scorer, ensuring all components interact correctly with adapters.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from airflow_dags.autonomous_fixing.adapters.languages.javascript_adapter import JavaScriptAdapter
from airflow_dags.autonomous_fixing.adapters.languages.python_adapter import PythonAdapter
from airflow_dags.autonomous_fixing.core.analyzer import ProjectAnalyzer
from airflow_dags.autonomous_fixing.core.fixer import IssueFixer
from airflow_dags.autonomous_fixing.core.iteration_engine import IterationEngine
from airflow_dags.autonomous_fixing.core.scorer import HealthScorer
from airflow_dags.autonomous_fixing.domain.models import AnalysisResult


class TestOrchestratorE2E:
    """End-to-end tests for the full orchestration flow."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with test projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create JavaScript project
            js_project = workspace / "js-project"
            js_project.mkdir()
            (js_project / "package.json").write_text("""{
                "name": "test-js",
                "version": "1.0.0",
                "scripts": {
                    "test": "echo 'tests pass'",
                    "build": "echo 'build success'"
                }
            }""")
            (js_project / "index.js").write_text('console.log("hello");')

            # Create Python project
            py_project = workspace / "py-project"
            py_project.mkdir()
            (py_project / "main.py").write_text('print("hello")')
            (py_project / "setup.py").write_text("# setup")

            yield {
                "workspace": str(workspace),
                "js_project": str(js_project),
                "py_project": str(py_project),
            }

    @pytest.fixture
    def language_adapters(self):
        """Create language adapters."""
        return {"javascript": JavaScriptAdapter({}), "python": PythonAdapter({})}

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {
            "execution": {"max_iterations": 2, "max_concurrent_projects": 2},
            "complexity_threshold": 10,
            "max_file_lines": 500,
        }

    @pytest.fixture
    def analyzer(self, language_adapters, config):
        """Create ProjectAnalyzer."""
        return ProjectAnalyzer(language_adapters, config)

    @pytest.fixture
    def fixer(self, config):
        """Create IssueFixer with mocked Claude client."""
        with patch("airflow_dags.autonomous_fixing.core.fixer.ClaudeClient") as mock_claude:
            mock_client = Mock()
            mock_claude.return_value = mock_client
            fixer = IssueFixer(config)
            fixer.claude = mock_client
            return fixer

    @pytest.fixture
    def scorer(self, config):
        """Create HealthScorer."""
        return HealthScorer(config)

    @pytest.fixture
    def iteration_engine(self, analyzer, fixer, scorer, config):
        """Create IterationEngine with all components."""
        return IterationEngine(analyzer, fixer, scorer, config)

    def test_analyzer_has_adapters_dict(self, analyzer):
        """ProjectAnalyzer must have adapters as a dict, not a method."""
        assert hasattr(analyzer, "adapters"), "Analyzer must have 'adapters' attribute"
        assert isinstance(analyzer.adapters, dict), "adapters must be a dictionary"
        assert not hasattr(analyzer, "_get_adapter"), "Should NOT have _get_adapter method"

    def test_analyzer_adapters_contain_language_instances(self, analyzer):
        """Adapters dict must contain actual adapter instances."""
        assert "javascript" in analyzer.adapters
        assert "python" in analyzer.adapters
        assert isinstance(analyzer.adapters["javascript"], JavaScriptAdapter)
        assert isinstance(analyzer.adapters["python"], PythonAdapter)

    def test_static_analysis_flow(self, analyzer, temp_workspace):
        """Test P1 static analysis flow through analyzer."""
        projects_by_language = {
            "javascript": [temp_workspace["js_project"]],
            "python": [temp_workspace["py_project"]],
        }

        # Run static analysis
        result = analyzer.analyze_static(projects_by_language)

        # Verify result structure
        assert hasattr(result, "results_by_project")
        assert isinstance(result.results_by_project, dict)

        # Verify both projects were analyzed
        assert len(result.results_by_project) == 2

        # Verify each result is an AnalysisResult
        for key, analysis in result.results_by_project.items():
            assert isinstance(analysis, AnalysisResult)
            assert hasattr(analysis, "success")
            assert hasattr(analysis, "errors")

    def test_iteration_engine_upgrade_hooks_flow(self, iteration_engine, temp_workspace):
        """Test hook upgrade flow using correct adapter access."""
        projects_by_language = {"javascript": [temp_workspace["js_project"]]}
        p1_score_data = {"score": 0.85}

        # Mock hook manager
        iteration_engine.hook_manager = Mock()
        iteration_engine.hook_manager.upgrade_after_gate_passed = Mock()

        # Mock adapter methods
        js_adapter = iteration_engine.analyzer.adapters["javascript"]
        with (
            patch.object(js_adapter, "run_type_check") as mock_type_check,
            patch.object(js_adapter, "run_build") as mock_build,
        ):
            mock_type_check.return_value = AnalysisResult(
                language="javascript",
                phase="type_check",
                project_path=temp_workspace["js_project"],
                success=True,
                errors=[],
            )

            mock_build.return_value = AnalysisResult(
                language="javascript",
                phase="build",
                project_path=temp_workspace["js_project"],
                success=True,
                errors=[],
            )

            # This should not raise AttributeError about _get_adapter
            try:
                iteration_engine._upgrade_hooks_after_p1(projects_by_language, p1_score_data)
                # Verify hook manager was called
                assert iteration_engine.hook_manager.upgrade_after_gate_passed.called
            except AttributeError as e:
                if "_get_adapter" in str(e):
                    pytest.fail(f"Should use adapters dict, not _get_adapter: {e}")
                raise

    def test_full_p1_gate_flow(self, iteration_engine, temp_workspace):
        """Test complete P1 gate flow including hook upgrade."""
        projects_by_language = {"javascript": [temp_workspace["js_project"]]}

        # Mock fixer and hook manager
        iteration_engine.fixer.configure_precommit_hooks = Mock(return_value=True)
        iteration_engine.hook_manager = Mock()
        iteration_engine.hook_manager.upgrade_after_gate_passed = Mock()

        # Mock adapter methods for hook verification
        js_adapter = iteration_engine.analyzer.adapters["javascript"]
        with (
            patch.object(js_adapter, "run_type_check") as mock_type_check,
            patch.object(js_adapter, "run_build") as mock_build,
        ):
            mock_type_check.return_value = AnalysisResult(
                language="javascript",
                phase="type_check",
                project_path=temp_workspace["js_project"],
                success=True,
                errors=[],
            )

            mock_build.return_value = AnalysisResult(
                language="javascript",
                phase="build",
                project_path=temp_workspace["js_project"],
                success=True,
                errors=[],
            )

            # Run hook setup phase
            iteration_engine._run_hook_setup_phase(projects_by_language)

            # Verify hooks were configured
            assert iteration_engine.fixer.configure_precommit_hooks.called

    def test_adapter_method_call_consistency(self, analyzer):
        """Verify all adapters respond to the same method calls."""
        required_methods = [
            "static_analysis",
            "run_tests",
            "analyze_coverage",
            "run_e2e_tests",
            "run_type_check",
            "run_build",
            "validate_tools",
            "parse_errors",
            "calculate_complexity",
        ]

        for lang_name, adapter in analyzer.adapters.items():
            for method_name in required_methods:
                assert hasattr(
                    adapter, method_name
                ), f"{lang_name} adapter missing method: {method_name}"
                assert callable(
                    getattr(adapter, method_name)
                ), f"{lang_name} adapter {method_name} is not callable"

    def test_no_attributeerror_on_adapter_access(self, iteration_engine, temp_workspace):
        """Ensure no AttributeError when accessing adapters throughout the flow."""
        projects_by_language = {
            "javascript": [temp_workspace["js_project"]],
            "python": [temp_workspace["py_project"]],
        }

        # Test analyzer adapter access
        for lang in projects_by_language.keys():
            adapter = iteration_engine.analyzer.adapters.get(lang)
            assert adapter is not None, f"Should get adapter for {lang}"

        # Test that we can call methods on adapters
        js_adapter = iteration_engine.analyzer.adapters["javascript"]
        py_adapter = iteration_engine.analyzer.adapters["python"]

        # These should not raise AttributeError
        assert callable(js_adapter.run_type_check)
        assert callable(js_adapter.run_build)
        assert callable(py_adapter.run_type_check)
        assert callable(py_adapter.run_build)


class TestAdapterMethodReturnValues:
    """Test that adapter methods return correct types."""

    @pytest.fixture
    def js_adapter(self):
        return JavaScriptAdapter({})

    @pytest.fixture
    def py_adapter(self):
        return PythonAdapter({})

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "test.py").write_text("x = 1")
            yield str(project_path)

    def test_all_adapter_methods_return_analysis_result(self, js_adapter, py_adapter, temp_project):
        """All analysis methods must return AnalysisResult."""
        methods_to_test = [
            ("run_type_check", (temp_project,)),
            ("run_build", (temp_project,)),
        ]

        for adapter in [js_adapter, py_adapter]:
            for method_name, args in methods_to_test:
                method = getattr(adapter, method_name)
                result = method(*args)

                assert isinstance(result, AnalysisResult), (
                    f"{adapter.language_name}.{method_name} must return AnalysisResult, "
                    f"got {type(result)}"
                )

                # Verify required attributes exist
                assert hasattr(result, "success"), f"{method_name} result missing 'success'"
                assert hasattr(result, "errors"), f"{method_name} result missing 'errors'"
                assert hasattr(result, "language"), f"{method_name} result missing 'language'"
                assert hasattr(result, "phase"), f"{method_name} result missing 'phase'"
                assert hasattr(
                    result, "project_path"
                ), f"{method_name} result missing 'project_path'"
