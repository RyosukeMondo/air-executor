#!/bin/bash
# Setup Python development tools for autonomous fixing
# Based on config/projects/air-executor.yaml

set -e

echo "=================================="
echo "Python Tools Setup"
echo "=================================="
echo ""

# Check for virtual environment
VENV_DIR=".venv"
if [ -d "$VENV_DIR" ]; then
    echo "✅ Found virtual environment at $VENV_DIR"
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    USE_VENV=true
    echo ""
elif [ "$1" = "--sudo" ]; then
    USE_SUDO="sudo"
    USE_VENV=false
    echo "⚠️  Running with sudo for system-wide installation"
    echo ""
else
    echo "⚠️  No virtual environment found and externally-managed Python detected"
    echo ""
    echo "Options:"
    echo "  1. Create virtual environment (recommended):"
    echo "     python3 -m venv .venv"
    echo "     source .venv/bin/activate"
    echo "     ./scripts/setup_python.sh"
    echo ""
    echo "  2. Install system-wide (requires sudo):"
    echo "     ./scripts/setup_python.sh --sudo"
    echo ""
    exit 1
fi

# Check Python version
echo "1. Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python first:"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "   macOS: brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Found: $PYTHON_VERSION"
echo ""

# Install linters (from config: ["pylint", "mypy"])
echo "2. Installing linters..."
echo "   - pylint (code quality)"
echo "   - mypy (type checking)"

if [ "$USE_VENV" = true ]; then
    pip install pylint mypy
elif [ -n "$USE_SUDO" ]; then
    $USE_SUDO pip3 install pylint mypy
else
    pip3 install --user pylint mypy
fi

echo "✅ Linters installed"
echo ""

# Install test framework (from config: "pytest")
echo "3. Installing test framework..."
echo "   - pytest"

if [ "$USE_VENV" = true ]; then
    pip install pytest pytest-cov
elif [ -n "$USE_SUDO" ]; then
    $USE_SUDO pip3 install pytest pytest-cov
else
    pip3 install --user pytest pytest-cov
fi

echo "✅ Test framework installed"
echo ""

# Optional: Install additional useful tools
echo "4. Installing optional tools..."
echo "   - coverage (code coverage analysis)"
echo "   - radon (complexity metrics)"

if [ "$USE_VENV" = true ]; then
    pip install coverage radon
elif [ -n "$USE_SUDO" ]; then
    $USE_SUDO pip3 install coverage radon
else
    pip3 install --user coverage radon
fi

echo "✅ Optional tools installed"
echo ""

# Verify installation
echo "=================================="
echo "Verification"
echo "=================================="
echo ""

echo "Checking installed versions..."
python3 --version
pylint --version 2>&1 | head -1
mypy --version
pytest --version
coverage --version 2>&1 | head -1
radon --version 2>&1 | head -1

echo ""
echo "✅ Python toolchain setup complete!"
echo ""
echo "Tools installed:"
echo "  - pylint     (linter)"
echo "  - mypy       (type checker)"
echo "  - pytest     (test runner)"
echo "  - coverage   (coverage analysis)"
echo "  - radon      (complexity metrics)"
echo ""
echo "You can now run: python3 airflow_dags/autonomous_fixing/core/tool_validator.py --check-all"
