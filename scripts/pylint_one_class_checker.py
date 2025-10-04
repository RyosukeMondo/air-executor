"""
Custom Pylint plugin to enforce one class per file rule.

Usage:
    Add to .pylintrc:
    [MAIN]
    load-plugins=scripts.pylint_one_class_checker
"""

import astroid
from pylint.checkers import BaseChecker


class OneClassPerFileChecker(BaseChecker):
    """Check that each module contains at most one class definition."""

    name = "one-class-per-file"
    msgs = {
        "C9001": (
            "Module contains %s classes, maximum is 1",
            "too-many-classes-in-module",
            "Each module should contain at most one class for better maintainability.",
        ),
    }
    # Maximum classes per module (hardcoded to 1)
    MAX_CLASSES = 1

    def __init__(self, linter=None):
        super().__init__(linter)
        self.class_count = 0

    def visit_module(self, node: astroid.Module) -> None:
        """Reset counter at module start."""
        self.class_count = 0

    def visit_classdef(self, node: astroid.ClassDef) -> None:
        """Count class definitions."""
        # Only count top-level classes (not nested)
        if isinstance(node.parent, astroid.Module):
            self.class_count += 1

    def leave_module(self, node: astroid.Module) -> None:
        """Check class count when leaving module."""
        if self.class_count > self.MAX_CLASSES:
            self.add_message(
                "too-many-classes-in-module",
                node=node,
                args=(self.class_count,),
            )


def register(linter):
    """Register the checker with pylint."""
    linter.register_checker(OneClassPerFileChecker(linter))
