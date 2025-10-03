# Airflow DAGs - Complete Guide

Comprehensive guide for all Airflow DAG integration with Air Executor.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Available DAGs](#available-dags)
- [Deployment Methods](#deployment-methods)
- [Autonomous Fixing with Airflow](#autonomous-fixing-with-airflow)
- [Development Workflow](#development-workflow)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

This directory contains Airflow DAG definitions for:
1. **Basic Integration** - Air-Executor job execution via Airflow
2. **Hybrid Control** - Airflow orchestration + Air-Executor dynamic discovery
3. **Autonomous Fixing** - Real-time web monitoring of autonomous code fixing

### Directory Structure

```
airflow_dags/
├── README.md                          # This file (SSOT for all Airflow DAGs)
│
├── air_executor_integration.py        # Basic Air-Executor integration
├── hybrid_control_example.py          # Hybrid control flow pattern
├── autonomous_fixing_dag.py           # Autonomous fixing with web UI
│
├── autonomous_fixing/                 # Autonomous fixing system
│   ├── fix_orchestrator.py            # Main orchestration logic
│   ├── health_monitor.py              # Health metrics collection
│   ├── issue_discovery.py             # Issue detection and parsing
│   ├── state_manager.py               # Redis state management
│   ├── executor_runner.py             # Air-executor task execution
│   ├── issue_grouping.py              # Intelligent task batching
│   ├── enhanced_health_monitor.py     # Enhanced metrics with coverage
│   ├── test_metrics.py                # Test breakdown analysis
│   ├── code_metrics.py                # Code quality metrics
│   └── multi_language_orchestrator.py # Multi-language support
│
└── [DEPRECATED - See consolidation note]
    ├── README_AIRFLOW_INTEGRATION.md  → This README
    └── autonomous_fixing/
        ├── README.md                  → This README
        ├── README_BATCH_FIXING.md     → This README (Batching section)
        └── README_BATCHING_MODES.md   → This README (Batching section)
```

## Quick Start

### Prerequisites

```bash
# 1. Install and start Airflow
pip install apache-airflow==2.10.4
airflow db init
airflow users create --username admin --password admin --role Admin

# 2. Start Airflow services
airflow webserver -p 8080 &
airflow scheduler &

# 3. For autonomous fixing: Install Redis
redis-server &
redis-cli ping  # Should return PONG
```

### Deploy DAGs

```bash
# Sync DAGs to Airflow (auto-discovery, validation, cleanup)
./scripts/sync_dags_to_airflow.sh --auto-unpause

# Or for development (symlinks)
./scripts/sync_dags_to_airflow.sh --symlink --auto-unpause

# Verify DAGs appeared
airflow dags list | grep -E 'air_executor|autonomous'
```

### Access Airflow UI

```bash
# Open browser
open http://localhost:8080

# Login with credentials created above
# (or check ~/airflow/simple_auth_manager_passwords.json.generated)
```

## Available DAGs

### 1. air_executor_demo

**File**: `air_executor_integration.py`

**Purpose**: Basic integration showing Air-Executor job creation and monitoring

**Features**:
- Create Air-Executor jobs from Airflow
- PythonSensor for monitoring job completion
- XCom for passing data between tasks

**Trigger**:
```bash
airflow dags trigger air_executor_demo
```

**Use Case**: Simple job execution, learning the integration pattern

### 2. hybrid_control_flow

**File**: `hybrid_control_example.py`

**Purpose**: Advanced pattern showing Airflow orchestration + Air-Executor dynamic discovery

**Features**:
- Airflow preparation phase
- Handoff to Air-Executor for dynamic work
- Air-Executor discovers and queues tasks dynamically
- Control returns to Airflow for post-processing

**Trigger**:
```bash
airflow dags trigger hybrid_control_flow
```

**Use Case**: Complex workflows where task structure isn't known upfront

### 3. autonomous_fixing

**File**: `autonomous_fixing_dag.py`

**Purpose**: Web UI monitoring for autonomous code fixing with streaming output

**Features**:
- ✅ Real-time streaming Claude output
- ✅ Monitor health checks in browser
- ✅ Watch commit messages as created
- ✅ Track progress through iterations
- ✅ Accessible from anywhere on network
- ✅ Full execution history

**Trigger via UI**:
1. Go to http://localhost:8080
2. Find "autonomous_fixing" DAG
3. Click "Trigger DAG w/ config"
4. Enter parameters (JSON):
```json
{
  "max_iterations": 10,
  "target_project": "/path/to/project",
  "simulation": false
}
```

**Trigger via CLI**:
```bash
airflow dags trigger autonomous_fixing \
  --conf '{"max_iterations": 10, "simulation": false}'
```

**Use Case**: Interactive monitoring of autonomous fixing, debugging, development

## Deployment Methods

### Method 1: Copy (Production-Safe)

```bash
# Copies files to Airflow DAGs folder
./scripts/sync_dags_to_airflow.sh --copy

# Changes require re-sync
# Good for production, stable deployments
```

**Pros**: Isolated from source changes, predictable
**Cons**: Manual sync needed after changes

### Method 2: Symlink (Development)

```bash
# Creates symlinks (changes auto-sync)
./scripts/sync_dags_to_airflow.sh --symlink

# File changes immediately visible to Airflow
# Good for development, iteration
```

**Pros**: Auto-sync, fast iteration
**Cons**: Accidental changes affect Airflow

### Method 3: Git-Sync (Production with CI/CD)

```yaml
# In Airflow deployment (Kubernetes example)
dags:
  gitSync:
    enabled: true
    repo: https://github.com/RyosukeMondo/air-executor.git
    branch: main
    subPath: airflow_dags
    wait: 60
```

**Pros**: Automated, version controlled, scalable
**Cons**: Requires CI/CD setup

### Sync Script Features

The unified sync script (`scripts/sync_dags_to_airflow.sh`) provides:

**Auto-Discovery**: Finds all `.py` files automatically (no hardcoded lists)
**Validation**: Syntax and import checks before deployment
**Stale Detection**: Identifies DAGs referencing deleted files
**Auto-Cleanup**: Removes stale DAG metadata with `--cleanup`
**Auto-Unpause**: Activates new DAGs with `--auto-unpause`
**Dry Run**: Preview changes with `--dry-run`

```bash
# Full sync with cleanup and unpause (recommended)
./scripts/sync_dags_to_airflow.sh --cleanup --auto-unpause

# Development mode
./scripts/sync_dags_to_airflow.sh --symlink --auto-unpause

# See what would happen
./scripts/sync_dags_to_airflow.sh --dry-run
```

## Autonomous Fixing with Airflow

### Why Use Airflow for Autonomous Fixing?

| Feature | PM2 | Airflow |
|---------|-----|---------|
| **Interface** | Terminal | Web Browser |
| **Accessibility** | SSH required | Network accessible |
| **Real-Time Output** | `pm2 logs` | Streaming in browser |
| **History** | Log files only | Full UI history with graphs |
| **Parameters** | Command line args | JSON config per run |
| **Monitoring** | Terminal command | Visual dashboard |
| **Best For** | Server automation | Interactive development |

**Use PM2 when**: Running headless on server, automation scripts, CI/CD

**Use Airflow when**: Interactive monitoring, debugging, team collaboration

### Running Autonomous Fixing

**Step 1: Sync DAG**
```bash
./scripts/sync_dags_to_airflow.sh --auto-unpause
```

**Step 2: Access Web UI**
```bash
open http://localhost:8080
```

**Step 3: Trigger with Parameters**
```json
{
  "max_iterations": 10,
  "target_project": "/home/rmondo/repos/money-making-app",
  "simulation": false
}
```

**Step 4: Monitor Streaming Logs**
- Click on running task
- Click "Logs" tab
- See real-time output:
  - Health check results
  - Issues being discovered
  - Claude's reasoning and fixes
  - Commit messages
  - Progress through iterations

### What You'll See in Logs

```
================================================================================
🚀 Starting Autonomous Code Fixing Orchestrator
================================================================================
Max iterations: 10
Simulation mode: False
Config: /home/rmondo/repos/air-executor/config/autonomous_fix.yaml
================================================================================

============================================================
🔄 Run #1 - run_20251002_234136
============================================================
🔍 Smart Health Check: money-making-app
============================================================

⚡ Static Analysis (fast)...
❌ Static failed (19%) → Skipping dynamic checks

============================================================
📊 Smart Health Summary
============================================================
⚡ Static Analysis (19%):
  ❌ Analysis: fail (1818 errors)
  ⚠️ Code Quality: 47%

⚠️ Overall Health: 13%
============================================================

📍 Phase: build
🔍 Discovering build issues... Found 1818 errors

📦 Mega Batch Mode:
   Input tasks: 1818
   Output: 1 comprehensive mega-batch

🔨 Executing 1 task...
  [1/1] fix_mega_batch...

[Claude session output showing fixes being made...]

✅ Task completed: Success (Duration: 503.7s)
```

### Configuration for Airflow Runs

All parameters optional, passed via `dag_run.conf`:

```json
{
  "max_iterations": 10,          // Number of fix cycles (default: 10)
  "target_project": "/path",     // Override project path
  "simulation": false            // If true, no actual changes
}
```

**Examples**:

```json
// Quick test
{"max_iterations": 1, "simulation": true}

// Full production
{"max_iterations": 10, "simulation": false}

// Different project
{
  "max_iterations": 5,
  "target_project": "/home/rmondo/repos/other-project"
}
```

## Development Workflow

### Best Practices

**1. Version Control**
- ✅ Keep DAG source code in this directory
- ✅ Track changes, create branches, review via PRs
- ❌ Never edit files directly in `~/airflow/dags/`

**2. Development Cycle**
```bash
# 1. Edit DAG in git repo
vim airflow_dags/my_dag.py

# 2. Validate locally
python airflow_dags/my_dag.py  # Should run without errors

# 3. Commit changes
git add airflow_dags/my_dag.py
git commit -m "Update DAG logic"

# 4. Sync to Airflow
./scripts/sync_dags_to_airflow.sh

# 5. Test in Airflow UI (refreshes within ~30 seconds)
```

**3. Testing**
```bash
# Test DAG for syntax errors
airflow dags list-import-errors

# Test specific DAG
airflow dags test autonomous_fixing 2025-10-02

# Test specific task
airflow tasks test autonomous_fixing run_autonomous_fixing 2025-10-02
```

### DAG Development Template

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def my_task_function(**context):
    """Task implementation"""
    # Access parameters
    conf = context['dag_run'].conf or {}
    param = conf.get('my_param', 'default_value')

    # Your logic here
    print(f"Running with param: {param}")

    # Return value (available via XCom)
    return {'result': 'success'}

with DAG(
    'my_dag',
    default_args=default_args,
    description='My DAG description',
    schedule=None,  # Manual trigger only
    catchup=False,
) as dag:

    task = PythonOperator(
        task_id='my_task',
        python_callable=my_task_function,
        provide_context=True,
    )
```

## Monitoring

### Via Airflow UI

**DAG Overview**:
- Go to http://localhost:8080
- See all DAGs with run status, success rate
- Graph view showing task dependencies

**Live Monitoring**:
1. Click on running DAG
2. Click on running task
3. Click "Logs" tab
4. See streaming output in real-time

**Historical Analysis**:
- View past runs with duration, status
- Compare runs over time
- Identify trends and patterns

### Via CLI

```bash
# List all DAGs
airflow dags list

# List DAG runs
airflow dags list-runs -d autonomous_fixing

# Check task logs
airflow tasks logs autonomous_fixing run_autonomous_fixing <date>

# Check import errors
airflow dags list-import-errors
```

### Via Git (for Autonomous Fixing)

```bash
# Check commits created
cd /path/to/project
git log --oneline -10

# Review specific commit
git show HEAD

# See all changes
git diff HEAD~5 HEAD
```

### Via Redis (for Autonomous Fixing)

```bash
# View task queue
redis-cli ZRANGE autonomous_fix:task_queue 0 -1 WITHSCORES

# View run history
redis-cli LRANGE autonomous_fix:run_history 0 9

# View session summary
redis-cli GET autonomous_fix:summary:build
```

## Troubleshooting

### DAG Not Appearing in UI

**Check sync**:
```bash
./scripts/sync_dags_to_airflow.sh
airflow dags list | grep your_dag
```

**Check for import errors**:
```bash
airflow dags list-import-errors
```

**Check if paused**:
```bash
# Unpause manually
airflow dags unpause your_dag

# Or use auto-unpause
./scripts/sync_dags_to_airflow.sh --auto-unpause
```

**Force refresh**:
```bash
airflow dags reserialize
# Then refresh browser (F5)
```

### Task Fails Immediately

**For autonomous_fixing DAG**:

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Check virtual environment exists
ls ~/.venv/air-executor/bin/python

# Check Claude CLI authenticated
claude login

# Check target project exists
ls /path/to/project
```

**Check logs for error**:
```bash
airflow tasks logs autonomous_fixing run_autonomous_fixing <date>
```

### No Streaming Output Visible

Already handled with `PYTHONUNBUFFERED=1` and `bufsize=1`.

If still not working:
```python
# Check DAG configuration has:
env = {
    'PYTHONUNBUFFERED': '1'  # Must be present
}
```

### Stale DAGs Persisting

```bash
# Clean up stale metadata
./scripts/sync_dags_to_airflow.sh --cleanup

# If still present, manual cleanup:
airflow dags delete old_dag_id
```

### Changes Not Reflected

**Copy mode**: Re-sync required
```bash
./scripts/sync_dags_to_airflow.sh
```

**Symlink mode**: Wait ~30 seconds for scheduler to detect changes

**Force immediate refresh**:
```bash
airflow dags reserialize
```

## Batching System (for Autonomous Fixing)

The autonomous fixing system supports intelligent issue batching:

### Batching Modes

**1. Mega Batch Mode** - ONE comprehensive fix per phase
```yaml
issue_grouping:
  mega_batch_mode: true
batch_sizes:
  build_fixes: 1  # ONE mega-task
```
- Fast: 1 session for all issues
- Large commits (harder to review)
- All-or-nothing

**2. Smart Batch Mode** - Human-reviewable logical groups (DEFAULT)
```yaml
issue_grouping:
  mega_batch_mode: false
  max_cleanup_batch_size: 50
  max_location_batch_size: 20
batch_sizes:
  build_fixes: 3  # 3 focused batches
```
- Cleanup batches: "Remove all unused imports" (project-wide)
- Location batches: "Fix type errors in home/" (by module)
- Reviewable commits (10-30 files each)

**3. Individual Mode** - One issue at a time
```yaml
issue_grouping:
  max_cleanup_batch_size: 1  # Disables batching
batch_sizes:
  build_fixes: 5  # 5 individual fixes
```
- Very fine-grained
- Slow (100 issues = 100 sessions)
- Noisy commit history

### Batch Types

**Cleanup Batches** (Project-wide, one type):
- `chore: remove all unused imports (30 files)`
- `style: format all code (50 files)`
- `chore: add missing const keywords (40 files)`

**Location Batches** (One module/screen):
- `fix: type errors in home/ (15 issues, 8 files)`
- `fix: null safety in auth/ (12 issues, 6 files)`
- `fix: missing overrides in widgets/ (8 issues, 5 files)`

**Mega Batch** (Everything):
- `fix: comprehensive cleanup of 100 issues`

### Performance Comparison

100 build errors to fix:

| Mode | Claude Sessions | Time | Commits |
|------|----------------|------|---------|
| Mega Batch | 1 | ~15 min | 1 |
| Smart Batch | 5-7 | ~60 min | 5-7 |
| Individual | 100 | ~150 min | 100 |

## Integration with Other Systems

### Combined with Other DAGs

```python
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

trigger_fixing = TriggerDagRunOperator(
    task_id='trigger_fixing',
    trigger_dag_id='autonomous_fixing',
    conf={'max_iterations': 5, 'simulation': False}
)
```

### Scheduled Execution (Not Recommended)

For scheduled runs:
```python
# In DAG definition
schedule='0 2 * * *'  # Daily at 2 AM
```

**⚠️ Warning**: Only schedule if confident in system stability and error handling

### Notifications

```python
# Add to default_args
'on_failure_callback': notify_failure,
'on_success_callback': notify_success,
```

## Best Practices

### 1. Start with Simulation
```json
{"simulation": true, "max_iterations": 1}
```
Test without making changes

### 2. Monitor First Run
Watch entire first execution in UI before leaving unattended

### 3. Check Commits
```bash
cd /path/to/project
git log -10
git diff HEAD~5 HEAD
```

### 4. Progressive Rollout
- Test on 1 project first
- Review commits
- Scale to more projects

### 5. Use Appropriate Batching
- Mega batch: Initial cleanup, tech debt sprints
- Smart batch: Normal development (default)
- Individual: Testing, learning, critical code

## See Also

- **Main Docs**: See `/docs/AUTONOMOUS_FIXING.md` for complete autonomous fixing guide
- **Scripts**: See `/scripts/README.md` for script documentation
- **Configuration**: See `/docs/CONFIGURATION.md` for configuration reference
- **Architecture**: See `/docs/ARCHITECTURE.md` for system design

---

**For quick reference**: See project root `/QUICKSTART.md`
**For troubleshooting**: See `/docs/reference/troubleshooting.md`

**Last Updated**: 2025-01-10
