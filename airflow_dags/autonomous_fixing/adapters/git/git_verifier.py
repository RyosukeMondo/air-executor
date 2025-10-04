"""
Git Verifier - Verify that fixes result in actual git commits.

Prevents wasteful iterations where Claude says "success" but nothing was actually done.
"""

import logging
import subprocess

logger = logging.getLogger(__name__)


class GitVerifier:
    """
    Verify that fixes result in git commits.

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
        pass

    def get_head_commit(self, project_path: str) -> str | None:
        """
        Get current HEAD commit hash.

        Args:
            project_path: Path to git repository

        Returns:
            Commit hash or None if not a git repo
        """
        try:
            result = subprocess.run(
                ["git", "-C", project_path, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None

        except Exception as e:
            print(f"      ⚠️  Git check failed: {e}")
            return None

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

        # If we couldn't get before commit, can't verify
        if before_commit is None:
            logger.warning(f"No initial commit hash available for {project_path}")
            return {
                "verified": False,
                "commit_made": False,
                "new_commit": None,
                "message": "Could not get initial commit hash",
            }

        # Get current HEAD
        after_commit = self.get_head_commit(project_path)
        logger.debug(f"After commit: {after_commit}")

        if after_commit is None:
            logger.warning(f"Could not get post-fix commit hash for {project_path}")
            return {
                "verified": False,
                "commit_made": False,
                "new_commit": None,
                "message": "Could not get post-fix commit hash",
            }

        # Check if commit changed
        if after_commit == before_commit:
            logger.warning(
                f"No commit detected after {operation} in {project_path} "
                f"(before={before_commit[:8]}, after={after_commit[:8]})"
            )
            return {
                "verified": False,
                "commit_made": False,
                "new_commit": None,
                "message": f"No commit detected after {operation}",
            }

        # Success - commit was made
        logger.info(
            f"Commit verified for {operation} in {project_path}: "
            f"{before_commit[:8]} → {after_commit[:8]}"
        )
        return {
            "verified": True,
            "commit_made": True,
            "new_commit": after_commit,
            "message": f"Commit verified: {after_commit[:8]}",
        }

    def get_commit_message(self, project_path: str, commit_hash: str) -> str | None:
        """
        Get commit message for a commit.

        Args:
            project_path: Path to git repository
            commit_hash: Commit hash

        Returns:
            Commit message or None
        """
        try:
            result = subprocess.run(
                ["git", "-C", project_path, "log", "-1", "--format=%s", commit_hash],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None

        except Exception:
            return None
