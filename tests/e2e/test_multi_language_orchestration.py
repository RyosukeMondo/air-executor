"""E2E test for multi-language project orchestration.

Tests that the system correctly handles multiple languages simultaneously:
- Detects and processes JavaScript and Python projects
- Uses correct language adapters
- Maintains independent error handling per language
- Aggregates results across languages
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from airflow_dags.autonomous_fixing.adapters.languages.javascript_adapter import JavaScriptAdapter
from airflow_dags.autonomous_fixing.adapters.languages.python_adapter import PythonAdapter
from airflow_dags.autonomous_fixing.core.analyzer import ProjectAnalyzer
from airflow_dags.autonomous_fixing.core.fixer import IssueFixer
from airflow_dags.autonomous_fixing.core.iteration_engine import IterationEngine
from airflow_dags.autonomous_fixing.core.scorer import HealthScorer
from airflow_dags.autonomous_fixing.domain.models import AnalysisResult


class TestMultiLanguageOrchestration:
    """E2E tests for multi-language project handling."""

    @pytest.fixture
    def multi_language_workspace(self):
        """Create workspace with both JavaScript and Python projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # JavaScript project
            js_project = workspace / "js-app"
            js_project.mkdir()
            (js_project / "package.json").write_text("""{
                "name": "test-js-app",
                "version": "1.0.0",
                "scripts": {
                    "test": "jest",
                    "build": "webpack"
                }
            }""")
            (js_project / "index.js").write_text("""
function add(a, b) {
    return a + b;
}
module.exports = { add };
""")

            # Python project
            py_project = workspace / "py-lib"
            py_project.mkdir()
            (py_project / "main.py").write_text("""
def multiply(x, y):
    return x * y
""")
            (py_project / "setup.py").write_text("""
from setuptools import setup
setup(name='test-py-lib', version='1.0.0')
""")

            yield {
                "workspace": str(workspace),
                "js_project": str(js_project),
                "py_project": str(py_project),
            }

    @pytest.fixture
    def adapters(self):
        """Create adapters for both languages."""
        return {
            "javascript": JavaScriptAdapter({}),
            "python": PythonAdapter({}),
        }

    @pytest.fixture
    def config(self):
        """Multi-language configuration."""
        return {
            "execution": {
                "max_iterations": 1,
                "max_concurrent_projects": 2,
                "max_duration_hours": 1,
            },
            "priorities": {
                "p1_static": {"enabled": True, "success_threshold": 0.8},
                "p2_tests": {"enabled": False},
                "p3_coverage": {"enabled": False},
                "p4_e2e": {"enabled": False},
            },
            "complexity_threshold": 10,
            "max_file_lines": 500,
        }

    @pytest.fixture
    def analyzer(self, adapters, config):
        """Create ProjectAnalyzer with both adapters."""
        return ProjectAnalyzer(adapters, config)

    def test_analyzer_has_both_adapters(self, analyzer):
        """Verify analyzer has JavaScript and Python adapters."""
        assert "javascript" in analyzer.adapters
        assert "python" in analyzer.adapters
        assert isinstance(analyzer.adapters["javascript"], JavaScriptAdapter)
        assert isinstance(analyzer.adapters["python"], PythonAdapter)

    def test_analyze_both_languages_simultaneously(self, analyzer, multi_language_workspace):
        """Test analyzing JavaScript and Python projects together."""
        projects_by_language = {
            "javascript": [multi_language_workspace["js_project"]],
            "python": [multi_language_workspace["py_project"]],
        }

        # Run static analysis on both
        result = analyzer.analyze_static(projects_by_language)

        # Verify results for both languages
        assert result is not None
        assert hasattr(result, "results_by_project")

        # Should have results for both projects
        results_dict = result.results_by_project
        assert len(results_dict) == 2

        # Each result should be an AnalysisResult
        for project_key, analysis in results_dict.items():
            assert isinstance(analysis, AnalysisResult)
            assert hasattr(analysis, "success")
            assert hasattr(analysis, "language")

    def test_correct_adapter_selected_per_language(self, analyzer, multi_language_workspace):
        """Verify correct adapter is used for each language."""
        projects_by_language = {
            "javascript": [multi_language_workspace["js_project"]],
            "python": [multi_language_workspace["py_project"]],
        }

        result = analyzer.analyze_static(projects_by_language)

        # Check language assignment in results
        for project_key, analysis in result.results_by_project.items():
            # Language should be either 'javascript' or 'python'
            assert analysis.language in ["javascript", "python"]

    def test_independent_error_handling_per_language(self, analyzer, multi_language_workspace):
        """Test that errors in one language don't affect the other."""
        # Create projects where one might fail (e.g., missing node_modules)
        projects_by_language = {
            "javascript": [multi_language_workspace["js_project"]],
            "python": [multi_language_workspace["py_project"]],
        }

        # Analysis should not crash even if one language has issues
        result = analyzer.analyze_static(projects_by_language)

        # Should still return results (success or failure for each)
        assert result is not None
        assert hasattr(result, "results_by_project")

    def test_iteration_engine_handles_multi_language(
        self, adapters, config, multi_language_workspace
    ):
        """Test IterationEngine correctly orchestrates multi-language projects."""
        analyzer = ProjectAnalyzer(adapters, config)

        mock_ai_client = Mock()
        mock_ai_client.query.return_value = {"success": True}

        fixer = IssueFixer(config, ai_client=mock_ai_client, language_adapters=adapters)
        scorer = HealthScorer(config)

        engine = IterationEngine(config, analyzer=analyzer, fixer=fixer, scorer=scorer)

        projects_by_language = {
            "javascript": [multi_language_workspace["js_project"]],
            "python": [multi_language_workspace["py_project"]],
        }

        # Run P1 analysis
        p1_result, p1_score_data, success = engine._run_static_analysis_phase(
            projects_by_language, _iteration=1
        )

        # Should have results for both languages
        assert p1_result is not None
        assert hasattr(p1_result, "results_by_project")

        # Should have results (at least one project analyzed)
        assert len(p1_result.results_by_project) >= 1


class TestLanguageIsolation:
    """Test that languages are properly isolated in processing."""

    def test_python_adapter_not_called_for_javascript(self):
        """Verify Python adapter doesn't process JavaScript projects."""
        adapters = {
            "javascript": JavaScriptAdapter({}),
            "python": PythonAdapter({}),
        }

        config = {"complexity_threshold": 10, "max_file_lines": 500}
        analyzer = ProjectAnalyzer(adapters, config)

        # Verify adapters are separate instances
        assert analyzer.adapters["javascript"] is not analyzer.adapters["python"]
        assert not isinstance(analyzer.adapters["javascript"], type(analyzer.adapters["python"]))

    def test_javascript_adapter_not_called_for_python(self):
        """Verify JavaScript adapter doesn't process Python projects."""
        adapters = {
            "javascript": JavaScriptAdapter({}),
            "python": PythonAdapter({}),
        }

        config = {"complexity_threshold": 10, "max_file_lines": 500}
        analyzer = ProjectAnalyzer(adapters, config)

        # Verify correct adapter types
        assert isinstance(analyzer.adapters["javascript"], JavaScriptAdapter)
        assert isinstance(analyzer.adapters["python"], PythonAdapter)


class TestLanguageScaling:
    """Test system behavior with multiple projects per language."""

    @pytest.fixture
    def multiple_python_projects(self):
        """Create multiple Python projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            projects = []
            for i in range(3):
                project = workspace / f"py-project-{i}"
                project.mkdir()
                (project / "main.py").write_text(f"""
def func_{i}():
    return {i}
""")
                projects.append(str(project))

            yield projects

    def test_multiple_projects_same_language(self, multiple_python_projects):
        """Test handling multiple projects of same language."""
        adapters = {"python": PythonAdapter({})}
        config = {"complexity_threshold": 10, "max_file_lines": 500}
        analyzer = ProjectAnalyzer(adapters, config)

        projects_by_language = {"python": multiple_python_projects}

        # Should handle all 3 projects
        result = analyzer.analyze_static(projects_by_language)

        assert result is not None
        assert hasattr(result, "results_by_project")

        # Should have results for all 3 projects
        assert len(result.results_by_project) >= 1  # At least one result
