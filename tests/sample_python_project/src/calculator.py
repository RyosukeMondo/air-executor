"""Calculator module with intentional issues for testing."""

import math  # Used
import os  # ISSUE: Unused import
from typing import Optional


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def multiply(a, b):  # ISSUE: Missing type hints (mypy error)
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


# ISSUE: High cyclomatic complexity function (complexity > 10)
def complex_calculator(operation: str, a: float, b: float, c: Optional[float] = None) -> float:
    """
    Complex calculator with many branches.
    This function has HIGH COMPLEXITY for testing.
    """
    result = 0.0

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Division by zero")
        result = a / b
    elif operation == "power":
        result = a ** b
    elif operation == "sqrt":
        if a < 0:
            raise ValueError("Cannot sqrt negative")
        result = math.sqrt(a)
    elif operation == "modulo":
        if b == 0:
            raise ValueError("Modulo by zero")
        result = a % b
    elif operation == "triple_add":
        if c is None:
            raise ValueError("Need c for triple_add")
        result = a + b + c
    elif operation == "triple_multiply":
        if c is None:
            raise ValueError("Need c for triple_multiply")
        result = a * b * c
    elif operation == "average":
        if c is None:
            result = (a + b) / 2
        else:
            result = (a + b + c) / 3
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return result


# NO COVERAGE: This function is never tested
def advanced_math(x: float, y: float) -> float:
    """
    Advanced math function with NO test coverage.
    This tests the P3 coverage phase.
    """
    if x > y:
        return x ** 2 + y ** 2
    elif x < y:
        return math.sqrt(abs(x)) + math.sqrt(abs(y))
    else:
        return x * y


# NO COVERAGE: Edge case handler
def handle_edge_cases(value: Optional[int]) -> int:
    """Handle edge cases - UNCOVERED."""
    if value is None:
        return 0
    if value < 0:
        return abs(value)
    if value > 1000:
        return 1000
    return value
