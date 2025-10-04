"""Language adapters for multi-language autonomous fixing."""

from .base import AnalysisResult, LanguageAdapter
from .flutter_adapter import FlutterAdapter
from .go_adapter import GoAdapter
from .javascript_adapter import JavaScriptAdapter
from .python_adapter import PythonAdapter

__all__ = [
    'LanguageAdapter',
    'AnalysisResult',
    'FlutterAdapter',
    'PythonAdapter',
    'JavaScriptAdapter',
    'GoAdapter',
]
