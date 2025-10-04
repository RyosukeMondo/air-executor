"""Unit tests for complexity calculation accuracy.

These tests verify that calculate_complexity returns accurate values
and doesn't silently fall back to incorrect heuristics.
"""

import pytest
import subprocess
import sys
from pathlib import Path

from airflow_dags.autonomous_fixing.adapters.languages.python_adapter import PythonAdapter


class TestComplexityCalculation:
    """Test complexity calculation accuracy and error handling."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with standard config."""
        return PythonAdapter({
            'complexity_threshold': 15,
            'max_file_lines': 500,
            'linters': ['ruff', 'mypy']
        })

    @pytest.fixture
    def test_file(self, tmp_path):
        """Create a test file with known complexity."""
        # Simple function with complexity 1
        simple_code = """
def simple_function(x):
    return x + 1
"""

        # Complex function with complexity 7 (6 decision points + 1)
        complex_code = """
def complex_function(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c
            else:
                return a + b
        elif b < 0:
            return a - b
        else:
            return a
    elif a < 0:
        if b > 0:
            return b - a
        else:
            return -a
    else:
        return 0
"""

        test_file = tmp_path / "test_complexity.py"
        test_file.write_text(simple_code + complex_code)
        return test_file

    def test_radon_is_available(self):
        """Radon must be available via sys.executable -m radon."""
        result = subprocess.run(
            [sys.executable, "-m", "radon", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Radon not available! Install with: pip install radon\n"
            f"Error: {result.stderr}"
        )

    def test_calculate_complexity_with_simple_function(self, adapter, tmp_path):
        """Complexity calculation should return low value for simple functions."""
        simple_file = tmp_path / "simple.py"
        simple_file.write_text("""
def add(a, b):
    return a + b
""")

        complexity = adapter.calculate_complexity(str(simple_file))
        assert complexity <= 2, f"Simple function should have complexity <= 2, got {complexity}"

    def test_calculate_complexity_with_complex_function(self, adapter, test_file):
        """Complexity calculation should return accurate value for complex functions."""
        complexity = adapter.calculate_complexity(str(test_file))

        # The complex_function has 6 if/elif/else decision points + 1 = 7
        # Should be close to 7 (radon might calculate slightly differently)
        assert 5 <= complexity <= 8, (
            f"Complex function should have complexity ~7, got {complexity}\n"
            "If this fails, radon might be falling back to keyword counting heuristic"
        )

    def test_calculate_complexity_on_real_file(self, adapter):
        """Test complexity calculation on actual project file."""
        # Use spawner.py which we know has max complexity 7
        spawner_file = Path("/home/rmondo/repos/air-executor/src/air_executor/manager/spawner.py")

        if not spawner_file.exists():
            pytest.skip("spawner.py not found")

        complexity = adapter.calculate_complexity(str(spawner_file))

        # spawner.py was refactored to have complexity 7
        assert complexity <= 10, (
            f"spawner.py should have complexity <= 10, got {complexity}\n"
            "This file was refactored to reduce complexity"
        )

        # If complexity is way too high (e.g., 44), it means radon failed
        # and fallback heuristic was used (counting keywords)
        assert complexity < 20, (
            f"Complexity {complexity} is suspiciously high!\n"
            "This suggests radon failed and keyword counting heuristic was used.\n"
            "Bug: radon not accessible via subprocess"
        )

    def test_complexity_matches_radon_output(self, adapter, test_file):
        """Verify adapter complexity matches direct radon call."""
        # Get complexity from adapter
        adapter_complexity = adapter.calculate_complexity(str(test_file))

        # Get complexity directly from radon
        result = subprocess.run(
            [sys.executable, "-m", "radon", "cc", str(test_file), "-s", "-n", "A"],
            capture_output=True,
            text=True
        )

        # Parse radon output to find max complexity
        import re
        max_radon_complexity = 0
        for match in re.finditer(r"\((\d+)\)", result.stdout):
            complexity = int(match.group(1))
            max_radon_complexity = max(max_radon_complexity, complexity)

        # They should match exactly
        assert adapter_complexity == max_radon_complexity, (
            f"Adapter complexity ({adapter_complexity}) doesn't match "
            f"radon output ({max_radon_complexity})\n"
            f"Radon output:\n{result.stdout}"
        )

    def test_no_silent_failures(self, adapter, monkeypatch):
        """Complexity calculation should NOT silently fall back on errors."""
        def mock_run_fail(*args, **kwargs):
            raise FileNotFoundError("radon not found")

        # Mock subprocess.run to simulate radon failure
        import subprocess as sp
        monkeypatch.setattr(sp, "run", mock_run_fail)

        # Should raise error, NOT silently return wrong value
        with pytest.raises(Exception):
            adapter.calculate_complexity("/some/file.py")

    def test_nonexistent_file_raises_error(self, adapter):
        """Calculating complexity of nonexistent file should raise error."""
        with pytest.raises(Exception):
            adapter.calculate_complexity("/nonexistent/file.py")


class TestComplexityHeuristic:
    """Test the fallback complexity heuristic (should rarely be used)."""

    @pytest.fixture
    def adapter(self):
        return PythonAdapter({'complexity_threshold': 10})

    def test_simple_complexity_counts_control_flow(self, adapter, tmp_path):
        """Simple complexity heuristic counts control flow keywords."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def func():
    if True:
        for x in range(10):
            while x > 0:
                if x and y or z:
                    pass
""")

        complexity = adapter._simple_complexity(str(test_file))

        # Should count: 2 if, 1 for, 1 while, 1 and, 1 or = 6 + base 1 = 7
        assert complexity >= 6, f"Expected >= 6, got {complexity}"
