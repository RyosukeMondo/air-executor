"""Tests for calculator module."""

import pytest
from src.calculator import add, subtract, multiply, divide, complex_calculator


# PASSING TESTS
def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    """Test subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5


def test_multiply():
    """Test multiplication."""
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0


# FAILING TEST - Intentional failure
def test_divide_basic():
    """Test division - FAILS intentionally."""
    assert divide(10, 2) == 5
    assert divide(9, 3) == 3
    assert divide(7, 2) == 3.5
    # FAILURE: Wrong assertion
    assert divide(10, 4) == 3  # Should be 2.5, this will FAIL


def test_divide_by_zero():
    """Test division by zero raises error."""
    with pytest.raises(ValueError):
        divide(10, 0)


# PARTIAL COVERAGE - complex_calculator only tested for some operations
def test_complex_calculator_add():
    """Test complex calculator add operation."""
    assert complex_calculator("add", 5, 3) == 8


def test_complex_calculator_multiply():
    """Test complex calculator multiply operation."""
    assert complex_calculator("multiply", 4, 5) == 20


# FAILING TEST - Wrong expectation
def test_complex_calculator_power():
    """Test complex calculator power - FAILS."""
    # FAILURE: Wrong expected value
    assert complex_calculator("power", 2, 3) == 6  # Should be 8, this will FAIL


# NO TESTS for:
# - advanced_math() -> NO COVERAGE
# - handle_edge_cases() -> NO COVERAGE
# - complex_calculator() other operations -> PARTIAL COVERAGE
