"""Language adapters for multi-language autonomous fixing."""

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
