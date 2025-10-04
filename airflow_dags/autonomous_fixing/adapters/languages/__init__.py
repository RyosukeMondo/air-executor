"""Language adapters for multi-language autonomous fixing."""

from .base import LanguageAdapter
from .flutter_adapter import FlutterAdapter
from .go_adapter import GoAdapter
from .javascript_adapter import JavaScriptAdapter
from .python_adapter import PythonAdapter  # Import from python_adapter.py

__all__ = [
    "FlutterAdapter",
    "GoAdapter",
    "JavaScriptAdapter",
    "LanguageAdapter",
    "PythonAdapter",
]
