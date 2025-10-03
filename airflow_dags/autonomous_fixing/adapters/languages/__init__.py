"""Language adapters for multi-language autonomous fixing."""

from .base import LanguageAdapter
from .flutter_adapter import FlutterAdapter
from .python import PythonAdapter  # NEW: Import from python package
from .javascript_adapter import JavaScriptAdapter
from .go_adapter import GoAdapter

# Import models from domain (don't re-export from here)
from ...domain.models import AnalysisResult, ToolValidationResult

__all__ = [
    'LanguageAdapter',
    'FlutterAdapter',
    'PythonAdapter',
    'JavaScriptAdapter',
    'GoAdapter',
]
