"""Task and fix result models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    """A fixable issue/task."""

    id: str
    type: str  # 'fix_build_error', 'fix_test_failure', 'fix_lint', etc.
    priority: int  # 1-10, 1 = highest

    # Optional fields for backward compatibility
    project_path: str | None = None
    language: str | None = None
    phase: str | None = None  # 'build', 'test', 'lint' (old model)
    file: str | None = None
    line: int | None = None
    message: str = ""
    context: str = ""

    # Task-specific details (flexible storage)
    details: dict = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # 'pending', 'in_progress', 'completed', 'failed'
    error_message: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization (include all fields)."""
        from dataclasses import asdict

        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Task":
        """Create from dictionary (filter valid fields only)."""
        from dataclasses import fields

        valid_fields = {f.name for f in fields(Task)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return Task(**filtered_data)


@dataclass
class FixResult:
    """Result from fixing issues."""

    fixes_applied: int = 0
    fixes_attempted: int = 0
    success: bool = False
    error_message: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "fixes_applied": self.fixes_applied,
            "fixes_attempted": self.fixes_attempted,
            "success": self.success,
            "error_message": self.error_message,
        }

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.fixes_attempted == 0:
            return 0.0
        return self.fixes_applied / self.fixes_attempted
