"""Domain interfaces for dependency inversion."""
from .code_fixer import ICodeFixer
from .health_monitor import IHealthMonitor
from .issue_discoverer import IIssueDiscoverer
from .language_adapter import ILanguageAdapter
from .state_store import IStateStore, ITaskRepository

__all__ = [
    'ILanguageAdapter',
    'IHealthMonitor',
    'IStateStore',
    'ITaskRepository',
    'ICodeFixer',
    'IIssueDiscoverer',
]
