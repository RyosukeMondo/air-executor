"""Integration tests for state migration and portability."""

import shutil
import time
from pathlib import Path

from airflow_dags.autonomous_fixing.core.state_manager import ProjectStateManager


class TestStateMigration:
    """Test migration from external cache to project state."""

    def test_migration_from_external_hooks_cache(self, tmp_path):
        """Test migration from external hooks cache to project state."""
        # Create project
        project = tmp_path / "test-project"
        project.mkdir()

        # Create config files
        (project / ".pre-commit-config.yaml").write_text("repos: []")
        hook_dir = project / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit").write_text("#!/bin/sh")

        # Create external cache
        external_cache_dir = Path("config/precommit-cache")
        external_cache_dir.mkdir(parents=True, exist_ok=True)
        external_cache = external_cache_dir / f"{project.name}-hooks.yaml"
        external_cache.write_text("""
hook_framework:
  installed: true
  type: pre-commit
""")

        try:
            # Check state - with existing hooks, should skip reconfiguration
            manager = ProjectStateManager(project)
            should_reconfig, reason = manager.should_reconfigure("hooks")

            assert should_reconfig is False
            # New behavior: detects existing hooks in filesystem directly
            assert "hooks already configured" in reason or "pre-commit" in reason

            # Save new state - should write to project
            manager.save_state("hooks", {"configured": True})

            # Verify .ai-state/ created
            assert (project / ".ai-state").exists()
            assert (project / ".ai-state" / "hooks_state.md").exists()

            # Verify gitignore updated
            gitignore = project / ".gitignore"
            assert gitignore.exists()
            assert ".ai-state/" in gitignore.read_text()

            # Next check should use project state, not external
            manager2 = ProjectStateManager(project)
            should_reconfig2, reason2 = manager2.should_reconfigure("hooks")

            assert should_reconfig2 is False
            assert "cached" in reason2  # Uses project state now
            assert "external" not in reason2

        finally:
            # Cleanup external cache
            if external_cache.exists():
                external_cache.unlink()

    def test_migration_from_external_tests_cache(self, tmp_path):
        """Test migration from external tests cache to project state."""
        # Create project
        project = tmp_path / "test-project"
        project.mkdir()

        # Create config files
        (project / "package.json").write_text('{"name": "test", "scripts": {"test": "pytest"}}')

        # Create external cache
        external_cache_dir = Path("config/test-cache")
        external_cache_dir.mkdir(parents=True, exist_ok=True)
        external_cache = external_cache_dir / f"{project.name}-tests.yaml"
        external_cache.write_text("""
test_framework: pytest
test_command: pytest
test_patterns:
  - "test_*.py"
""")

        try:
            # Check state - should use external cache
            manager = ProjectStateManager(project)
            should_reconfig, reason = manager.should_reconfigure("tests")

            assert should_reconfig is False
            assert "external cache" in reason

            # Save new state
            manager.save_state("tests", {"discovered": True})

            # Verify project state created
            assert (project / ".ai-state" / "tests_state.md").exists()

            # Next check should use project state
            manager2 = ProjectStateManager(project)
            should_reconfig2, reason2 = manager2.should_reconfigure("tests")

            assert should_reconfig2 is False
            assert "cached" in reason2

        finally:
            # Cleanup external cache
            if external_cache.exists():
                external_cache.unlink()

    def test_migration_logged(self, tmp_path, caplog):
        """Test that existing hook detection is properly logged."""
        project = tmp_path / "test-project"
        project.mkdir()
        (project / ".pre-commit-config.yaml").write_text("repos: []")

        # Create external cache (for backward compatibility test)
        external_cache_dir = Path("config/precommit-cache")
        external_cache_dir.mkdir(parents=True, exist_ok=True)
        external_cache = external_cache_dir / f"{project.name}-hooks.yaml"
        external_cache.write_text("hook_framework:\n  installed: true")

        try:
            manager = ProjectStateManager(project)

            with caplog.at_level("DEBUG"):
                should_reconfig, reason = manager.should_reconfigure("hooks")

            # Verify detection logged (new behavior: detects existing hooks directly)
            assert should_reconfig is False
            assert "hooks already configured" in reason or "pre-commit" in reason
            assert "hooks" in caplog.text

        finally:
            if external_cache.exists():
                external_cache.unlink()


class TestStatePortability:
    """Test cross-machine consistency and portability."""

    def test_copy_project_to_different_path(self, tmp_path):
        """Test that state works after copying project to different path."""
        # Create original project with state
        original_project = tmp_path / "original"
        original_project.mkdir()

        config = original_project / ".pre-commit-config.yaml"
        config.write_text("repos:\n  - repo: test")
        hook_dir = original_project / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit").write_text("#!/bin/sh")

        # Save state
        manager1 = ProjectStateManager(original_project)
        manager1.save_state("hooks", {"configured": True, "project": "original"})

        # Verify state works
        should_reconfig1, reason1 = manager1.should_reconfigure("hooks")
        assert should_reconfig1 is False

        # Copy project to different location
        copied_project = tmp_path / "copied"
        shutil.copytree(original_project, copied_project)

        # Verify state still works at new location
        manager2 = ProjectStateManager(copied_project)
        should_reconfig2, reason2 = manager2.should_reconfigure("hooks")

        assert should_reconfig2 is False
        assert "cached" in reason2

    def test_state_survives_project_rename(self, tmp_path):
        """Test that state is valid after project directory rename."""
        # Create project with state
        project_v1 = tmp_path / "project-v1"
        project_v1.mkdir()

        (project_v1 / ".pre-commit-config.yaml").write_text("repos: []")
        hook_dir = project_v1 / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit").write_text("#!/bin/sh")

        manager1 = ProjectStateManager(project_v1)
        manager1.save_state("hooks", {"configured": True})

        # Rename project directory
        project_v2 = tmp_path / "project-v2"
        project_v1.rename(project_v2)

        # Verify state still valid at new name
        manager2 = ProjectStateManager(project_v2)
        should_reconfig, reason = manager2.should_reconfigure("hooks")

        assert should_reconfig is False
        assert "cached" in reason

    def test_config_modification_detected_after_copy(self, tmp_path):
        """Test that config modification is detected even after project copy."""
        # Create project with state
        original = tmp_path / "original"
        original.mkdir()

        config = original / ".pre-commit-config.yaml"
        config.write_text("repos: []")
        hook_dir = original / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit").write_text("#!/bin/sh")

        manager1 = ProjectStateManager(original)
        manager1.save_state("hooks", {"configured": True})

        # Copy project
        copied = tmp_path / "copied"
        shutil.copytree(original, copied)

        # Modify config in copied project
        time.sleep(0.1)  # Ensure mtime difference
        (copied / ".pre-commit-config.yaml").write_text("repos:\n  - repo: new")

        # Verify modification detected
        manager2 = ProjectStateManager(copied)
        should_reconfig, reason = manager2.should_reconfigure("hooks")

        assert should_reconfig is True
        assert "modified" in reason.lower() or "changed" in reason.lower()


class TestStateInvalidation:
    """Test state invalidation triggers in integration scenarios."""

    def test_invalidation_after_config_change(self, tmp_path):
        """Test that changing config invalidates state."""
        project = tmp_path / "test-project"
        project.mkdir()

        config = project / "package.json"
        config.write_text('{"name": "test", "version": "1.0.0"}')

        # Save state
        manager = ProjectStateManager(project)
        manager.save_state("tests", {"discovered": True})

        # Verify state valid
        should_reconfig1, _ = manager.should_reconfigure("tests")
        assert should_reconfig1 is False

        # Modify config
        time.sleep(0.1)
        config.write_text('{"name": "test", "version": "2.0.0"}')

        # Verify state invalidated
        should_reconfig2, reason = manager.should_reconfigure("tests")
        assert should_reconfig2 is True
        assert "modified" in reason.lower() or "changed" in reason.lower()

    def test_invalidation_after_file_deletion(self, tmp_path):
        """Test that deleting required files invalidates state."""
        project = tmp_path / "test-project"
        project.mkdir()

        config = project / ".pre-commit-config.yaml"
        config.write_text("repos: []")
        hook_dir = project / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        hook_file = hook_dir / "pre-commit"
        hook_file.write_text("#!/bin/sh")

        # Save state
        manager = ProjectStateManager(project)
        manager.save_state("hooks", {"configured": True})

        # Verify state valid
        should_reconfig1, _ = manager.should_reconfigure("hooks")
        assert should_reconfig1 is False

        # Delete hook file
        hook_file.unlink()

        # Verify state invalidated
        should_reconfig2, reason = manager.should_reconfigure("hooks")
        assert should_reconfig2 is True
        assert "deleted" in reason.lower()

    def test_state_consistency_across_managers(self, tmp_path):
        """Test that multiple manager instances see consistent state."""
        project = tmp_path / "test-project"
        project.mkdir()

        (project / ".pre-commit-config.yaml").write_text("repos: []")
        hook_dir = project / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit").write_text("#!/bin/sh")

        # Manager 1 saves state
        manager1 = ProjectStateManager(project)
        manager1.save_state("hooks", {"configured": True})

        # Manager 2 checks state
        manager2 = ProjectStateManager(project)
        should_reconfig2, reason2 = manager2.should_reconfigure("hooks")

        # Manager 3 checks state
        manager3 = ProjectStateManager(project)
        should_reconfig3, reason3 = manager3.should_reconfigure("hooks")

        # All should see same state
        assert should_reconfig2 is False
        assert should_reconfig3 is False
        assert "cached" in reason2
        assert "cached" in reason3
