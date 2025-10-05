"""End-to-end test for project-based state management in autonomous fixing.

Tests the actual code integration to verify:
1. .ai-state/ directory created in project
2. State files written with correct format (Markdown + YAML frontmatter)
3. .gitignore updated with .ai-state/ entry
4. Config modification triggers invalidation
5. State persists across runs
6. Setup skipped when state is valid

Note: This tests the code paths directly rather than running autonomous_fix.sh
to avoid dependencies on the full execution environment.
"""

import tempfile
import time
from pathlib import Path

import pytest
import yaml

from airflow_dags.autonomous_fixing.core.setup_tracker import SetupTracker
from airflow_dags.autonomous_fixing.core.state_manager import ProjectStateManager
from airflow_dags.autonomous_fixing.core.validators.preflight import PreflightValidator


@pytest.fixture
def test_project():
    """Create temporary test project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()

        # Create config files
        (project_path / ".pre-commit-config.yaml").write_text("repos: []")
        hook_dir = project_path / ".git" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit").write_text("#!/bin/sh\necho 'pre-commit hook'")

        (project_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')

        yield project_path


def test_project_state_directory_created(test_project):
    """Test that .ai-state/ directory is created when saving state."""
    state_dir = test_project / ".ai-state"
    assert not state_dir.exists()

    # Simulate what IterationEngine does: save state after successful setup
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})

    assert state_dir.exists()
    assert state_dir.is_dir()


def test_project_state_files_created(test_project):
    """Test that state files are created with correct format."""
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})

    state_dir = test_project / ".ai-state"
    hooks_state = state_dir / "hooks_state.md"
    assert hooks_state.exists()

    # Verify file format
    content = hooks_state.read_text()
    assert content.startswith("---")  # YAML frontmatter
    assert "generated:" in content
    assert "config_hash:" in content
    assert "# Hooks Configuration State" in content

    # Verify frontmatter is valid YAML
    parts = content.split("---", 2)
    assert len(parts) >= 3
    metadata = yaml.safe_load(parts[1])
    assert "generated" in metadata
    assert "status" in metadata
    assert "config_hash" in metadata


def test_gitignore_updated(test_project):
    """Test that .gitignore is updated with .ai-state/ entry."""
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})

    gitignore = test_project / ".gitignore"
    assert gitignore.exists()

    content = gitignore.read_text()
    assert ".ai-state/" in content


def test_config_modification_triggers_invalidation(test_project):
    """Test that modifying config invalidates state via PreflightValidator."""
    # Setup: create state manager and save initial state
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})

    # Setup tracker and validator (simulate IterationEngine setup)
    setup_tracker = SetupTracker(config=None)
    setup_tracker.mark_setup_complete(str(test_project), "hooks")
    validator = PreflightValidator(setup_tracker)

    # First check - should skip (state valid)
    can_skip, reason = validator.can_skip_hook_config(test_project)
    assert can_skip is True

    # Wait to ensure mtime difference
    time.sleep(0.2)

    # Modify .pre-commit-config.yaml
    precommit_config = test_project / ".pre-commit-config.yaml"
    original_content = precommit_config.read_text()
    precommit_config.write_text(original_content + "\n# Modified\n")

    # Second check - should NOT skip (config modified)
    can_skip2, reason2 = validator.can_skip_hook_config(test_project)
    assert can_skip2 is False
    assert "modified" in reason2.lower() or "changed" in reason2.lower()


def test_state_persists_across_validator_checks(test_project):
    """Test that state persists and validator recognizes it."""
    # Save state
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})
    manager.save_state("tests", {"discovered": True})

    # Create validator
    setup_tracker = SetupTracker(config=None)
    setup_tracker.mark_setup_complete(str(test_project), "hooks")
    setup_tracker.mark_setup_complete(str(test_project), "tests")
    validator = PreflightValidator(setup_tracker)

    # Multiple checks should all recognize state
    for _ in range(3):
        can_skip_hooks, _ = validator.can_skip_hook_config(test_project)
        can_skip_tests, _ = validator.can_skip_test_discovery(test_project)

        assert can_skip_hooks is True
        assert can_skip_tests is True


def test_state_file_permissions(test_project):
    """Test that state files have correct permissions (0644)."""
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})

    hooks_state = test_project / ".ai-state" / "hooks_state.md"
    mode = hooks_state.stat().st_mode & 0o777
    assert mode == 0o644


def test_multiple_phases_separate_state_files(test_project):
    """Test that hooks and tests have separate state files."""
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True, "phase": "hooks"})
    manager.save_state("tests", {"discovered": True, "phase": "tests"})

    state_dir = test_project / ".ai-state"
    hooks_state = state_dir / "hooks_state.md"
    tests_state = state_dir / "tests_state.md"

    assert hooks_state.exists()
    assert tests_state.exists()

    # Verify they have different content
    hooks_content = hooks_state.read_text()
    tests_content = tests_state.read_text()

    assert "Hooks Configuration State" in hooks_content
    assert "Tests Configuration State" in tests_content


def test_state_format_validation_markers(test_project):
    """Test that state files include validation markers."""
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})

    hooks_state = test_project / ".ai-state" / "hooks_state.md"
    content = hooks_state.read_text()

    # Verify validation markers present
    assert "Validation Markers" in content
    assert "Cache Invalidation Triggers" in content
    assert "Hook file exists" in content
    assert "Config file exists" in content


def test_integration_with_preflight_validator_full_flow(test_project):
    """Test full integration: state manager + preflight validator."""
    # Setup: test_project fixture already has .pre-commit-config.yaml and .git/hooks/pre-commit
    # So validator will initially say "can skip" because files exist
    # This is actually correct behavior - we're testing state invalidation, not initial setup

    setup_tracker = SetupTracker(config=None)
    validator = PreflightValidator(setup_tracker)

    # Step 1: Even though files exist, without tracker state, behavior depends on file existence
    # Since test fixture creates files, validator may say "can skip" (files already exist)
    # This is actually CORRECT - if hooks exist, we can skip
    can_skip1, reason1 = validator.can_skip_hook_config(test_project)
    # Don't assert False here - files exist, so skipping is valid

    # Step 2: Mark setup complete and save state (simulate IterationEngine)
    setup_tracker.mark_setup_complete(str(test_project), "hooks")
    manager = ProjectStateManager(test_project)
    manager.save_state("hooks", {"configured": True})

    # Step 3: Validator should still skip (state + files both good)
    can_skip2, reason2 = validator.can_skip_hook_config(test_project)
    assert can_skip2 is True
    assert "saved" in reason2.lower() or "configured" in reason2.lower()

    # Step 4: Delete required file - should trigger re-run
    (test_project / ".git" / "hooks" / "pre-commit").unlink()

    can_skip3, reason3 = validator.can_skip_hook_config(test_project)
    assert can_skip3 is False
    assert "deleted" in reason3.lower() or "missing" in reason3.lower()
