"""Unit tests for new configuration classes.

Tests validation, defaults, and test-specific configurations for:
- HookLevelConfig
- AnalysisDelegateConfig
- PromptManagerConfig
"""

from pathlib import Path

from airflow_dags.autonomous_fixing.config import (
    AnalysisDelegateConfig,
    HookLevelConfig,
    PromptManagerConfig,
)


class TestHookLevelConfig:
    """Test HookLevelConfig functionality."""

    def test_default_configuration(self):
        """Test default configuration paths."""
        config = HookLevelConfig()

        assert config.config_path == Path("config/hook-levels.yaml")
        assert config.cache_dir == Path("config/precommit-cache")

    def test_for_testing_with_tmp_path(self, tmp_path):
        """Test isolated test configuration."""
        config = HookLevelConfig.for_testing(tmp_path)

        assert config.config_path == tmp_path / "hook-levels.yaml"
        assert config.cache_dir == tmp_path / "hook-cache"

    def test_for_testing_without_tmp_path(self):
        """Test test configuration with defaults when no tmp_path provided."""
        config = HookLevelConfig.for_testing()

        assert config.config_path == Path("config/hook-levels.yaml")
        assert config.cache_dir == Path("config/precommit-cache")

    def test_custom_paths(self, tmp_path):
        """Test custom path configuration."""
        custom_config = tmp_path / "custom-hooks.yaml"
        custom_cache = tmp_path / "custom-cache"

        config = HookLevelConfig(config_path=custom_config, cache_dir=custom_cache)

        assert config.config_path == custom_config
        assert config.cache_dir == custom_cache


class TestAnalysisDelegateConfig:
    """Test AnalysisDelegateConfig functionality."""

    def test_default_configuration(self):
        """Test default configuration paths."""
        config = AnalysisDelegateConfig()

        assert config.analysis_cache_dir == Path("config/analysis-cache")
        assert config.hook_cache_dir == Path("config/precommit-cache")
        assert config.test_cache_dir == Path("config/test-cache")
        assert config.wrapper_settings["path"] == "scripts/claude_wrapper.py"
        assert config.wrapper_settings["python_executable"] == "python"

    def test_for_testing_with_tmp_path(self, tmp_path):
        """Test isolated test configuration."""
        config = AnalysisDelegateConfig.for_testing(tmp_path)

        assert config.analysis_cache_dir == tmp_path / "analysis-cache"
        assert config.hook_cache_dir == tmp_path / "hook-cache"
        assert config.test_cache_dir == tmp_path / "test-cache"

    def test_for_testing_without_tmp_path(self):
        """Test test configuration with defaults when no tmp_path provided."""
        config = AnalysisDelegateConfig.for_testing()

        assert config.analysis_cache_dir == Path("config/analysis-cache")
        assert config.hook_cache_dir == Path("config/precommit-cache")
        assert config.test_cache_dir == Path("config/test-cache")

    def test_custom_paths(self, tmp_path):
        """Test custom path configuration."""
        custom_analysis = tmp_path / "custom-analysis"
        custom_hooks = tmp_path / "custom-hooks"
        custom_tests = tmp_path / "custom-tests"
        custom_wrapper = {"path": "custom/wrapper.py", "python_executable": "python3"}

        config = AnalysisDelegateConfig(
            analysis_cache_dir=custom_analysis,
            hook_cache_dir=custom_hooks,
            test_cache_dir=custom_tests,
            wrapper_settings=custom_wrapper,
        )

        assert config.analysis_cache_dir == custom_analysis
        assert config.hook_cache_dir == custom_hooks
        assert config.test_cache_dir == custom_tests
        assert config.wrapper_settings["path"] == "custom/wrapper.py"


class TestPromptManagerConfig:
    """Test PromptManagerConfig functionality."""

    def test_default_configuration(self):
        """Test default configuration paths."""
        config = PromptManagerConfig()

        assert config.prompts_config_path == Path("config/prompts.yaml")

    def test_for_testing_with_tmp_path(self, tmp_path):
        """Test isolated test configuration."""
        config = PromptManagerConfig.for_testing(tmp_path)

        assert config.prompts_config_path == tmp_path / "prompts.yaml"

    def test_for_testing_without_tmp_path(self):
        """Test test configuration with defaults when no tmp_path provided."""
        config = PromptManagerConfig.for_testing()

        assert config.prompts_config_path == Path("config/prompts.yaml")

    def test_custom_path(self, tmp_path):
        """Test custom path configuration."""
        custom_prompts = tmp_path / "custom-prompts.yaml"

        config = PromptManagerConfig(prompts_config_path=custom_prompts)

        assert config.prompts_config_path == custom_prompts


class TestConfigIntegration:
    """Test configs work together for complete isolation."""

    def test_complete_isolation(self, tmp_path):
        """Test that all configs can be isolated together."""
        # Create all configs with same base directory
        hook_config = HookLevelConfig.for_testing(tmp_path)
        delegate_config = AnalysisDelegateConfig.for_testing(tmp_path)
        prompt_config = PromptManagerConfig.for_testing(tmp_path)

        # Verify all paths are under tmp_path
        assert str(hook_config.config_path).startswith(str(tmp_path))
        assert str(hook_config.cache_dir).startswith(str(tmp_path))
        assert str(delegate_config.analysis_cache_dir).startswith(str(tmp_path))
        assert str(delegate_config.hook_cache_dir).startswith(str(tmp_path))
        assert str(delegate_config.test_cache_dir).startswith(str(tmp_path))
        assert str(prompt_config.prompts_config_path).startswith(str(tmp_path))

        # Verify no path collisions
        all_paths = [
            hook_config.config_path,
            hook_config.cache_dir,
            delegate_config.analysis_cache_dir,
            delegate_config.hook_cache_dir,
            delegate_config.test_cache_dir,
            prompt_config.prompts_config_path,
        ]
        # Check that hook_cache_dir appears twice (expected) but no other duplicates
        assert len([p for p in all_paths if p == hook_config.cache_dir]) == 2  # Expected shared
        assert len([p for p in all_paths if p == delegate_config.analysis_cache_dir]) == 1
        assert len([p for p in all_paths if p == prompt_config.prompts_config_path]) == 1
