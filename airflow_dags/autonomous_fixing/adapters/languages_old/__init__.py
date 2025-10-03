"""Language adapters for multi-language autonomous fixing."""

from .base import LanguageAdapter, AnalysisResult
from .flutter_adapter import FlutterAdapter
from .python_adapter import PythonAdapter
from .javascript_adapter import JavaScriptAdapter
from .go_adapter import GoAdapter

__all__ = [
    'LanguageAdapter',
    'AnalysisResult',
    'FlutterAdapter',
    'PythonAdapter',
    'JavaScriptAdapter',
    'GoAdapter',
]
