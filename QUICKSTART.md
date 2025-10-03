# Quick Start Guide

**KISS Principle**: Simple commands that work. No Python/venv hassle.

## Prerequisites

```bash
# One-time setup - install development tools
./scripts/setup_python.sh      # Python tools
./scripts/setup_javascript.sh  # JavaScript/TypeScript tools
./scripts/setup_go.sh           # Go tools (including SDK)
./scripts/setup_flutter.sh      # Flutter SDK

# Verify installation
./scripts/check_tools.sh
```

## Quick Run

### Single Project

```bash
# Run any project - handles Python environment automatically
./scripts/run_autonomous_fix.sh config/projects/money-making-app.yaml

# Or run in background
./scripts/run_autonomous_fix.sh config/projects/air-executor.yaml --background
```

### All Projects (PM2)

```bash
# Start all projects
pm2 start config/pm2.config.js

# Start specific project
pm2 start config/pm2.config.js --only fix-air-executor

# Monitor logs
pm2 logs
pm2 logs fix-money-making-app

# Check status
pm2 status
```

## Available Projects

| Project | Language | Config |
|---------|----------|--------|
| **air-executor** | Python | `config/projects/air-executor.yaml` |
| **cc-task-manager** | JavaScript | `config/projects/cc-task-manager.yaml` |
| **mind-training** | JavaScript | `config/projects/mind-training.yaml` |
| **money-making-app** | Flutter | `config/projects/money-making-app.yaml` |
| **warps** | TypeScript | `config/projects/warps.yaml` |

## Options

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

# Review commits
git log --oneline -5
```

## How It Works

### Automatic Python Environment Detection

Wrapper scripts automatically find Python in this order:
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
# Check if actually running (real analysis takes time)
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

config/
├── pm2.config.js               # PM2 process management
└── projects/                   # Project configurations
    ├── money-making-app.yaml   # Flutter app
    ├── air-executor.yaml       # Python project
    └── cc-task-manager.yaml    # JavaScript project

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

## Safety Features

✅ **All changes are commits** - Easy to review
✅ **No auto-push** - You push when ready
✅ **Git status check** - Warns about uncommitted changes
✅ **Rollback anytime** - `git reset --hard HEAD~N`
✅ **Stops on time limit** - Won't run forever

## Quick Command Reference

```bash
# Setup (once)
./scripts/setup_python.sh && ./scripts/check_tools.sh

# Run single project
./scripts/run_autonomous_fix.sh config/projects/money-making-app.yaml

# Run all projects with PM2
pm2 start config/pm2.config.js
pm2 logs

# Monitor
tail -f logs/orchestrator_run.log

# Check tools
./scripts/check_tools.sh

# Debug
cat logs/debug/*.jsonl | jq .

# Stop PM2 processes
pm2 stop all
pm2 delete all
```

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

**That's it! No PYTHONPATH, no venv activation, just run the script.**

---

For detailed documentation, see `docs/` directory.
