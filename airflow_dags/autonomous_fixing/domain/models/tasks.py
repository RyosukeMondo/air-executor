"""Task and fix result models."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Task:
    """A fixable issue/task."""
    id: str
    type: str  # 'fix_build_error', 'fix_test_failure', 'fix_lint', etc.
    priority: int  # 1-10, 1 = highest
    project_path: str
    language: str

    # Task-specific details
    details: Dict = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'failed'
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.type,
            'priority': self.priority,
            'project_path': self.project_path,
            'language': self.language,
            'details': self.details,
            'created_at': self.created_at,
            'status': self.status,
            'error_message': self.error_message,
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Task':
        """Create from dictionary."""
        return Task(**data)


@dataclass
class FixResult:
    """Result from fixing issues."""
    fixes_applied: int = 0
    fixes_attempted: int = 0
    success: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'fixes_applied': self.fixes_applied,
            'fixes_attempted': self.fixes_attempted,
            'success': self.success,
            'error_message': self.error_message,
        }

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.fixes_attempted == 0:
            return 0.0
        return self.fixes_applied / self.fixes_attempted
