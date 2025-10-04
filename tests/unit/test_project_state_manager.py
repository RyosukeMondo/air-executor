"""Unit tests for ProjectStateManager."""

import hashlib
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from airflow_dags.autonomous_fixing.core.state_manager import ProjectStateManager


class TestProjectStateManagerInit:
    """Test ProjectStateManager initialization."""

    def test_init_sets_paths(self, tmp_path):
        """Test that initialization sets correct paths."""
        manager = ProjectStateManager(tmp_path)

        assert manager.project_path == tmp_path
        assert manager.state_dir == tmp_path / ".ai-state"

    def test_init_does_not_create_state_dir(self, tmp_path):
        """Test that initialization doesn't create state directory yet."""
        manager = ProjectStateManager(tmp_path)

        assert not manager.state_dir.exists()


class TestProjectStateManagerSaveState:
    """Test state saving functionality."""

    def test_save_state_creates_directory(self, tmp_path):
        """Test that save_state creates .ai-state directory."""
        manager = ProjectStateManager(tmp_path)

        manager.save_state('hooks', {'configured': True})

        assert manager.state_dir.exists()
        assert manager.state_dir.is_dir()

    def test_save_state_creates_gitignore_entry(self, tmp_path):
        """Test that save_state adds .ai-state/ to .gitignore."""
        manager = ProjectStateManager(tmp_path)

        manager.save_state('hooks', {'configured': True})

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert '.ai-state/' in gitignore.read_text()

    def test_save_state_does_not_duplicate_gitignore(self, tmp_path):
        """Test that .ai-state/ is not duplicated in .gitignore."""
        manager = ProjectStateManager(tmp_path)

        # Save state twice
        manager.save_state('hooks', {'configured': True})
        manager.save_state('tests', {'discovered': True})

        gitignore_content = (tmp_path / ".gitignore").read_text()
        assert gitignore_content.count('.ai-state/') == 1

    def test_save_state_preserves_existing_gitignore(self, tmp_path):
        """Test that existing .gitignore content is preserved."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n")

        manager = ProjectStateManager(tmp_path)
        manager.save_state('hooks', {'configured': True})

        content = gitignore.read_text()
        assert '*.pyc' in content
        assert '__pycache__/' in content
        assert '.ai-state/' in content

    def test_save_state_creates_markdown_file(self, tmp_path):
        """Test that state file is created with Markdown format."""
        manager = ProjectStateManager(tmp_path)

        manager.save_state('hooks', {'configured': True})

        state_file = manager.state_dir / "hooks_state.md"
        assert state_file.exists()

        content = state_file.read_text()
        assert content.startswith('---')
        assert 'generated:' in content
        assert 'config_hash:' in content

    def test_save_state_includes_yaml_frontmatter(self, tmp_path):
        """Test that state file includes valid YAML frontmatter."""
        manager = ProjectStateManager(tmp_path)

        manager.save_state('hooks', {'configured': True})

        state_file = manager.state_dir / "hooks_state.md"
        content = state_file.read_text()

        # Extract frontmatter
        parts = content.split('---', 2)
        assert len(parts) >= 3

        frontmatter = yaml.safe_load(parts[1])
        assert 'generated' in frontmatter
        assert 'status' in frontmatter
        assert 'config_hash' in frontmatter

    def test_save_state_hooks_includes_validation_markers(self, tmp_path):
        """Test that hooks state includes validation markers."""
        # Create config files
        (tmp_path / ".pre-commit-config.yaml").write_text("repos: []")
        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        (tmp_path / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh")

        manager = ProjectStateManager(tmp_path)
        manager.save_state('hooks', {'configured': True})

        state_file = manager.state_dir / "hooks_state.md"
        content = state_file.read_text()

        assert 'Hook file exists: True' in content
        assert 'Config file exists: True' in content

    def test_save_state_tests_includes_validation_markers(self, tmp_path):
        """Test that tests state includes validation markers."""
        (tmp_path / "package.json").write_text('{"name": "test"}')

        manager = ProjectStateManager(tmp_path)
        manager.save_state('tests', {'discovered': True})

        state_file = manager.state_dir / "tests_state.md"
        content = state_file.read_text()

        assert 'Config file exists: True' in content

    def test_save_state_sets_file_permissions(self, tmp_path):
        """Test that state file has correct permissions (0644)."""
        manager = ProjectStateManager(tmp_path)

        manager.save_state('hooks', {'configured': True})

        state_file = manager.state_dir / "hooks_state.md"
        assert state_file.stat().st_mode & 0o777 == 0o644

    def test_save_state_uses_atomic_write(self, tmp_path):
        """Test that save_state uses atomic write (temp file + rename)."""
        manager = ProjectStateManager(tmp_path)

        # Mock write to verify temp file is used
        original_write_text = Path.write_text

        temp_files_created = []

        def track_write_text(self, *args, **kwargs):
            if self.suffix == '.tmp':
                temp_files_created.append(self)
            return original_write_text(self, *args, **kwargs)

        with patch.object(Path, 'write_text', track_write_text):
            manager.save_state('hooks', {'configured': True})

        assert len(temp_files_created) > 0


class TestProjectStateManagerGetConfigHash:
    """Test configuration hash computation."""

    def test_get_config_hash_hooks(self, tmp_path):
        """Test hash computation for hooks phase."""
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos:\n  - repo: test")

        manager = ProjectStateManager(tmp_path)
        hash_value = manager._get_config_hash('hooks')

        # Verify it's a valid SHA256 hash
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_get_config_hash_tests(self, tmp_path):
        """Test hash computation for tests phase."""
        config = tmp_path / "package.json"
        config.write_text('{"scripts": {"test": "pytest"}}')

        manager = ProjectStateManager(tmp_path)
        hash_value = manager._get_config_hash('tests')

        assert len(hash_value) == 64

    def test_get_config_hash_missing_file(self, tmp_path):
        """Test hash computation when config file is missing."""
        manager = ProjectStateManager(tmp_path)
        hash_value = manager._get_config_hash('hooks')

        # Should return empty hash
        expected = hashlib.sha256().hexdigest()
        assert hash_value == expected

    def test_get_config_hash_changes_on_content_change(self, tmp_path):
        """Test that hash changes when config content changes."""
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []")

        manager = ProjectStateManager(tmp_path)
        hash1 = manager._get_config_hash('hooks')

        # Modify config
        config.write_text("repos:\n  - repo: added")
        hash2 = manager._get_config_hash('hooks')

        assert hash1 != hash2


class TestProjectStateManagerShouldReconfigure:
    """Test reconfiguration logic."""

    def test_should_reconfigure_missing_state(self, tmp_path):
        """Test that missing state triggers reconfiguration."""
        manager = ProjectStateManager(tmp_path)

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'no hooks state found' in reason

    def test_should_reconfigure_corrupted_frontmatter(self, tmp_path):
        """Test that corrupted frontmatter triggers reconfiguration."""
        manager = ProjectStateManager(tmp_path)
        state_file = manager.state_dir / "hooks_state.md"
        state_file.parent.mkdir(exist_ok=True)

        # Write invalid frontmatter
        state_file.write_text("Invalid content without frontmatter")

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'corrupted' in reason
        assert not state_file.exists()  # Should be deleted

    def test_should_reconfigure_stale_state(self, tmp_path):
        """Test that stale state (>30 days) triggers reconfiguration."""
        # Create all required files
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []")
        hook_dir = tmp_path / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        hook_file = hook_dir / "pre-commit"
        hook_file.write_text("#!/bin/sh")

        manager = ProjectStateManager(tmp_path)

        # Get the actual config hash to avoid hash mismatch
        actual_hash = manager._get_config_hash('hooks')

        # Create state with old timestamp but ensure mtime is also old
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=31)
        state_file = manager.state_dir / "hooks_state.md"
        state_file.parent.mkdir(exist_ok=True)

        content = f"""---
generated: {old_timestamp.isoformat()}
status: CONFIGURED
config_hash: {actual_hash}
---
# Hooks Configuration State
"""
        state_file.write_text(content)

        # Set config file mtime to be older than state file to pass mtime check
        # (mtime check compares config mtime > state mtime)
        import os
        old_config_time = (datetime.now(timezone.utc) - timedelta(days=32)).timestamp()
        os.utime(config, (old_config_time, old_config_time))
        os.utime(hook_file, (old_config_time, old_config_time))

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'stale' in reason

    def test_should_reconfigure_config_modified_mtime(self, tmp_path):
        """Test that config file modification (mtime) triggers reconfiguration."""
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []")

        manager = ProjectStateManager(tmp_path)
        manager.save_state('hooks', {'configured': True})

        # Wait to ensure mtime difference
        time.sleep(0.1)

        # Modify config file (update mtime)
        config.write_text("repos:\n  - repo: new")

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'modified' in reason

    def test_should_reconfigure_config_hash_changed(self, tmp_path):
        """Test that config hash change triggers reconfiguration."""
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []")

        manager = ProjectStateManager(tmp_path)
        manager.save_state('hooks', {'configured': True})

        # Modify config with same mtime (hash check catches this)
        state_file = manager.state_dir / "hooks_state.md"
        original_mtime = state_file.stat().st_mtime

        # Change config content
        config.write_text("repos:\n  - repo: different")

        # Restore state file mtime to simulate mtime check passing
        import os
        os.utime(state_file, (original_mtime + 1, original_mtime + 1))

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'changed' in reason

    def test_should_reconfigure_required_files_deleted(self, tmp_path):
        """Test that deleted required files trigger reconfiguration."""
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []")
        hook_dir = tmp_path / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        hook_file = hook_dir / "pre-commit"
        hook_file.write_text("#!/bin/sh")

        manager = ProjectStateManager(tmp_path)
        manager.save_state('hooks', {'configured': True})

        # Delete hook file
        hook_file.unlink()

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'deleted' in reason

    def test_should_reconfigure_fresh_state_no_changes(self, tmp_path):
        """Test that fresh state with no changes allows skip."""
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []")
        hook_dir = tmp_path / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit").write_text("#!/bin/sh")

        manager = ProjectStateManager(tmp_path)
        manager.save_state('hooks', {'configured': True})

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is False
        assert 'cached' in reason


class TestProjectStateManagerBackwardCompatibility:
    """Test backward compatibility with external cache."""

    def test_check_external_cache_hooks(self, tmp_path):
        """Test fallback to external hooks cache."""
        project_name = tmp_path.name
        external_cache_dir = Path('config/precommit-cache')
        external_cache_dir.mkdir(parents=True, exist_ok=True)
        external_cache = external_cache_dir / f"{project_name}-hooks.yaml"
        external_cache.write_text("hook_framework:\n  installed: true")

        manager = ProjectStateManager(tmp_path)

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is False
        assert 'external cache' in reason

    def test_check_external_cache_tests(self, tmp_path):
        """Test fallback to external tests cache."""
        project_name = tmp_path.name
        external_cache_dir = Path('config/test-cache')
        external_cache_dir.mkdir(parents=True, exist_ok=True)
        external_cache = external_cache_dir / f"{project_name}-tests.yaml"
        external_cache.write_text("test_framework: pytest")

        manager = ProjectStateManager(tmp_path)

        should_reconfig, reason = manager.should_reconfigure('tests')

        assert should_reconfig is False
        assert 'external cache' in reason

    def test_external_cache_stale(self, tmp_path):
        """Test that stale external cache triggers reconfiguration."""
        project_name = tmp_path.name
        external_cache_dir = Path('config/precommit-cache')
        external_cache_dir.mkdir(parents=True, exist_ok=True)
        external_cache = external_cache_dir / f"{project_name}-hooks.yaml"
        external_cache.write_text("hook_framework:\n  installed: true")

        # Set old mtime
        old_time = time.time() - (31 * 24 * 60 * 60)
        import os
        os.utime(external_cache, (old_time, old_time))

        manager = ProjectStateManager(tmp_path)

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'stale' in reason

    def test_migration_logged(self, tmp_path, caplog):
        """Test that migration from external cache is logged."""
        project_name = tmp_path.name
        external_cache_dir = Path('config/precommit-cache')
        external_cache_dir.mkdir(parents=True, exist_ok=True)
        external_cache = external_cache_dir / f"{project_name}-hooks.yaml"
        external_cache.write_text("hook_framework:\n  installed: true")

        manager = ProjectStateManager(tmp_path)

        with caplog.at_level('INFO'):
            manager.should_reconfigure('hooks')

        assert 'Migrating state from config/ to .ai-state/' in caplog.text


class TestProjectStateManagerEdgeCases:
    """Test edge cases and error handling."""

    def test_save_state_handles_permission_error(self, tmp_path):
        """Test that permission errors are handled gracefully."""
        manager = ProjectStateManager(tmp_path)

        # Create state dir as read-only
        manager.state_dir.mkdir()
        manager.state_dir.chmod(0o444)

        try:
            with pytest.raises(Exception):
                manager.save_state('hooks', {'configured': True})
        finally:
            # Cleanup
            manager.state_dir.chmod(0o755)

    def test_should_reconfigure_handles_invalid_yaml_frontmatter(self, tmp_path):
        """Test handling of invalid YAML in frontmatter."""
        manager = ProjectStateManager(tmp_path)
        state_file = manager.state_dir / "hooks_state.md"
        state_file.parent.mkdir(exist_ok=True)

        # Write invalid YAML in frontmatter
        content = """---
invalid: yaml: content: here
---
# State
"""
        state_file.write_text(content)

        should_reconfig, reason = manager.should_reconfigure('hooks')

        assert should_reconfig is True
        assert 'corrupted' in reason

    def test_gitignore_creation_with_existing_content(self, tmp_path):
        """Test gitignore handling with various existing content."""
        # Create gitignore with trailing newline
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        manager = ProjectStateManager(tmp_path)
        manager.save_state('hooks', {'configured': True})

        content = gitignore.read_text()
        lines = content.strip().split('\n')

        assert '*.pyc' in lines
        assert '.ai-state/' in lines

    def test_state_file_format_consistency(self, tmp_path):
        """Test that state file format is consistent across saves."""
        (tmp_path / ".pre-commit-config.yaml").write_text("repos: []")

        manager = ProjectStateManager(tmp_path)

        manager.save_state('hooks', {'configured': True})
        state_file1 = (manager.state_dir / "hooks_state.md").read_text()

        # Save again
        manager.save_state('hooks', {'configured': True})
        state_file2 = (manager.state_dir / "hooks_state.md").read_text()

        # Both should have same structure (different timestamps though)
        assert state_file1.count('---') == state_file2.count('---')
        assert 'config_hash' in state_file1
        assert 'config_hash' in state_file2
