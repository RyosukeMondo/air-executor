#!/bin/bash
# Complete setup for autonomous fixing system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Setting up Autonomous Fixing System"
echo "========================================"
echo ""

# Step 1: Check Flutter
echo "📋 Step 1/5: Checking Flutter..."
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found"
    read -p "Install Flutter now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        bash "$SCRIPT_DIR/install_flutter.sh"
        echo "⚠️ Please add Flutter to PATH and restart terminal, then run this script again"
        exit 0
    else
        echo "⚠️ Skipping Flutter installation. Some features will not work."
    fi
else
    echo "✅ Flutter found: $(flutter --version | head -1)"
fi

# Step 2: Check Redis
echo ""
echo "📋 Step 2/5: Checking Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo "❌ Redis not found"
    read -p "Install Redis now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        bash "$SCRIPT_DIR/install_redis.sh"
    else
        echo "⚠️ Redis required for state management. Exiting."
        exit 1
    fi
else
    echo "✅ Redis found"
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️ Redis installed but not running. Starting..."
        sudo systemctl start redis || echo "❌ Could not start Redis"
    fi
fi

# Step 3: Install Python dependencies
echo ""
echo "📋 Step 3/5: Installing Python dependencies..."
bash "$SCRIPT_DIR/install_dependencies.sh"

# Step 4: Create configuration
echo ""
echo "📋 Step 4/5: Creating configuration..."
mkdir -p "$PROJECT_ROOT/config"

cat > "$PROJECT_ROOT/config/autonomous_fix.yaml" <<EOF
# Autonomous Fixing Configuration

# Target project
target_project:
  path: "$HOME/repos/money-making-app"
  type: "flutter"

# Completion criteria
completion_criteria:
  build_passes: true
  min_test_pass_rate: 0.95
  max_lint_errors: 0
  stability_runs: 3

# Circuit breaker
circuit_breaker:
  max_consecutive_failures: 5
  max_total_runs: 20
  max_duration_hours: 4

# Session management
session_mode: "separate"  # 'separate' | 'keep' | 'hybrid'

# Batch sizes
batch_sizes:
  build_fixes: 5
  test_fixes: 3
  lint_fixes: 10

# Air-executor settings
air_executor:
  wrapper_path: "$PROJECT_ROOT/claude_wrapper.py"
  timeout: 300
  auto_commit: true
  max_retries: 2

# Redis connection
redis:
  host: "localhost"
  port: 6379
  db: 0
EOF

echo "✅ Configuration created at config/autonomous_fix.yaml"

# Step 5: Create directories
echo ""
echo "📋 Step 5/5: Creating directories..."
mkdir -p "$PROJECT_ROOT/airflow_dags/autonomous_fixing"
mkdir -p "$PROJECT_ROOT/logs"

echo "✅ Directories created"

# Final summary
echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "📝 Next steps:"
echo "1. Review config: $PROJECT_ROOT/config/autonomous_fix.yaml"
echo "2. Start Redis: sudo systemctl start redis"
echo "3. Test health monitor: python airflow_dags/autonomous_fixing/health_monitor.py"
echo ""
echo "🔍 Verify setup:"
echo "   flutter doctor"
echo "   redis-cli ping"
echo "   python --version"
echo ""
