# Linting Setup Guide - Hybrid Ruff + Pylint

## Overview

This project uses a **hybrid linting approach**:
- **Ruff**: Fast daily checks (complexity, style, imports)
- **Pylint**: Comprehensive metrics (lines per file, classes per file, detailed design checks)

## Quick Start

```bash
# Install dependencies
source .venv/bin/activate
pip install -r requirements-dev.txt

# Use the wrapper script (recommended)
./scripts/lint.sh                    # Fast check on airflow_dags/
./scripts/lint.sh --full             # Comprehensive check (ruff + pylint)
./scripts/lint.sh --fix              # Auto-fix issues
./scripts/lint.sh path/to/file.py    # Check specific file

# Or run tools directly
ruff check airflow_dags/             # Fast check
PYTHONPATH=. pylint airflow_dags/    # Comprehensive check
ruff check --fix airflow_dags/       # Fix auto-fixable issues
```

## Ruff Configuration

**Speed**: ⚡ Extremely fast (Rust-based)
**Use case**: Daily development, CI/CD fast feedback

### What Ruff Checks
- **E**: PEP 8 style errors
- **F**: Pyflakes (unused imports, undefined names)
- **I**: Import ordering (isort)
- **N**: PEP 8 naming conventions
- **W**: PEP 8 warnings
- **C90**: McCabe cyclomatic complexity (max: 10)

### Config Location
`pyproject.toml` → `[tool.ruff.lint]`

### Usage
```bash
# Check all Python files
ruff check .

# Check specific directory
ruff check airflow_dags/

# Auto-fix issues
ruff check --fix .

# Watch mode (continuous checking)
ruff check --watch .
```

## Pylint Configuration

**Speed**: 🐌 Slower but thorough
**Use case**: Pre-commit, PR reviews, comprehensive analysis

### What Pylint Checks

#### Design Metrics
- **Cyclomatic complexity**: max 10 (via McCabe)
- **Lines per file**: max 500 (`too-many-lines`)
- **Classes per file**: max 1 (custom checker)
- **Function arguments**: max 5
- **Local variables**: max 15
- **Class attributes**: max 7
- **Nested blocks**: max 5
- **Return statements**: max 6
- **Branches per function**: max 12
- **Statements per function**: max 50

#### Code Quality
- Naming conventions (snake_case, PascalCase)
- Duplicate code detection
- Unused variables/imports
- Missing documentation
- Code smells

### Config Location
`.pylintrc` (root directory)

### Custom Plugin
**One Class Per File Checker** (`scripts/pylint_one_class_checker.py`)
- Enforces maximum 1 top-level class per module
- Error code: `C9001` (too-many-classes-in-module)

### Usage
```bash
# Check entire project (IMPORTANT: set PYTHONPATH for custom plugin)
PYTHONPATH=. pylint airflow_dags/

# Check specific file
PYTHONPATH=. pylint airflow_dags/autonomous_fixing/core/analyzer.py

# Check with score
PYTHONPATH=. pylint airflow_dags/ --score=y

# Generate HTML report
PYTHONPATH=. pylint airflow_dags/ --output-format=html > pylint_report.html

# Disable specific checks
PYTHONPATH=. pylint airflow_dags/ --disable=C0114,C0116

# Or use the wrapper script (handles PYTHONPATH automatically)
./scripts/lint.sh --full airflow_dags/
```

## Available Metrics Summary

| Metric | Ruff | Pylint | Default Limit |
|--------|------|--------|---------------|
| **Cyclomatic complexity** | ✅ C90 | ✅ McCabe | 10 |
| **Lines per file** | ❌ | ✅ C0302 | 500 |
| **Classes per file** | ❌ | ✅ C9001 | 1 |
| **Function arguments** | ❌ | ✅ R0913 | 5 |
| **Local variables** | ❌ | ✅ R0914 | 15 |
| **Nested blocks** | ❌ | ✅ R1702 | 5 |
| **Class attributes** | ❌ | ✅ R0902 | 7 |
| **Return statements** | ❌ | ✅ R0911 | 6 |
| **Code duplication** | ❌ | ✅ R0801 | 4 lines |

## Recommended Workflow

### Daily Development
```bash
# Quick check while coding
ruff check airflow_dags/ --watch

# Fix auto-fixable issues
ruff check --fix .
```

### Before Commit
```bash
# Comprehensive check
pylint airflow_dags/

# If score < 8.0, review and fix issues
```

### Pre-commit Hook (Optional)
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running ruff..."
ruff check . || exit 1

echo "Running pylint on changed files..."
git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | xargs pylint || exit 1
```

## Adjusting Limits

### Increase Complexity Limit
**Ruff** (`pyproject.toml`):
```toml
[tool.ruff.lint.mccabe]
max-complexity = 15  # Increase from 10
```

**Pylint** (`.pylintrc`):
```ini
[EXTENSIONS]
max-complexity=15  # Increase from 10
```

### Increase Lines Per File
`.pylintrc`:
```ini
[FORMAT]
max-module-lines=800  # Increase from 500
```

### Allow Multiple Classes Per File
`.pylintrc`:
```ini
[MAIN]
max-classes-per-module=3  # Increase from 1
```

## Ignoring Specific Violations

### Inline Suppression
```python
# Ruff
# ruff: noqa: C901
def complex_function():  # Ignore complexity for this function
    pass

# Pylint
# pylint: disable=too-many-branches
def branchy_function():
    pass
# pylint: enable=too-many-branches
```

### File-level Suppression
```python
# Top of file
# ruff: noqa: C901
# pylint: disable=too-many-lines
```

## CI/CD Integration

```yaml
# .github/workflows/lint.yml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Ruff check
        run: ruff check .

      - name: Pylint check
        run: pylint airflow_dags/ --fail-under=8.0
```

## Troubleshooting

### "Module not found" for custom plugin
Ensure your PYTHONPATH includes the project root:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pylint airflow_dags/
```

### Pylint too slow
```bash
# Use parallel processing
pylint --jobs=4 airflow_dags/

# Check only changed files
git diff --name-only | grep '\.py$' | xargs pylint
```

### Conflicting rules between ruff and pylint
Pylint is configured to align with ruff. If conflicts occur, ruff takes precedence for style (it's faster and auto-fixes).

## References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pylint Documentation](https://pylint.readthedocs.io/)
- [McCabe Complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
