"""Language adapters for multi-language autonomous fixing."""

# Import models from domain (don't re-export from here)
from ...domain.models import AnalysisResult, ToolValidationResult
from .base import LanguageAdapter
from .flutter_adapter import FlutterAdapter
from .go_adapter import GoAdapter
from .javascript_adapter import JavaScriptAdapter
from .python import PythonAdapter  # NEW: Import from python package

__all__ = [
    'LanguageAdapter',
    'FlutterAdapter',
    'PythonAdapter',
    'JavaScriptAdapter',
    'GoAdapter',
]
