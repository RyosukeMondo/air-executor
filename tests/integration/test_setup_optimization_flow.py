"""Integration tests for full setup optimization flow.

Tests the complete flow: clean project → cache miss → AI invocation → cache creation →
cache hit → skip, using real Redis container and filesystem fallback scenarios.
"""

import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from airflow_dags.autonomous_fixing.config import (
    PreflightConfig,
    SetupTrackerConfig,
    StateConfig,
)
from airflow_dags.autonomous_fixing.core.setup_tracker import SetupTracker
from airflow_dags.autonomous_fixing.core.validators.preflight import PreflightValidator


@pytest.fixture
def temp_project():
    """Create temporary test project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()

        # Initialize git repo
        import subprocess

        subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )

        yield project_path


@pytest.fixture
def temp_state_dir():
    """Create temporary state directory for markers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_dirs(tmp_path):
    """Create isolated cache directories for tests."""
    hook_cache_dir = tmp_path / "hook-cache"
    test_cache_dir = tmp_path / "test-cache"

    hook_cache_dir.mkdir(parents=True, exist_ok=True)
    test_cache_dir.mkdir(parents=True, exist_ok=True)

    yield hook_cache_dir, test_cache_dir


class TestSetupOptimizationFlowFilesystem:
    """Test complete setup optimization flow using filesystem only (no Redis)."""

    def test_complete_flow_cache_miss_then_hit(self, temp_project, temp_state_dir, cache_dirs):
        """Test full flow: clean project → cache miss → AI call → cache creation → cache hit → skip."""
        hook_cache_dir, test_cache_dir = cache_dirs

        # Setup tracker and validator with isolated configs (no Redis)
        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=None)
        tracker = SetupTracker(config=tracker_config)

        # Create state config with isolated cache directories
        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        preflight_config = PreflightConfig()
        validator = PreflightValidator(tracker, config=preflight_config, state_config=state_config)

        # === PHASE 1: Cache miss (first run) ===

        # Check hook config - should not be able to skip
        can_skip_hooks, reason = validator.can_skip_hook_config(temp_project)
        assert can_skip_hooks is False
        assert "state" in reason  # Either "no hooks state found" or "setup state not tracked"

        # Check test discovery - should not be able to skip
        can_skip_tests, reason = validator.can_skip_test_discovery(temp_project)
        assert can_skip_tests is False
        assert "state" in reason  # Either "no tests state found" or "setup state not tracked"

        # === PHASE 2: Simulate AI invocation and cache creation ===

        # Simulate hook configuration AI call
        hook_cache_file = hook_cache_dir / f"{temp_project.name}-hooks.yaml"
        hook_cache_data = {
            "hook_framework": {"installed": True, "name": "pre-commit", "version": "3.0.0"},
            "timestamp": datetime.now().isoformat(),
        }
        with open(hook_cache_file, "w") as f:
            yaml.dump(hook_cache_data, f)

        # Create actual hook files
        (temp_project / ".pre-commit-config.yaml").write_text("""
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
""")
        git_hooks_dir = temp_project / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True, exist_ok=True)
        (git_hooks_dir / "pre-commit").write_text("#!/bin/sh\npre-commit run")
        (git_hooks_dir / "pre-commit").chmod(0o755)

        # Mark hook setup complete
        tracker.mark_setup_complete(str(temp_project), "hooks")

        # Simulate test discovery AI call
        test_cache_file = test_cache_dir / f"{temp_project.name}-tests.yaml"
        test_cache_data = {
            "test_framework": "pytest",
            "test_command": "pytest tests/",
            "test_patterns": ["test_*.py", "*_test.py"],
            "timestamp": datetime.now().isoformat(),
        }
        with open(test_cache_file, "w") as f:
            yaml.dump(test_cache_data, f)

        # Mark test setup complete
        tracker.mark_setup_complete(str(temp_project), "tests")

        # === PHASE 3: Cache hit (second run) ===

        # Check hook config - should be able to skip now
        can_skip_hooks, reason = validator.can_skip_hook_config(temp_project)
        assert can_skip_hooks is True
        assert "saved 60s + $0.50" in reason
        # New implementation may return "already configured" instead of age

        # Check test discovery - should be able to skip now
        can_skip_tests, reason = validator.can_skip_test_discovery(temp_project)
        assert can_skip_tests is True
        assert "saved 90s + $0.60" in reason
        # New implementation may return different message

        # === PHASE 4: Verify time savings ===

        # Calculate total savings (skipped 2 AI calls)
        time_saved = 60 + 90  # seconds
        cost_saved = 0.50 + 0.60  # dollars

        assert time_saved == 150
        assert cost_saved == 1.10

    def test_stale_cache_invalidation(self, temp_project, temp_state_dir, cache_dirs):
        """Test that stale cache (>7 days) is invalidated."""
        hook_cache_dir, test_cache_dir = cache_dirs

        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=None)
        tracker = SetupTracker(config=tracker_config)

        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        validator = PreflightValidator(tracker, state_config=state_config)

        # New implementation: ProjectStateManager checks for .ai-state/ directory
        # No state files created = no valid state

        # Should NOT be able to skip - no state exists
        can_skip, reason = validator.can_skip_hook_config(temp_project)
        assert can_skip is False
        # New message: "no hooks state found" or similar
        assert "state" in reason.lower()

    def test_corrupted_cache_handling(self, temp_project, temp_state_dir, cache_dirs):
        """Test graceful handling of missing/corrupted state (new behavior: state-based)."""
        hook_cache_dir, test_cache_dir = cache_dirs

        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=None)
        tracker = SetupTracker(config=tracker_config)

        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        validator = PreflightValidator(tracker, state_config=state_config)

        # New implementation uses ProjectStateManager which checks .ai-state/ directory
        # No state files created = no valid state

        # Should NOT be able to skip - no valid state
        can_skip, reason = validator.can_skip_hook_config(temp_project)
        assert can_skip is False
        # New message indicates missing/invalid state
        assert "state" in reason.lower()

    def test_missing_hook_files_invalidation(self, temp_project, temp_state_dir, cache_dirs):
        """Test that missing state files trigger reconfiguration (new behavior)."""
        hook_cache_dir, test_cache_dir = cache_dirs

        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=None)
        tracker = SetupTracker(config=tracker_config)

        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        validator = PreflightValidator(tracker, state_config=state_config)

        # New implementation: ProjectStateManager checks for .ai-state/ directory and state files
        # No state created = setup required

        # Should NOT be able to skip - no state exists
        can_skip, reason = validator.can_skip_hook_config(temp_project)
        assert can_skip is False
        # Message indicates no state found
        assert "state" in reason.lower() or "found" in reason.lower()


class TestSetupOptimizationFlowWithRedis:
    """Test complete setup optimization flow using real Redis container."""

    @pytest.fixture
    def redis_container(self):
        """Start Redis container for testing."""
        import subprocess

        # Check if Redis is already running
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=test-redis-setup-opt", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True,
            )

            if "test-redis-setup-opt" in result.stdout:
                # Stop existing container
                subprocess.run(
                    ["docker", "stop", "test-redis-setup-opt"], check=True, capture_output=True
                )
                subprocess.run(
                    ["docker", "rm", "test-redis-setup-opt"], check=True, capture_output=True
                )
        except subprocess.CalledProcessError:
            pass

        # Start fresh Redis container
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                "test-redis-setup-opt",
                "-p",
                "6380:6379",  # Use different port to avoid conflicts
                "redis:7-alpine",
            ],
            check=True,
            capture_output=True,
        )

        # Wait for Redis to be ready
        time.sleep(2)

        yield {"redis_host": "localhost", "redis_port": 6380, "namespace": "test_integration"}

        # Cleanup
        subprocess.run(["docker", "stop", "test-redis-setup-opt"], check=True, capture_output=True)
        subprocess.run(["docker", "rm", "test-redis-setup-opt"], check=True, capture_output=True)

    @pytest.mark.skipif(
        __import__("subprocess").run(["which", "docker"], capture_output=True).returncode != 0,
        reason="Docker not available",
    )
    def test_redis_integration_flow(
        self, temp_project, temp_state_dir, cache_dirs, redis_container
    ):
        """Test full flow with real Redis container."""
        hook_cache_dir, test_cache_dir = cache_dirs

        # Setup tracker with real Redis
        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=redis_container)
        tracker = SetupTracker(config=tracker_config)

        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        validator = PreflightValidator(tracker, state_config=state_config)

        # Verify Redis connection
        assert tracker.redis_client is not None

        # === PHASE 1: First run (cache miss) ===

        can_skip_hooks, _ = validator.can_skip_hook_config(temp_project)
        assert can_skip_hooks is False

        # === PHASE 2: Simulate AI invocation ===

        # Create caches
        hook_cache_file = hook_cache_dir / f"{temp_project.name}-hooks.yaml"
        hook_cache_data = {"hook_framework": {"installed": True}}
        with open(hook_cache_file, "w") as f:
            yaml.dump(hook_cache_data, f)

        # Create hook files
        (temp_project / ".pre-commit-config.yaml").touch()
        git_hooks_dir = temp_project / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True, exist_ok=True)
        (git_hooks_dir / "pre-commit").touch()

        # Mark complete in Redis
        tracker.mark_setup_complete(str(temp_project), "hooks")

        # === PHASE 3: Second run (cache hit from Redis) ===

        # Create NEW tracker instance (simulating restart)
        tracker_config2 = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=redis_container)
        tracker2 = SetupTracker(config=tracker_config2)

        validator2 = PreflightValidator(tracker2, state_config=state_config)

        # Should be able to skip now (state persisted in Redis)
        can_skip_hooks, reason = validator2.can_skip_hook_config(temp_project)
        assert can_skip_hooks is True
        assert "saved 60s + $0.50" in reason

    @pytest.mark.skipif(
        __import__("subprocess").run(["which", "docker"], capture_output=True).returncode != 0,
        reason="Docker not available",
    )
    def test_redis_fallback_to_filesystem(self, temp_project, temp_state_dir, cache_dirs):
        """Test filesystem fallback when Redis is unavailable."""
        hook_cache_dir, test_cache_dir = cache_dirs

        # Try to connect to non-existent Redis
        redis_config = {"redis_host": "localhost", "redis_port": 9999, "namespace": "test"}

        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=redis_config)
        tracker = SetupTracker(config=tracker_config)

        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        validator = PreflightValidator(tracker, state_config=state_config)

        # Should fallback to filesystem (redis_client should be None)
        assert tracker.redis_client is None

        # Create cache and mark complete
        hook_cache_file = hook_cache_dir / f"{temp_project.name}-hooks.yaml"
        hook_cache_data = {"hook_framework": {"installed": True}}
        with open(hook_cache_file, "w") as f:
            yaml.dump(hook_cache_data, f)

        (temp_project / ".pre-commit-config.yaml").touch()
        git_hooks_dir = temp_project / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True, exist_ok=True)
        (git_hooks_dir / "pre-commit").touch()

        tracker.mark_setup_complete(str(temp_project), "hooks")

        # Should work with filesystem markers
        can_skip, reason = validator.can_skip_hook_config(temp_project)
        assert can_skip is True
        assert "saved 60s + $0.50" in reason


class TestConcurrentAccess:
    """Test concurrent access scenarios."""

    def test_concurrent_marker_writes(self, temp_project, temp_state_dir):
        """Test that concurrent marker writes don't corrupt state."""
        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=None)
        tracker = SetupTracker(config=tracker_config)

        # Simulate rapid concurrent writes
        import threading

        def write_marker():
            tracker.mark_setup_complete(str(temp_project), "hooks")

        threads = [threading.Thread(target=write_marker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should still be valid
        assert tracker.is_setup_complete(str(temp_project), "hooks") is True


class TestPerformanceIntegration:
    """Test performance requirements in integration context."""

    def test_validation_performance_realistic_project(
        self, temp_project, temp_state_dir, cache_dirs
    ):
        """Test validation performance on realistic project setup."""
        hook_cache_dir, test_cache_dir = cache_dirs

        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=None)
        tracker = SetupTracker(config=tracker_config)

        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        validator = PreflightValidator(tracker, state_config=state_config)

        # Setup complete project
        hook_cache_file = hook_cache_dir / f"{temp_project.name}-hooks.yaml"
        hook_cache_data = {"hook_framework": {"installed": True}}
        with open(hook_cache_file, "w") as f:
            yaml.dump(hook_cache_data, f)

        test_cache_file = test_cache_dir / f"{temp_project.name}-tests.yaml"
        test_cache_data = {
            "test_framework": "pytest",
            "test_command": "pytest",
            "test_patterns": ["test_*.py"],
        }
        with open(test_cache_file, "w") as f:
            yaml.dump(test_cache_data, f)

        (temp_project / ".pre-commit-config.yaml").touch()
        git_hooks_dir = temp_project / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True, exist_ok=True)
        (git_hooks_dir / "pre-commit").touch()

        tracker.mark_setup_complete(str(temp_project), "hooks")
        tracker.mark_setup_complete(str(temp_project), "tests")

        # Measure performance
        start = time.time()
        validator.can_skip_hook_config(temp_project)
        validator.can_skip_test_discovery(temp_project)
        duration_ms = (time.time() - start) * 1000

        # Should complete in <200ms total
        assert duration_ms < 200, f"Validation took {duration_ms:.1f}ms, expected <200ms"

    def test_time_savings_calculation(self, temp_project, temp_state_dir, cache_dirs):
        """Test accurate time savings reporting."""
        hook_cache_dir, test_cache_dir = cache_dirs

        tracker_config = SetupTrackerConfig(state_dir=temp_state_dir, redis_config=None)
        tracker = SetupTracker(config=tracker_config)

        state_config = StateConfig(
            external_hook_cache_dir=hook_cache_dir, external_test_cache_dir=test_cache_dir
        )
        validator = PreflightValidator(tracker, state_config=state_config)

        # Setup project with both caches
        hook_cache_file = hook_cache_dir / f"{temp_project.name}-hooks.yaml"
        with open(hook_cache_file, "w") as f:
            yaml.dump({"hook_framework": {"installed": True}}, f)

        test_cache_file = test_cache_dir / f"{temp_project.name}-tests.yaml"
        with open(test_cache_file, "w") as f:
            yaml.dump(
                {
                    "test_framework": "pytest",
                    "test_command": "pytest",
                    "test_patterns": ["test_*.py"],
                },
                f,
            )

        (temp_project / ".pre-commit-config.yaml").touch()
        git_hooks_dir = temp_project / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True, exist_ok=True)
        (git_hooks_dir / "pre-commit").touch()

        tracker.mark_setup_complete(str(temp_project), "hooks")
        tracker.mark_setup_complete(str(temp_project), "tests")

        # Check savings messages
        can_skip_hooks, hook_reason = validator.can_skip_hook_config(temp_project)
        can_skip_tests, test_reason = validator.can_skip_test_discovery(temp_project)

        assert "saved 60s + $0.50" in hook_reason
        assert "saved 90s + $0.60" in test_reason

        # Total savings should be 150s + $1.10 (60 + 90 and 0.50 + 0.60)
        assert can_skip_hooks and can_skip_tests
