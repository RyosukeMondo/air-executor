#!/bin/bash
# Install Python dependencies for autonomous fixing system

set -e

echo "🔧 Installing Python dependencies..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment if needed
VENV_DIR="$HOME/.venv/air-executor"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install core dependencies
echo "📦 Installing core dependencies..."
pip install \
    redis \
    apache-airflow \
    anthropic \
    pyyaml \
    python-dotenv

# Install optional monitoring dependencies
echo "📦 Installing monitoring dependencies..."
pip install \
    prometheus-client \
    psutil

# Install testing dependencies
echo "📦 Installing testing dependencies..."
pip install \
    pytest \
    pytest-json-report

echo ""
echo "✅ All dependencies installed!"
echo ""
echo "📝 Activate virtual environment with:"
echo "    source $VENV_DIR/bin/activate"
echo ""
echo "Installed packages:"
pip list | grep -E "(redis|airflow|anthropic|prometheus)"
