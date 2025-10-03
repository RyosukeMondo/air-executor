# Autonomous Fixing - Quick Start

**KISS principle**: Simple commands that always work, no Python/venv hassle.

## Prerequisites

```bash
# Install development tools (one-time setup)
./scripts/setup_python.sh      # Python tools
./scripts/setup_javascript.sh  # JavaScript/TypeScript tools
./scripts/setup_go.sh           # Go tools (including SDK)
./scripts/setup_flutter.sh      # Flutter SDK

# Verify installation
./scripts/check_tools.sh
```

## Run Autonomous Fixing

### Quick Start (any project)
```bash
# Run any project config - handles Python environment automatically
./scripts/run_autonomous_fix.sh config/projects/money-making-app.yaml

# Or run in background
./scripts/run_autonomous_fix.sh config/projects/air-executor.yaml --background
```

### Available Projects
```bash
# Flutter app
./scripts/run_autonomous_fix.sh config/projects/money-making-app.yaml

# Python projects
./scripts/run_autonomous_fix.sh config/projects/air-executor.yaml

# JavaScript/TypeScript projects
./scripts/run_autonomous_fix.sh config/projects/cc-task-manager.yaml
./scripts/run_autonomous_fix.sh config/projects/mind-training.yaml
./scripts/run_autonomous_fix.sh config/projects/warps.yaml
```

### Options
```bash
# Run in background
./scripts/run_autonomous_fix.sh <config> --background

# Custom log file
./scripts/run_autonomous_fix.sh <config> --log my_run.log

# Check tools only (no execution)
./scripts/run_autonomous_fix.sh <config> --check-tools
```

## Monitor Progress

### While Running
```bash
# Watch main output
tail -f logs/orchestrator_run.log

# Watch debug logs (structured JSON)
tail -f logs/debug/multi-project_*.jsonl

# Check process status
ps aux | grep multi_language_orchestrator
```

### After Completion
```bash
# Check results
cat logs/orchestrator_run.log

# View debug timeline
cat logs/debug/multi-project_<timestamp>.jsonl | jq .
```

## Tool Validation

```bash
# Check all tools
./scripts/check_tools.sh

# Check specific language
./scripts/check_tools.sh --check-flutter

# Full validation with config
./scripts/run_autonomous_fix.sh <config> --check-tools
```

## How It Works

### Automatic Python Environment Detection

The wrapper scripts automatically find and use Python in this order:

1. ✅ Project venv (`.venv/bin/python`)
2. ✅ Config venv (`.venv/air-executor/bin/python`)
3. ✅ System python3
4. ⚠️  System python (fallback)

**No manual PYTHONPATH or venv activation needed!**

### Execution Flow

```
1. Tool Validation → Check all required tools exist
2. Test Discovery  → Claude discovers test configuration
3. Phase Loop:
   ├─ P1: Static Analysis → Linting, type checking
   │  ├─ Score < threshold? → Fix issues → Repeat
   │  └─ Score >= threshold? → Continue
   ├─ P2: Tests → Run test suite
   │  ├─ Failures? → Fix tests → Repeat
   │  └─ Pass? → Success!
   └─ Max iterations reached → Stop
```

## Troubleshooting

### Python not found
```bash
# Install Python
sudo apt install python3 python3-pip

# Or create venv
python3 -m venv .venv
source .venv/bin/activate
./scripts/setup_python.sh
```

### Tools missing
```bash
# Check what's missing
./scripts/check_tools.sh

# Install missing tools
./scripts/setup_python.sh
./scripts/setup_javascript.sh
./scripts/setup_go.sh
./scripts/setup_flutter.sh
```

### Process hangs
```bash
# Check if actually running (takes time for real analysis)
ps aux | grep multi_language_orchestrator

# Check debug logs for progress
tail -f logs/debug/multi-project_*.jsonl

# Typical phase durations:
# - Test discovery: 5-10s
# - Static analysis: 30-120s
# - Test execution: 60-300s
# - Fix iteration: 30-60s
```

### Permission errors
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Check file permissions
ls -l scripts/
```

## Advanced Usage

### Background Execution
```bash
# Start in background
./scripts/run_autonomous_fix.sh config/projects/money-making-app.yaml --background

# Monitor
tail -f logs/orchestrator_run.log

# Stop
kill <PID>  # PID shown when starting
```

### Custom Configurations
```bash
# Edit project config
vim config/projects/money-making-app.yaml

# Key settings:
# - max_iterations: How many fix cycles
# - success_threshold: Score required to pass
# - test_timeout: Max time for tests
# - auto_commit: Git commit fixes automatically
```

### Debug Logging
```bash
# Enable debug in config
logging:
  level: "DEBUG"  # or "INFO", "WARNING", "ERROR"
  file: "logs/fix-money-making-app.log"

# Structured debug logs (JSON)
cat logs/debug/multi-project_*.jsonl | jq .

# Filter specific events
cat logs/debug/*.jsonl | jq 'select(.event == "wrapper_call")'
```

## Files and Directories

```
scripts/
├── run_autonomous_fix.sh      # Main wrapper (use this!)
├── check_tools.sh              # Quick tool validation
├── setup_python.sh             # Install Python tools
├── setup_javascript.sh         # Install JS/TS tools
├── setup_go.sh                 # Install Go tools
├── setup_flutter.sh            # Install Flutter SDK
└── SETUP_TOOLS.md              # Detailed setup guide

config/projects/                # Project configurations
├── money-making-app.yaml       # Flutter app
├── air-executor.yaml           # Python project
├── cc-task-manager.yaml        # JavaScript project
└── ...

logs/
├── orchestrator_run.log        # Main output
├── debug/                      # Structured JSON logs
└── fix-<project>-*.log         # Project-specific logs
```

## Best Practices

### Before Running
1. Check tools: `./scripts/check_tools.sh`
2. Review config: `cat config/projects/<project>.yaml`
3. Check git status: `cd <project> && git status`
4. Create feature branch: `git checkout -b fix/autonomous-improvements`

### While Running
1. Monitor logs: `tail -f logs/orchestrator_run.log`
2. Watch debug events: `tail -f logs/debug/*.jsonl`
3. Be patient - real analysis takes time!

### After Running
1. Review changes: `cd <project> && git diff`
2. Check commits: `git log -3 --oneline`
3. Run tests manually: Verify fixes work
4. Review debug timeline: `cat logs/debug/*.jsonl | jq .`

## Need Help?

```bash
# Show script usage
./scripts/run_autonomous_fix.sh

# Show tool check options
./scripts/check_tools.sh --help

# Read detailed setup
cat scripts/SETUP_TOOLS.md

# Check debug logs
cat logs/debug/multi-project_*.jsonl | jq .
```

## Quick Command Reference

```bash
# Setup (once)
./scripts/setup_python.sh && ./scripts/check_tools.sh

# Run (simple)
./scripts/run_autonomous_fix.sh config/projects/money-making-app.yaml

# Run (background)
./scripts/run_autonomous_fix.sh config/projects/air-executor.yaml --background

# Monitor
tail -f logs/orchestrator_run.log

# Check tools
./scripts/check_tools.sh

# Debug
cat logs/debug/*.jsonl | jq .
```

**That's it! No PYTHONPATH, no venv activation, just run the script.**
