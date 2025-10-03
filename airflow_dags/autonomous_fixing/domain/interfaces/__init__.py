"""Domain interfaces for dependency inversion."""
from .language_adapter import ILanguageAdapter
from .health_monitor import IHealthMonitor
from .state_store import IStateStore, ITaskRepository
from .code_fixer import ICodeFixer
from .issue_discoverer import IIssueDiscoverer

__all__ = [
    'ILanguageAdapter',
    'IHealthMonitor',
    'IStateStore',
    'ITaskRepository',
    'ICodeFixer',
    'IIssueDiscoverer',
]
