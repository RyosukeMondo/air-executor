# Autonomous Fixing - Quick Start Guide

Complete guide for running autonomous fixing on your projects.

## 🚀 Quick Start

### For money-making-app (Flutter)

```bash
# One command - handles everything
./scripts/autonomous_fix.sh config/money-making-app.yaml
```

This will:
1. ✓ Check and start Redis if needed
2. ✓ Validate Python environment
3. ✓ Check dependencies (yaml, redis packages)
4. ✓ Validate Flutter toolchain
5. ✓ Run the orchestrator

## 📁 Project Structure

```
air-executor/
├── config/
│   ├── money-making-app.yaml          # Flutter app configuration
│   └── sample_config.yaml             # Python project example
│
├── scripts/
│   ├── autonomous_fix.sh              # ⭐ MAIN - Simple entry point
│   ├── autonomous_fix_with_redis.sh   # Full startup (Redis + validation)
│   ├── autonomous_fix_advanced.sh     # Advanced options
│   ├── install_redis.sh               # Redis installation
│   ├── install_flutter.sh             # Flutter installation
│   └── check_tools.sh                 # Tool validation
│
└── run_orchestrator.py                # Python orchestrator
```

## 📝 Configuration Files

### Location
All configs go in `config/` directory:

```bash
config/
├── money-making-app.yaml   # Your Flutter project
├── air-executor.yaml       # Python project example
└── custom-project.yaml     # Add your own
```

### Configuration Template

```yaml
# Minimal config
target_project: "/path/to/your/project"

projects:
  - path: "/path/to/your/project"
    language: "flutter"  # or "python", "javascript", "go"
    enabled: true

languages:
  enabled: ["flutter"]

  flutter:
    analyze_command: "flutter analyze --no-pub"
    test_command: "flutter test"
    complexity_threshold: 15

priorities:
  p1_static:
    enabled: true
    max_duration_seconds: 300

  p2_tests:
    enabled: true
    adaptive_strategy: true

execution:
  max_iterations: 3

state_manager:
  redis_host: "localhost"
  redis_port: 6379

git:
  auto_commit: true
  commit_prefix: "fix"
```

See `config/money-making-app.yaml` for full example with all options.

## 🔧 Prerequisites

### Required
- **Python 3.8+** with virtual environment (`.venv/`)
- **Redis** for state management

### Language-Specific
- **Flutter**: `flutter` command (for Flutter projects)
- **Python**: `pylint`, `pytest` (for Python projects)
- **JavaScript**: `eslint`, `jest` (for JS projects)
- **Go**: `go`, `staticcheck` (for Go projects)

### Installation Scripts

```bash
# Install Redis
./scripts/install_redis.sh

# Install Flutter
./scripts/install_flutter.sh

# Check all tools
./scripts/check_tools.sh
```

## 🎯 Usage Examples

### 1. Flutter Project (money-making-app)

```bash
./scripts/autonomous_fix.sh config/money-making-app.yaml
```

### 2. Python Project (air-executor)

```bash
# Create config first
cat > config/air-executor.yaml <<EOF
target_project: "/home/rmondo/repos/air-executor"
projects:
  - path: "/home/rmondo/repos/air-executor"
    language: "python"
    enabled: true
languages:
  enabled: ["python"]
  python:
    linters: ["pylint"]
    test_framework: "pytest"
priorities:
  p1_static:
    enabled: true
state_manager:
  redis_host: "localhost"
  redis_port: 6379
git:
  auto_commit: false
EOF

# Run it
./scripts/autonomous_fix.sh config/air-executor.yaml
```

### 3. Custom Project

```bash
# 1. Copy template
cp config/money-making-app.yaml config/my-project.yaml

# 2. Edit config
vim config/my-project.yaml
# Update: target_project, projects[0].path, languages

# 3. Run
./scripts/autonomous_fix.sh config/my-project.yaml
```

## 🔍 Monitoring

### Logs
```bash
# Main log
tail -f logs/money-making-app.log

# Debug log (detailed)
tail -f logs/debug/money-making-app_debug.jsonl

# Orchestrator log
tail -f logs/orchestrator_run.log
```

### Redis State
```bash
# Check Redis connection
redis-cli ping

# View state keys
redis-cli keys "money_making_app:*"

# Get specific state
redis-cli get "money_making_app:session:current"
```

### Health Metrics
The orchestrator tracks:
- **Static Analysis Score**: Lint/analysis results
- **Test Pass Rate**: Unit test success
- **Coverage**: Code coverage percentage
- **Overall Health**: Combined score

## 🛠️ Troubleshooting

### Redis Not Running
```bash
# Start Redis
redis-server --daemonize yes

# Or use system service
sudo systemctl start redis
```

### Python Environment Issues
```bash
# Ensure venv exists
python3 -m venv .venv

# Install dependencies
.venv/bin/pip install pyyaml redis

# The script will auto-detect .venv/bin/python3
```

### Flutter Not Found
```bash
# Install Flutter
./scripts/install_flutter.sh

# Or manually
git clone https://github.com/flutter/flutter.git ~/flutter
export PATH="$PATH:$HOME/flutter/bin"
```

### Import Errors
```bash
# Make sure PYTHONPATH is set (script does this automatically)
export PYTHONPATH="/home/rmondo/repos/air-executor"

# Test imports
.venv/bin/python3 -c "from airflow_dags.autonomous_fixing.multi_language_orchestrator import MultiLanguageOrchestrator"
```

## 📊 Architecture

### Execution Flow

```
autonomous_fix.sh
    ↓
autonomous_fix_with_redis.sh
    ↓ [1] Check Redis → Start if needed
    ↓ [2] Detect Python (.venv/bin/python3)
    ↓ [3] Validate dependencies (yaml, redis)
    ↓ [4] Validate language tools (flutter, pylint, etc)
    ↓ [5] Run orchestrator
    ↓
run_orchestrator.py
    ↓ Load config
    ↓ Create MultiLanguageOrchestrator
    ↓
MultiLanguageOrchestrator
    ↓ Initialize adapters (PythonAdapter, FlutterAdapter, etc)
    ↓ Create analyzer, fixer, scorer, iteration_engine
    ↓ Validate tools (pre-flight)
    ↓ Get projects from config
    ↓ Run iteration_engine.run_improvement_loop()
    ↓
IterationEngine
    ↓ Loop: analyze → fix → verify → score
    ↓ Until: max_iterations OR health_threshold
    ↓ Return: results
```

### Components

- **Domain Layer** (`domain/`): Models, interfaces (SSOT)
- **Adapters** (`adapters/`): Language adapters, state, AI, git
- **Core** (`core/`): Analyzer, fixer, scorer, iteration engine
- **Orchestrator**: Thin coordinator (delegates to core)

## 🎓 Best Practices

### 1. Start Small
```bash
# First run: Just static analysis
priorities:
  p1_static: {enabled: true}
  p2_tests: {enabled: false}
  p3_coverage: {enabled: false}
  p4_e2e: {enabled: false}
```

### 2. Use Git Safety
```bash
# Disable auto-commit for first run
git:
  auto_commit: false

# Review changes manually
git diff
git status
```

### 3. Set Reasonable Limits
```bash
execution:
  max_iterations: 3  # Don't run forever

circuit_breaker:
  max_consecutive_failures: 5
  max_duration_hours: 2
```

### 4. Monitor Progress
```bash
# In one terminal: run orchestrator
./scripts/run_autonomous_fix.sh config/my-project.yaml

# In another: watch logs
tail -f logs/orchestrator_run.log
```

## 📚 Advanced Usage

### Background Execution
```bash
# Run in background
./scripts/autonomous_fix_advanced.sh config/money-making-app.yaml --background

# Monitor
tail -f logs/orchestrator_run.log
```

### Tool Validation Only
```bash
./scripts/autonomous_fix_advanced.sh config/my-project.yaml --check-tools
```

### Custom Log File
```bash
./scripts/autonomous_fix_advanced.sh config/my-project.yaml --log custom.log
```

## 🔗 Related Documentation

- `scripts/README_AUTONOMOUS_FIXING.md` - Original autonomous fixing docs
- `scripts/SETUP_TOOLS.md` - Tool installation guide
- `claudedocs/refactoring-final-complete.md` - Architecture details

## 💡 Tips

1. **Redis is required** - The orchestrator uses Redis for state management
2. **Virtual environment** - Always use `.venv/bin/python3` (script detects automatically)
3. **Config location** - Put configs in `config/` directory for organization
4. **Logs** - Check `logs/` for detailed output and debugging
5. **Iterations** - Start with `max_iterations: 1-3` for testing

## 🆘 Getting Help

If issues persist:
1. Check logs: `logs/orchestrator_run.log`
2. Validate tools: `./scripts/check_tools.sh`
3. Test Redis: `redis-cli ping`
4. Check Python imports: `.venv/bin/python3 -c "import yaml, redis"`
5. Review config: Ensure paths and settings are correct

---

**Generated**: 2025-10-03
**Version**: 2.0 (Refactored Architecture)
