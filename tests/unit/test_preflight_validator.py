"""Unit tests for PreflightValidator."""

import pytest
import time
import yaml
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from airflow_dags.autonomous_fixing.core.setup_tracker import SetupTracker
from airflow_dags.autonomous_fixing.core.validators.preflight import PreflightValidator


class TestPreflightValidatorHookConfig:
    """Test hook configuration validation."""

    @pytest.fixture
    def mock_tracker(self):
        """Create mock SetupTracker."""
        tracker = Mock(spec=SetupTracker)
        tracker.is_setup_complete.return_value = False
        return tracker

    @pytest.fixture
    def validator(self, mock_tracker):
        """Create PreflightValidator with mock tracker."""
        return PreflightValidator(mock_tracker)

    def test_can_skip_when_state_not_tracked(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when state not tracked."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is False
        assert "setup state not tracked" in reason
        mock_tracker.is_setup_complete.assert_called_once()

    def test_can_skip_when_cache_missing(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache file missing."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        # State tracked, but no cache
        mock_tracker.is_setup_complete.return_value = True

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is False
        assert "cache file missing" in reason

    def test_can_skip_when_cache_stale(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache is stale (>7 days)."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create stale cache file (8 days old)
        cache_dir = Path('config/precommit-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-hooks.yaml'

        cache_data = {'hook_framework': {'installed': True}}
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        # Set modification time to 8 days ago
        import os
        eight_days_ago = time.time() - (8 * 24 * 60 * 60)
        os.utime(cache_file, (eight_days_ago, eight_days_ago))

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is False
        assert "cache stale" in reason
        assert "8d old" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_when_cache_invalid_yaml(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache has invalid YAML."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create cache with invalid YAML
        cache_dir = Path('config/precommit-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-hooks.yaml'
        cache_file.write_text("invalid: yaml: structure: {")

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is False
        assert "cache invalid" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_when_cache_missing_required_field(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache missing hook_framework.installed."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create cache missing required field
        cache_dir = Path('config/precommit-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-hooks.yaml'

        cache_data = {'other_field': 'value'}  # Missing hook_framework.installed
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is False
        assert "cache invalid" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_when_precommit_config_missing(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when .pre-commit-config.yaml missing."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create valid cache
        cache_dir = Path('config/precommit-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-hooks.yaml'

        cache_data = {'hook_framework': {'installed': True}}
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        # No .pre-commit-config.yaml in project

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is False
        assert ".pre-commit-config.yaml not found" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_when_git_hook_missing(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when .git/hooks/pre-commit missing."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create valid cache
        cache_dir = Path('config/precommit-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-hooks.yaml'

        cache_data = {'hook_framework': {'installed': True}}
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        # Create .pre-commit-config.yaml but not git hook
        (project_path / '.pre-commit-config.yaml').touch()

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is False
        assert "git hook not installed" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_success(self, validator, mock_tracker, tmp_path):
        """Test successful skip when all conditions met."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create valid cache (fresh, <7 days)
        cache_dir = Path('config/precommit-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-hooks.yaml'

        cache_data = {'hook_framework': {'installed': True}}
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        # Create .pre-commit-config.yaml
        (project_path / '.pre-commit-config.yaml').touch()

        # Create git hook
        git_hooks_dir = project_path / '.git' / 'hooks'
        git_hooks_dir.mkdir(parents=True)
        (git_hooks_dir / 'pre-commit').touch()

        can_skip, reason = validator.can_skip_hook_config(project_path)

        assert can_skip is True
        assert "saved 60s + $0.50" in reason
        assert "0d ago" in reason  # Fresh cache

        # Cleanup
        cache_file.unlink()

    def test_validation_performance(self, validator, mock_tracker, tmp_path):
        """Test that validation completes in <100ms."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = False

        start = time.time()
        validator.can_skip_hook_config(project_path)
        duration = (time.time() - start) * 1000  # Convert to ms

        assert duration < 100, f"Validation took {duration:.1f}ms, expected <100ms"


class TestPreflightValidatorTestDiscovery:
    """Test test discovery validation."""

    @pytest.fixture
    def mock_tracker(self):
        """Create mock SetupTracker."""
        tracker = Mock(spec=SetupTracker)
        tracker.is_setup_complete.return_value = False
        return tracker

    @pytest.fixture
    def validator(self, mock_tracker):
        """Create PreflightValidator with mock tracker."""
        return PreflightValidator(mock_tracker)

    def test_can_skip_when_state_not_tracked(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when state not tracked."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        can_skip, reason = validator.can_skip_test_discovery(project_path)

        assert can_skip is False
        assert "setup state not tracked" in reason

    def test_can_skip_when_cache_missing(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache file missing."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        can_skip, reason = validator.can_skip_test_discovery(project_path)

        assert can_skip is False
        assert "cache file missing" in reason

    def test_can_skip_when_cache_stale(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache is stale (>7 days)."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create stale cache file (8 days old)
        cache_dir = Path('config/test-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-tests.yaml'

        cache_data = {
            'test_framework': 'pytest',
            'test_command': 'pytest',
            'test_patterns': ['test_*.py']
        }
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        # Set modification time to 8 days ago
        import os
        eight_days_ago = time.time() - (8 * 24 * 60 * 60)
        os.utime(cache_file, (eight_days_ago, eight_days_ago))

        can_skip, reason = validator.can_skip_test_discovery(project_path)

        assert can_skip is False
        assert "cache stale" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_when_cache_missing_required_fields(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache missing required fields."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create cache missing test_patterns
        cache_dir = Path('config/test-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-tests.yaml'

        cache_data = {
            'test_framework': 'pytest',
            'test_command': 'pytest'
            # Missing test_patterns
        }
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        can_skip, reason = validator.can_skip_test_discovery(project_path)

        assert can_skip is False
        assert "cache invalid" in reason
        assert "missing fields" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_when_cache_has_empty_fields(self, validator, mock_tracker, tmp_path):
        """Test that validation fails when cache has empty required fields."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create cache with empty field
        cache_dir = Path('config/test-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-tests.yaml'

        cache_data = {
            'test_framework': 'pytest',
            'test_command': '',  # Empty
            'test_patterns': ['test_*.py']
        }
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        can_skip, reason = validator.can_skip_test_discovery(project_path)

        assert can_skip is False
        assert "cache invalid" in reason
        assert "test_command is empty" in reason

        # Cleanup
        cache_file.unlink()

    def test_can_skip_success(self, validator, mock_tracker, tmp_path):
        """Test successful skip when all conditions met."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = True

        # Create valid cache (fresh, <7 days)
        cache_dir = Path('config/test-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_path.name}-tests.yaml'

        cache_data = {
            'test_framework': 'pytest',
            'test_command': 'pytest tests/',
            'test_patterns': ['test_*.py', '*_test.py']
        }
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        can_skip, reason = validator.can_skip_test_discovery(project_path)

        assert can_skip is True
        assert "saved 90s + $0.60" in reason
        assert "0d ago" in reason  # Fresh cache

        # Cleanup
        cache_file.unlink()

    def test_validation_performance(self, validator, mock_tracker, tmp_path):
        """Test that validation completes in <50ms."""
        project_path = tmp_path / "project"
        project_path.mkdir()
        mock_tracker.is_setup_complete.return_value = False

        start = time.time()
        validator.can_skip_test_discovery(project_path)
        duration = (time.time() - start) * 1000  # Convert to ms

        assert duration < 50, f"Validation took {duration:.1f}ms, expected <50ms"


class TestCacheValidation:
    """Test internal cache validation methods."""

    @pytest.fixture
    def validator(self):
        """Create validator with mock tracker."""
        tracker = Mock(spec=SetupTracker)
        return PreflightValidator(tracker)

    def test_validate_hook_cache_valid(self, validator, tmp_path):
        """Test validation of valid hook cache."""
        cache_file = tmp_path / "hooks.yaml"
        cache_data = {'hook_framework': {'installed': True}}
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        is_valid, reason = validator._validate_hook_cache(cache_file)

        assert is_valid is True
        assert "valid and complete" in reason

    def test_validate_hook_cache_missing_installed_field(self, validator, tmp_path):
        """Test validation fails when hook_framework.installed missing."""
        cache_file = tmp_path / "hooks.yaml"
        cache_data = {'hook_framework': {'other_field': 'value'}}
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        is_valid, reason = validator._validate_hook_cache(cache_file)

        assert is_valid is False
        assert "hook_framework.installed != true" in reason

    def test_validate_hook_cache_invalid_yaml(self, validator, tmp_path):
        """Test validation fails with invalid YAML."""
        cache_file = tmp_path / "hooks.yaml"
        cache_file.write_text("invalid: {yaml")

        is_valid, reason = validator._validate_hook_cache(cache_file)

        assert is_valid is False
        assert "YAML parse error" in reason

    def test_validate_test_cache_valid(self, validator, tmp_path):
        """Test validation of valid test cache."""
        cache_file = tmp_path / "tests.yaml"
        cache_data = {
            'test_framework': 'pytest',
            'test_command': 'pytest',
            'test_patterns': ['test_*.py']
        }
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        is_valid, reason = validator._validate_test_cache(cache_file)

        assert is_valid is True
        assert "valid and complete" in reason

    def test_validate_test_cache_missing_fields(self, validator, tmp_path):
        """Test validation fails when required fields missing."""
        cache_file = tmp_path / "tests.yaml"
        cache_data = {
            'test_framework': 'pytest'
            # Missing test_command and test_patterns
        }
        with open(cache_file, 'w') as f:
            yaml.dump(cache_data, f)

        is_valid, reason = validator._validate_test_cache(cache_file)

        assert is_valid is False
        assert "missing fields" in reason
        assert "test_command" in reason
        assert "test_patterns" in reason

    def test_validate_cache_permission_error(self, validator, tmp_path):
        """Test graceful handling of permission errors."""
        cache_file = tmp_path / "hooks.yaml"
        cache_file.write_text("data: value")
        cache_file.chmod(0o000)  # Remove all permissions

        is_valid, reason = validator._validate_hook_cache(cache_file)

        assert is_valid is False
        assert "unreadable" in reason.lower()

        # Cleanup
        cache_file.chmod(0o600)


class TestPerformance:
    """Test overall performance requirements."""

    @pytest.fixture
    def validator(self):
        """Create validator with mock tracker."""
        tracker = Mock(spec=SetupTracker)
        tracker.is_setup_complete.return_value = True
        val = PreflightValidator(tracker)
        return val, tracker

    def test_combined_validation_under_200ms(self, validator, tmp_path):
        """Test that both validations complete in <200ms total."""
        val, mock_tracker = validator
        project_path = tmp_path / "project"
        project_path.mkdir()

        # Create valid caches
        hook_cache_dir = Path('config/precommit-cache')
        hook_cache_dir.mkdir(parents=True, exist_ok=True)
        hook_cache = hook_cache_dir / f'{project_path.name}-hooks.yaml'
        with open(hook_cache, 'w') as f:
            yaml.dump({'hook_framework': {'installed': True}}, f)

        test_cache_dir = Path('config/test-cache')
        test_cache_dir.mkdir(parents=True, exist_ok=True)
        test_cache = test_cache_dir / f'{project_path.name}-tests.yaml'
        with open(test_cache, 'w') as f:
            yaml.dump({
                'test_framework': 'pytest',
                'test_command': 'pytest',
                'test_patterns': ['test_*.py']
            }, f)

        # Create required files
        (project_path / '.pre-commit-config.yaml').touch()
        git_hooks = project_path / '.git' / 'hooks'
        git_hooks.mkdir(parents=True)
        (git_hooks / 'pre-commit').touch()

        # Run both validations
        start = time.time()
        val.can_skip_hook_config(project_path)
        val.can_skip_test_discovery(project_path)
        duration = (time.time() - start) * 1000

        assert duration < 200, f"Combined validation took {duration:.1f}ms, expected <200ms"

        # Cleanup
        hook_cache.unlink()
        test_cache.unlink()
