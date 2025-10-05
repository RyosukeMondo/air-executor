"""
Progress Tracker - Unified git-based progress detection and circuit breaker.

Single Source of Truth for progress tracking across all orchestrators.
Combines functionality from:
- simple_autonomous_iteration circuit breaker
- autonomous_fixing GitVerifier
"""

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProgressState:
    """
    Progress tracking state.

    Tracks both commits and uncommitted changes for comprehensive detection.
    """

    last_commit_id: Optional[str] = None
    last_diff_hash: Optional[str] = None
    iterations_without_progress: int = 0


class ProgressTracker:
    """
    Track git-based progress with circuit breaker functionality.

    Responsibilities:
    - Detect new commits (most reliable indicator)
    - Detect uncommitted changes (work in progress)
    - Circuit breaker: Stop after N iterations without progress
    - Provide detailed diagnostic messages

    Does NOT:
    - Make commits (that's the wrapper's job)
    - Modify files (just observes)
    """

    def __init__(
        self,
        project_path: str | Path,
        *,
        circuit_breaker_threshold: int = 3,
        require_git_changes: bool = True,
    ):
        """
        Initialize progress tracker.

        Args:
            project_path: Path to git repository
            circuit_breaker_threshold: Stop after N iterations without progress
            require_git_changes: Whether to enforce git change requirement
        """
        self.project_path = Path(project_path)
        self.threshold = circuit_breaker_threshold
        self.require_git_changes = require_git_changes
        self.state = ProgressState()

    def get_current_commit_id(self) -> Optional[str]:
        """
        Get the current commit ID (HEAD).

        Returns:
            Commit SHA, or None if not a git repo or error
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def get_git_diff_hash(self) -> Optional[str]:
        """
        Get hash of current git diff to detect uncommitted changes.

        Returns:
            Hash of git diff, or None if not a git repo or error
        """
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return hashlib.md5(result.stdout.encode(), usedforsecurity=False).hexdigest()
            return None
        except Exception:
            return None

    def check_progress(self) -> tuple[bool, str]:
        """
        Check if progress was made since last check.

        Detects both:
        1. New commits (via commit ID comparison) - most reliable
        2. Uncommitted changes (via diff hash comparison)

        Returns:
            Tuple of (has_progress, diagnostic_message)
        """
        if not self.require_git_changes:
            return True, "Git change tracking disabled"

        current_commit = self.get_current_commit_id()
        current_diff_hash = self.get_git_diff_hash()

        if current_commit is None:
            return True, "Not a git repo or git error (skipping check)"

        # First iteration - establish baseline
        if self.state.last_commit_id is None:
            self.state.last_commit_id = current_commit
            self.state.last_diff_hash = current_diff_hash
            return True, f"First check (baseline: {current_commit[:8]})"

        # Check for new commits (most reliable indicator)
        if current_commit != self.state.last_commit_id:
            self.state.last_commit_id = current_commit
            self.state.last_diff_hash = current_diff_hash
            self.state.iterations_without_progress = 0
            return (
                True,
                f"New commit detected: {current_commit[:8]} "
                f"(was {self.state.last_commit_id[:8] if self.state.last_commit_id else 'unknown'})",
            )

        # Check for uncommitted changes
        if current_diff_hash != self.state.last_diff_hash:
            self.state.last_diff_hash = current_diff_hash
            self.state.iterations_without_progress = 0
            return True, f"Uncommitted changes detected (commit: {current_commit[:8]})"

        # No progress detected
        self.state.iterations_without_progress += 1
        return False, f"No changes detected (commit: {current_commit[:8]}, no uncommitted changes)"

    def should_trigger_circuit_breaker(self) -> tuple[bool, str]:
        """
        Check if circuit breaker should trigger.

        Returns:
            Tuple of (should_abort, diagnostic_message)
        """
        if self.state.iterations_without_progress >= self.threshold:
            # Provide detailed diagnostic information
            current_commit = self.get_current_commit_id()
            commit_info = (
                f"(current commit: {current_commit[:8]})" if current_commit else "(no git info)"
            )

            return True, (
                f"Circuit breaker triggered: {self.state.iterations_without_progress} iterations "
                f"without progress (threshold: {self.threshold}) {commit_info}\n"
                f"  Expected: New commits OR uncommitted changes\n"
                f"  Detected: No new commits since "
                f"{self.state.last_commit_id[:8] if self.state.last_commit_id else 'unknown'}, "
                f"no uncommitted changes"
            )

        progress_status = (
            f"{self.state.iterations_without_progress}/{self.threshold} iterations without progress"
        )
        return False, f"Circuit breaker OK ({progress_status})"

    def reset(self) -> None:
        """Reset progress tracking state."""
        self.state = ProgressState()

    # Compatibility methods for GitVerifier interface
    def get_head_commit(self, _project_path: Optional[str] = None) -> Optional[str]:
        """
        Get current HEAD commit hash (GitVerifier compatibility).

        Args:
            project_path: Path override (ignored, uses instance path)

        Returns:
            Commit hash or None if not a git repo
        """
        return self.get_current_commit_id()

    def verify_commit_made(
        self, _project_path: str, before_commit: Optional[str], operation: str
    ) -> dict:
        """
        Verify that a new commit was made (GitVerifier compatibility).

        Args:
            project_path: Path to git repository (ignored, uses instance path)
            before_commit: HEAD commit before operation
            operation: Description of operation (for logging)

        Returns:
            Dict with verification result:
            {
                'verified': bool,
                'commit_made': bool,
                'new_commit': str or None,
                'message': str
            }
        """
        # If we couldn't get before commit, can't verify
        if before_commit is None:
            return {
                "verified": False,
                "commit_made": False,
                "new_commit": None,
                "message": "Could not get initial commit hash",
            }

        # Get current HEAD
        after_commit = self.get_current_commit_id()

        if after_commit is None:
            return {
                "verified": False,
                "commit_made": False,
                "new_commit": None,
                "message": "Could not get post-fix commit hash",
            }

        # Check if commit changed
        if after_commit == before_commit:
            return {
                "verified": False,
                "commit_made": False,
                "new_commit": None,
                "message": f"No commit detected after {operation}",
            }

        # Success - commit was made
        return {
            "verified": True,
            "commit_made": True,
            "new_commit": after_commit,
            "message": f"Commit verified: {after_commit[:8]}",
        }

    def get_commit_message(self, _project_path: str, commit_hash: str) -> Optional[str]:
        """
        Get commit message for a commit (GitVerifier compatibility).

        Args:
            project_path: Path to git repository (ignored, uses instance path)
            commit_hash: Commit hash

        Returns:
            Commit message or None
        """
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%s", commit_hash],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None

        except Exception:
            return None
