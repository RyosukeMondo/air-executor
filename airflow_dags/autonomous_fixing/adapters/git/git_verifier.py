"""
Git Verifier - Verify that fixes result in actual git commits.

Prevents wasteful iterations where Claude says "success" but nothing was actually done.

NOTE: This is now a compatibility wrapper around common.progress_tracker.ProgressTracker.
      For new code, use ProgressTracker directly.
"""

import logging

from airflow_dags.common.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class GitVerifier:
    """
    Verify that fixes result in git commits.

    DEPRECATED: This is now a compatibility wrapper. Use common.progress_tracker.ProgressTracker directly.

    Responsibilities:
    - Get current HEAD commit before fix
    - Check if new commit exists after fix
    - Abort if no commit detected

    Does NOT:
    - Make commits (that's claude_wrapper's job)
    - Modify files (just verifies)
    """

    def __init__(self):
        """Initialize git verifier."""
        # No state needed - ProgressTracker instances are created per-call
        pass

    def get_head_commit(self, project_path: str) -> str | None:
        """
        Get current HEAD commit hash.

        Args:
            project_path: Path to git repository

        Returns:
            Commit hash or None if not a git repo
        """
        tracker = ProgressTracker(project_path)
        commit_id = tracker.get_current_commit_id()

        if commit_id is None:
            logger.warning(f"Git check failed for {project_path}")

        return commit_id

    def verify_commit_made(
        self, project_path: str, before_commit: str | None, operation: str
    ) -> dict:
        """
        Verify that a new commit was made.

        Args:
            project_path: Path to git repository
            before_commit: HEAD commit before fix
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
        logger.debug(f"Verifying commit for operation: {operation}")
        logger.debug(f"Project path: {project_path}")
        logger.debug(f"Before commit: {before_commit}")

        tracker = ProgressTracker(project_path)
        result = tracker.verify_commit_made(project_path, before_commit, operation)

        # Log based on result
        if result["verified"]:
            logger.info(
                f"Commit verified for {operation} in {project_path}: "
                f"{before_commit[:8] if before_commit else 'unknown'} → {result['new_commit'][:8]}"
            )
        else:
            logger.warning(
                f"No commit detected after {operation} in {project_path}: {result['message']}"
            )

        return result

    def get_commit_message(self, project_path: str, commit_hash: str) -> str | None:
        """
        Get commit message for a commit.

        Args:
            project_path: Path to git repository
            commit_hash: Commit hash

        Returns:
            Commit message or None
        """
        tracker = ProgressTracker(project_path)
        return tracker.get_commit_message(project_path, commit_hash)
