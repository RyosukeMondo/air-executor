"""Python project detection."""

from pathlib import Path
from typing import List


class PythonProjectDetector:
    """Detects Python projects in a directory tree."""

    def __init__(self):
        self.project_markers = ["setup.py", "pyproject.toml", "requirements.txt", "setup.cfg"]

    def detect_projects(self, root_path: str) -> List[str]:
        """
        Find all Python projects in a directory tree.

        Args:
            root_path: Root directory to search

        Returns:
            List of project paths
        """
        projects = []
        root = Path(root_path)

        # Look for project markers
        for marker in self.project_markers:
            for file_path in root.rglob(marker):
                project_dir = file_path.parent
                if str(project_dir) not in projects:
                    projects.append(str(project_dir))

        return projects

    def get_source_files(self, project_path: Path) -> List[Path]:
        """
        Get all Python source files in a project.

        Args:
            project_path: Project directory

        Returns:
            List of Python source files
        """
        source_files = []
        for pattern in ['**/*.py']:
            source_files.extend(project_path.rglob(pattern))

        # Exclude common non-source directories
        excluded = {'venv', '.venv', 'env', '__pycache__', '.tox', 'build', 'dist'}
        return [f for f in source_files if not any(e in f.parts for e in excluded)]
