"""
Commit Verifier - Verifies that Claude actually committed changes.

Prevents false success reports by ensuring commits were made.
"""

from ..adapters.git.git_verifier import GitVerifier


class CommitVerifier:
    """Verifies commits were made after fix operations."""

    def __init__(self):
        """Initialize commit verifier."""
        self.git_verifier = GitVerifier()

    def verify_fix_committed(self, project_path: str, before_commit: str, operation: str) -> bool:
        """
        Verify that a commit was made after a fix operation.

        Args:
            project_path: Path to the project
            before_commit: Git commit hash before the operation
            operation: Description of the operation (for error messages)

        Returns: True if commit verified, False otherwise
        """
        verification = self.git_verifier.verify_commit_made(project_path, before_commit, operation)

        if not verification["verified"]:
            print("      ❌ ABORT: Claude said success but no commit detected!")
            print(f"      {verification['message']}")
            print(f"      This indicates a problem with claude_wrapper or the {operation}.")
            return False

        print(f"      ✅ Verified: {verification['message']}")
        return True

    def get_head_commit(self, project_path: str) -> str:
        """Get current HEAD commit before operation."""
        return self.git_verifier.get_head_commit(project_path)
