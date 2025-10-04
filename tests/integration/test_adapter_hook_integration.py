"""Integration tests for adapter and hook manager integration.

These tests verify that adapters work correctly with HookLevelManager
and that the interface contract is honored in real usage.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from airflow_dags.autonomous_fixing.adapters.languages.javascript_adapter import JavaScriptAdapter
from airflow_dags.autonomous_fixing.adapters.languages.python_adapter import PythonAdapter
from airflow_dags.autonomous_fixing.core.hook_level_manager import HookLevelManager
from airflow_dags.autonomous_fixing.domain.models import AnalysisResult


class TestAdapterHookIntegration:
    """Test integration between language adapters and HookLevelManager."""

    @pytest.fixture
    def hook_manager(self):
        """Create HookLevelManager instance."""
        return HookLevelManager()

    @pytest.fixture
    def js_adapter(self):
        """Create JavaScript adapter instance."""
        return JavaScriptAdapter({})

    @pytest.fixture
    def py_adapter(self):
        """Create Python adapter instance."""
        return PythonAdapter({})

    @pytest.fixture
    def temp_js_project(self):
        """Create a temporary JavaScript project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create package.json
            (project_path / "package.json").write_text("""{
                "name": "test-project",
                "version": "1.0.0",
                "scripts": {
                    "build": "echo 'build success'",
                    "test": "echo 'test success'"
                }
            }""")

            # Create tsconfig.json
            (project_path / "tsconfig.json").write_text("""{
                "compilerOptions": {
                    "target": "ES2020"
                }
            }""")

            # Create a simple source file
            (project_path / "index.ts").write_text("const x: number = 42;")

            yield str(project_path)

    @pytest.fixture
    def temp_py_project(self):
        """Create a temporary Python project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create source file
            (project_path / "main.py").write_text("x: int = 42\nprint(x)")

            # Create setup.py
            (project_path / "setup.py").write_text("# setup.py")

            yield str(project_path)

    def test_js_adapter_type_check_returns_analysis_result(self, js_adapter, temp_js_project):
        """JavaScript adapter run_type_check returns proper AnalysisResult."""
        result = js_adapter.run_type_check(temp_js_project)

        assert isinstance(result, AnalysisResult), "Must return AnalysisResult"
        assert hasattr(result, "success"), "Must have success attribute"
        assert hasattr(result, "errors"), "Must have errors attribute"
        assert isinstance(result.success, bool), "success must be boolean"
        assert isinstance(result.errors, list), "errors must be list"

    def test_js_adapter_build_returns_analysis_result(self, js_adapter, temp_js_project):
        """JavaScript adapter run_build returns proper AnalysisResult."""
        result = js_adapter.run_build(temp_js_project)

        assert isinstance(result, AnalysisResult), "Must return AnalysisResult"
        assert hasattr(result, "success"), "Must have success attribute"
        assert hasattr(result, "errors"), "Must have errors attribute"
        assert isinstance(result.success, bool), "success must be boolean"

    def test_py_adapter_type_check_returns_analysis_result(self, py_adapter, temp_py_project):
        """Python adapter run_type_check returns proper AnalysisResult."""
        result = py_adapter.run_type_check(temp_py_project)

        assert isinstance(result, AnalysisResult), "Must return AnalysisResult"
        assert hasattr(result, "success"), "Must have success attribute"
        assert hasattr(result, "errors"), "Must have errors attribute"
        assert isinstance(result.success, bool), "success must be boolean"

    def test_py_adapter_build_returns_analysis_result(self, py_adapter, temp_py_project):
        """Python adapter run_build returns proper AnalysisResult."""
        result = py_adapter.run_build(temp_py_project)

        assert isinstance(result, AnalysisResult), "Must return AnalysisResult"
        assert hasattr(result, "success"), "Must have success attribute"
        assert isinstance(result.success, bool), "success must be boolean"

    def test_hook_manager_can_verify_type_check(self, hook_manager, js_adapter, temp_js_project):
        """HookLevelManager can verify type checking with adapter."""
        # Mock the type check to return success
        with patch.object(js_adapter, "run_type_check") as mock_type_check:
            mock_type_check.return_value = AnalysisResult(
                language="javascript",
                phase="type_check",
                project_path=temp_js_project,
                success=True,
                errors=[],
            )

            valid, reason = hook_manager._verify_type_check_and_build(temp_js_project, js_adapter)

            assert mock_type_check.called, "Should call adapter.run_type_check"
            mock_type_check.assert_called_once_with(temp_js_project)

    def test_hook_manager_can_verify_build(self, hook_manager, js_adapter, temp_js_project):
        """HookLevelManager can verify build with adapter."""
        # Mock both type check and build
        with (
            patch.object(js_adapter, "run_type_check") as mock_type_check,
            patch.object(js_adapter, "run_build") as mock_build,
        ):
            mock_type_check.return_value = AnalysisResult(
                language="javascript",
                phase="type_check",
                project_path=temp_js_project,
                success=True,
                errors=[],
            )

            mock_build.return_value = AnalysisResult(
                language="javascript",
                phase="build",
                project_path=temp_js_project,
                success=True,
                errors=[],
            )

            valid, reason = hook_manager._verify_type_check_and_build(temp_js_project, js_adapter)

            assert mock_build.called, "Should call adapter.run_build"
            mock_build.assert_called_once_with(temp_js_project)

    def test_hook_manager_detects_type_check_failure(
        self, hook_manager, js_adapter, temp_js_project
    ):
        """HookLevelManager detects type check failures."""
        with patch.object(js_adapter, "run_type_check") as mock_type_check:
            mock_type_check.return_value = AnalysisResult(
                language="javascript",
                phase="type_check",
                project_path=temp_js_project,
                success=False,
                errors=[{"message": "Type error"}],
            )

            valid, reason = hook_manager._verify_type_check_and_build(temp_js_project, js_adapter)

            assert not valid, "Should detect type check failure"
            assert "Type checking failed" in reason, "Should provide failure reason"

    def test_hook_manager_detects_build_failure(self, hook_manager, js_adapter, temp_js_project):
        """HookLevelManager detects build failures."""
        with (
            patch.object(js_adapter, "run_type_check") as mock_type_check,
            patch.object(js_adapter, "run_build") as mock_build,
        ):
            mock_type_check.return_value = AnalysisResult(
                language="javascript",
                phase="type_check",
                project_path=temp_js_project,
                success=True,
                errors=[],
            )

            mock_build.return_value = AnalysisResult(
                language="javascript",
                phase="build",
                project_path=temp_js_project,
                success=False,
                errors=[],
            )
            mock_build.return_value.error_message = "Build failed"

            valid, reason = hook_manager._verify_type_check_and_build(temp_js_project, js_adapter)

            assert not valid, "Should detect build failure"
            assert "Build failed" in reason, "Should provide failure reason"

    def test_adapter_error_message_attribute(self, js_adapter, temp_js_project):
        """Build failures should set error_message attribute."""
        # Create a project that will fail build
        project_path = Path(temp_js_project)
        package_json = project_path / "package.json"
        package_json.write_text("""{
            "name": "test-project",
            "scripts": {
                "build": "exit 1"
            }
        }""")

        result = js_adapter.run_build(temp_js_project)

        assert not result.success, "Build should fail"
        assert hasattr(result, "error_message"), "Should have error_message attribute on failure"


class TestIterationEngineAdapterAccess:
    """Test that IterationEngine accesses adapters correctly."""

    @pytest.fixture
    def mock_analyzer(self):
        """Create mock ProjectAnalyzer with adapters dict."""
        analyzer = Mock()
        analyzer.adapters = {"javascript": JavaScriptAdapter({}), "python": PythonAdapter({})}
        return analyzer

    @pytest.fixture
    def iteration_engine(self, mock_analyzer):
        """Create IterationEngine with mocked components."""
        from airflow_dags.autonomous_fixing.core.iteration_engine import IterationEngine

        mock_fixer = Mock()
        mock_scorer = Mock()
        config = {"execution": {"max_iterations": 5}}

        return IterationEngine(mock_analyzer, mock_fixer, mock_scorer, config)

    def test_iteration_engine_accesses_adapters_via_dict(self, iteration_engine):
        """IterationEngine should access adapters via self.analyzer.adapters dict."""
        # Verify the analyzer has adapters attribute
        assert hasattr(
            iteration_engine.analyzer, "adapters"
        ), "Analyzer should have 'adapters' attribute"
        assert isinstance(
            iteration_engine.analyzer.adapters, dict
        ), "Adapters should be a dictionary"

    def test_upgrade_hooks_uses_correct_adapter_access(self, iteration_engine, mock_analyzer):
        """_upgrade_hooks_after_p1 should use adapters.get() not _get_adapter()."""
        projects_by_language = {"javascript": ["/test/project1"]}
        p1_score_data = {"score": 0.85}

        # Mock the hook manager
        iteration_engine.hook_manager = Mock()
        iteration_engine.hook_manager.upgrade_after_gate_passed = Mock()

        # This should not raise AttributeError
        try:
            iteration_engine._upgrade_hooks_after_p1(projects_by_language, p1_score_data)
        except AttributeError as e:
            if "_get_adapter" in str(e):
                pytest.fail("Should not call _get_adapter - use adapters dict instead")
            raise
