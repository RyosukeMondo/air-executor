#!/bin/bash
# Setup script for Air-Executor development environment

set -e  # Exit on error

echo "🚀 Setting up Air-Executor development environment..."

# Check Python version
echo ""
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "❌ Error: Python 3.11+ required (found: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo ""
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install package in editable mode with dev dependencies
echo ""
echo "📥 Installing air-executor with dev dependencies..."
pip install -e ".[dev]"

# Create .air-executor directory
echo ""
echo "📁 Creating .air-executor directory..."
mkdir -p .air-executor/jobs
mkdir -p .air-executor/logs

# Create default config
if [ ! -f ".air-executor/config.yaml" ]; then
    echo ""
    echo "⚙️  Creating default config.yaml..."
    cat > .air-executor/config.yaml << EOF
# Air-Executor Configuration
# Polling interval in seconds (1-60)
poll_interval: 5

# Task timeout in seconds (60-7200)
task_timeout: 1800

# Maximum concurrent runners (1-50)
max_concurrent_runners: 10

# Base directory for storage
base_path: .air-executor

# Logging settings
log_level: INFO
log_format: json
EOF
    echo "✅ Default config created at .air-executor/config.yaml"
else
    echo "✅ Config already exists at .air-executor/config.yaml"
fi

# Run tests to verify installation
echo ""
echo "🧪 Running tests to verify installation..."
if pytest tests/ -v --tb=short; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "⚠️  Some tests failed, but installation is complete"
fi

# Create example job for testing
echo ""
echo "📝 Creating example test job..."
mkdir -p .air-executor/jobs/test-job

cat > .air-executor/jobs/test-job/state.json << EOF
{
  "id": "$(uuidgen)",
  "name": "test-job",
  "state": "waiting",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
}
EOF

cat > .air-executor/jobs/test-job/tasks.json << EOF
[
  {
    "id": "task-001",
    "job_name": "test-job",
    "command": "echo",
    "args": ["Hello from Air-Executor!"],
    "dependencies": [],
    "status": "pending",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "started_at": null,
    "completed_at": null,
    "error": null
  },
  {
    "id": "task-002",
    "job_name": "test-job",
    "command": "sleep",
    "args": ["2"],
    "dependencies": ["task-001"],
    "status": "pending",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "started_at": null,
    "completed_at": null,
    "error": null
  },
  {
    "id": "task-003",
    "job_name": "test-job",
    "command": "echo",
    "args": ["All tasks completed!"],
    "dependencies": ["task-002"],
    "status": "pending",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "started_at": null,
    "completed_at": null,
    "error": null
  }
]
EOF

mkdir -p .air-executor/jobs/test-job/logs

echo "✅ Example test job created"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Quick Start:"
echo ""
echo "  1. Start development server:"
echo "     ./start-dev.sh"
echo ""
echo "  2. Check status in another terminal:"
echo "     source venv/bin/activate"
echo "     air-executor status"
echo ""
echo "  3. View logs:"
echo "     air-executor logs --job test-job"
echo ""
echo "  4. Stop server:"
echo "     ./stop-dev.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
