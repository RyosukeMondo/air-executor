# Autonomous Code Fixing System

Intelligent, context-efficient autonomous code fixing using air-executor + Airflow orchestration.

## 🎯 Overview

This system autonomously discovers and fixes issues in Flutter projects using:
- **Health Monitoring**: Continuous assessment of build/test/lint status
- **Issue Discovery**: Intelligent detection and prioritization of problems
- **State Management**: Redis-based task queue and session tracking
- **Air-Executor Integration**: Narrow-context Claude-powered fixing
- **Completion Detection**: Concrete criteria to stop when done

## 📊 Architecture

```
Health Monitor → Issue Discovery → Task Queue (Redis) → Air-Executor → Verify → Repeat
                                         ↓
                                  State Manager
                                  (session summaries, run history)
```

### Key Components

| Component | Purpose | File |
|-----------|---------|------|
| **Health Monitor** | Collect build/test/lint metrics | `health_monitor.py` |
| **State Manager** | Task queue + session state (Redis) | `state_manager.py` |
| **Issue Discovery** | Find and parse errors/failures | `issue_discovery.py` |
| **Executor Runner** | Run fixes via air-executor | `executor_runner.py` |
| **Orchestrator** | Coordinate entire cycle | `fix_orchestrator.py` |

## 🚀 Quick Start

### 1. Installation

```bash
# Run master setup script
cd /home/rmondo/repos/air-executor
./scripts/setup_autonomous_fixing.sh
```

This installs:
- Flutter SDK (~flutter/bin/flutter)
- Redis (systemctl start redis)
- Python deps (airflow, redis-py, anthropic)

### 2. Configuration

Edit `config/autonomous_fix.yaml`:

```yaml
target_project:
  path: "/path/to/your/flutter/project"

completion_criteria:
  build_passes: true
  min_test_pass_rate: 0.95
  max_lint_errors: 0
  stability_runs: 3

circuit_breaker:
  max_consecutive_failures: 5
  max_total_runs: 20

batch_sizes:
  build_fixes: 3  # Fix 3 build errors per run
  test_fixes: 2   # Fix 2 test failures per run
  lint_fixes: 5   # Fix 5 lint issues per run
```

### 3. Run in Simulation Mode (Test First!)

```bash
source ~/.venv/air-executor/bin/activate

python airflow_dags/autonomous_fixing/fix_orchestrator.py \
  config/autonomous_fix.yaml \
  --simulation \
  --max-iterations=5
```

**Output:**
```
🚀 Starting Autonomous Code Fixing Orchestrator
============================================================
Project: your-project
Mode: SIMULATION
============================================================

🔄 Run #1 - run_20251002_123456
🔍 Collecting health metrics...
📊 Health Report: 20% (Needs Attention)
  ❌ Build: fail (28218 errors)

📍 Phase: build
🔍 Discovering build issues...
  Found 3 build errors
📝 Queueing 3 tasks
🎭 SIMULATION: Would execute 3 tasks
...
```

### 4. Run Live Autonomous Fixing

**⚠️ WARNING: This will make real code changes and commits!**

```bash
# Clear previous state
python airflow_dags/autonomous_fixing/state_manager.py clear

# Run autonomous fixing (no --simulation flag)
python airflow_dags/autonomous_fixing/fix_orchestrator.py \
  config/autonomous_fix.yaml \
  --max-iterations=10
```

## 📝 Usage Examples

### Test Individual Components

```bash
# Activate virtual environment
source ~/.venv/air-executor/bin/activate

# 1. Health Monitor
python airflow_dags/autonomous_fixing/health_monitor.py \
  /path/to/project

# 2. Issue Discovery
python airflow_dags/autonomous_fixing/issue_discovery.py \
  /path/to/project \
  build  # or 'test', 'lint', 'all'

# 3. State Manager
python airflow_dags/autonomous_fixing/state_manager.py stats
python airflow_dags/autonomous_fixing/state_manager.py test
python airflow_dags/autonomous_fixing/state_manager.py clear
```

### Monitor Progress

```bash
# Check task queue
redis-cli
> ZRANGE autonomous_fix:task_queue 0 -1 WITHSCORES

# Check run history
> LRANGE autonomous_fix:run_history 0 9

# Check session summary
> GET autonomous_fix:summary:build

# View all keys
> KEYS autonomous_fix:*
```

### Configuration Options

**Completion Criteria:**
```yaml
completion_criteria:
  build_passes: true              # Build must pass
  min_test_pass_rate: 0.95        # 95% tests passing
  max_lint_errors: 0              # No lint errors
  stability_runs: 3               # Stable for 3 consecutive runs
```

**Circuit Breaker:**
```yaml
circuit_breaker:
  max_consecutive_failures: 5     # Stop after 5 failures in a row
  max_total_runs: 20              # Max 20 total iterations
  max_duration_hours: 4           # Stop after 4 hours
```

**Session Modes:**
- `separate`: Each task gets fresh session (efficient context)
- `keep`: Single long session (expensive but contextual)
- `hybrid`: Separate tasks + shared summaries (RECOMMENDED)

## 🔄 Workflow

1. **Health Check**: Collect current build/test/lint metrics
2. **Completion Check**: Exit if all criteria met
3. **Circuit Breaker**: Stop if too many failures or no progress
4. **Phase Selection**: Choose build → test → lint (priority order)
5. **Issue Discovery**: Find errors/failures in selected phase
6. **Task Queueing**: Add tasks to Redis priority queue
7. **Batch Execution**: Fix top N tasks via air-executor
8. **Session Summary**: Store what was fixed for next iteration
9. **Repeat**: Loop until completion or circuit breaker

## 📊 Monitoring & Observability

### Health Metrics

```python
from health_monitor import FlutterHealthMonitor

monitor = FlutterHealthMonitor("/path/to/project")
metrics = monitor.collect_metrics()

print(f"Build: {metrics.build_status}")
print(f"Tests: {metrics.test_passed}/{metrics.test_total}")
print(f"Analysis: {metrics.analysis_errors} errors")
print(f"Health: {metrics.health_score:.0%}")
```

### State Inspection

```python
from state_manager import StateManager

mgr = StateManager()

# Queue status
print(f"Queue size: {mgr.get_queue_size()}")

# Latest run
latest = mgr.get_latest_run()
print(f"Last run: {latest['run_id']}")
print(f"  Health: {latest['metrics']['health_score']}")

# Circuit breaker
failures = mgr.get_failure_count()
if mgr.is_circuit_open():
    print("⚠️ Circuit breaker OPEN")
```

## 🛠️ Context Management Strategy

**Hybrid Approach** (Best of both worlds):

**Per-Task Context** (Separate Session):
- Narrow, focused prompt
- Only relevant files
- Specific error/test case
- Fresh analysis per task

**Shared State** (Session Continuity):
- Session summaries in Redis
- Previous fixes inform next tasks
- Pattern learning across sessions
- Avoid re-analyzing same issues

**Example Prompt:**
```
Fix this Flutter build error:

File: lib/main.dart:42
Error: Undefined name 'foo'

Code Context:
  → 42 | print(foo);  // Error here

Previous session: Fixed 5 of 10 issues

Instructions:
1. Analyze error
2. Fix ONLY this specific error
3. Verify with flutter analyze
4. Commit: "fix: Undefined name 'foo'"
```

## 🎯 Completion Detection

System stops when ALL criteria met:

✅ **Build passes** (`flutter analyze` clean)
✅ **Tests ≥95% pass rate**
✅ **0 lint errors**
✅ **3 consecutive stable runs** (same healthy metrics)

**OR** Circuit breaker triggers:

❌ **5 consecutive failures**
❌ **20 total runs**
❌ **4 hour duration**
❌ **No progress in 5 runs**

## 🔧 Troubleshooting

### Issue: Flutter not found
```bash
# Ensure Flutter in PATH
export PATH="$HOME/flutter/bin:$PATH"
source ~/.bashrc

# Verify
flutter --version
```

### Issue: Redis not running
```bash
# Check status
systemctl status redis

# Start Redis
sudo systemctl start redis

# Test connection
redis-cli ping  # Should return PONG
```

### Issue: Tasks not executing
```bash
# Check queue
redis-cli ZRANGE autonomous_fix:task_queue 0 -1

# Clear and retry
python airflow_dags/autonomous_fixing/state_manager.py clear
```

### Issue: No progress detected
- Check if errors are actually fixable
- Reduce batch size (fewer tasks per run)
- Increase timeout (more time per task)
- Review air-executor logs

## 📈 Performance Optimization

### Context Efficiency

| Strategy | Context Size | API Cost | Accuracy |
|----------|-------------|----------|----------|
| Full codebase | ~100K tokens | 💰💰💰 | 🎯🎯🎯 |
| **Hybrid (recommended)** | ~5K tokens | 💰 | 🎯🎯🎯 |
| File-only | ~2K tokens | 💰 | 🎯🎯 |

### Batch Size Tuning

```yaml
# Conservative (slow but safe)
batch_sizes:
  build_fixes: 1
  test_fixes: 1
  lint_fixes: 3

# Aggressive (fast but risky)
batch_sizes:
  build_fixes: 10
  test_fixes: 5
  lint_fixes: 20

# Balanced (recommended)
batch_sizes:
  build_fixes: 3
  test_fixes: 2
  lint_fixes: 5
```

## 🔐 Safety Features

1. **Simulation Mode**: Test without making changes
2. **Auto-commit**: Each fix is committed separately (easy rollback)
3. **Circuit Breaker**: Stops if things go wrong
4. **Task Retries**: Failed tasks requeued with lower priority (max 3 attempts)
5. **Narrow Context**: Only sees relevant code (reduces risk)

## 📋 TODO

- [ ] Add Airflow DAG wrappers
- [ ] Web dashboard for monitoring
- [ ] Prometheus metrics export
- [ ] Multi-project support
- [ ] Pattern learning database
- [ ] Rollback on regression detection

## 🤝 Contributing

See architecture doc: `/home/rmondo/repos/air-executor/docs/AUTONOMOUS_FIXING_ARCHITECTURE.md`

## 📄 License

[Your License]
