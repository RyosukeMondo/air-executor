"""Domain interfaces for dependency inversion."""

from .code_fixer import ICodeFixer
from .health_monitor import IHealthMonitor
from .issue_discoverer import IIssueDiscoverer
from .language_adapter import ILanguageAdapter
from .setup_tracker import ISetupTracker
from .state_repository import IStateRepository
from .state_store import IStateStore, ITaskRepository

__all__ = [
    "ICodeFixer",
    "IHealthMonitor",
    "IIssueDiscoverer",
    "ILanguageAdapter",
    "ISetupTracker",
    "IStateRepository",
    "IStateStore",
    "ITaskRepository",
]
