# Airflow DAG Integration for Autonomous Fixing

Web UI monitoring for autonomous code fixing with streaming Claude output.

## Quick Start

```bash
# 1. Sync DAG to Airflow
./scripts/sync_dags_to_airflow.sh

# 2. Open Airflow web UI
# Browser: http://localhost:8080

# 3. Find and trigger "autonomous_fixing" DAG
# Click: Trigger DAG w/ config

# 4. Enter parameters (JSON):
{
  "max_iterations": 10,
  "target_project": "/home/rmondo/repos/money-making-app",
  "simulation": false
}

# 5. View streaming logs
# Click: Task → Logs
```

## Features

### Real-Time Streaming Output
- ✅ See Claude's live reasoning and fixes
- ✅ Monitor health checks in real-time
- ✅ Watch commit messages as they're created
- ✅ Track progress through iterations
- ✅ No terminal needed - all in browser

### Web UI Benefits
- **Accessible**: Monitor from anywhere on network
- **History**: See all past runs and durations
- **Parameterized**: Customize each run with JSON config
- **Visual**: Clean web interface vs terminal logs
- **Persistent**: Logs stored and accessible after completion

## DAG Configuration

### Location
- **Source**: `airflow_dags/autonomous_fixing_dag.py`
- **Deployed**: Synced to `~/airflow/dags/` via sync script

### Parameters

All parameters are optional and passed via `dag_run.conf`:

```json
{
  "max_iterations": 10,           // Number of fixing iterations (default: 10)
  "target_project": "/path/to/project",  // Override project path
  "simulation": false             // If true, no actual changes made
}
```

**Examples**:

```json
// Quick test run
{
  "max_iterations": 1,
  "simulation": true
}

// Full production run
{
  "max_iterations": 10,
  "target_project": "/home/rmondo/repos/money-making-app",
  "simulation": false
}

// Different project
{
  "max_iterations": 5,
  "target_project": "/home/rmondo/repos/other-project"
}
```

### Execution Settings

```python
execution_timeout=timedelta(hours=4)  # Max 4 hours per run
retries=0                              # No auto-retry (manual retry available)
schedule=None                          # Manual trigger only
```

## How It Works

### Execution Flow

```
User triggers DAG with parameters
    ↓
PythonOperator runs run_autonomous_fixing()
    ↓
Spawns subprocess with orchestrator
    ↓
Streams stdout line-by-line to Airflow logs
    ↓
User sees real-time output in web UI
    ↓
On completion: success/failure shown in UI
```

### Streaming Implementation

```python
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,  # Line buffered for real-time
)

# Stream output line by line (visible in Airflow UI)
for line in process.stdout:
    print(line, end='', flush=True)
```

Every line printed appears immediately in the Airflow log viewer.

## What You'll See

### In the Logs Tab

```
================================================================================
🚀 Starting Autonomous Code Fixing Orchestrator
================================================================================
Max iterations: 10
Simulation mode: False
Config: /home/rmondo/repos/air-executor/config/autonomous_fix.yaml
Command: /home/rmondo/.venv/air-executor/bin/python ...
================================================================================

============================================================
🔄 Run #1 - run_20251002_234136
============================================================
🔍 Smart Health Check: money-making-app
============================================================

⚡ Static Analysis (fast)...

❌ Static failed (19%) → Skipping dynamic checks
   (Fix static issues first to save time)

============================================================
📊 Smart Health Summary
============================================================

⚡ Static Analysis (19%):
  ❌ Analysis: fail
     Errors: 1818
  ⚠️ Code Quality: 47%
     Files: 359, Avg: 171 lines

⚠️ Overall Health: 13%
   Status: Needs Attention
============================================================

📍 Phase: build
🔍 Discovering build issues...
  Found 1818 build errors

📦 Mega Batch Mode:
   Input tasks: 1818
   Output: 1 comprehensive mega-batch

🔨 Executing 1 tasks...

  [1/1] fix_mega_batch...

[Claude session output showing fixes being made...]

✅ Task completed: Success
   Duration: 503.7s

  ✅ Fixed 1/1 tasks
  📊 Will run full health check next iteration to verify fixes

============================================================
🔄 Run #2 - run_20251002_235007
============================================================
[Next iteration begins...]
```

## Comparison: PM2 vs Airflow

| Feature | PM2 | Airflow |
|---------|-----|---------|
| **Interface** | Terminal | Web Browser |
| **Accessibility** | SSH required | Network accessible |
| **History** | Log files only | Full UI history |
| **Parameters** | Command line args | JSON config per run |
| **Monitoring** | `pm2 logs` command | Click Logs tab |
| **Best For** | Server automation | Interactive monitoring |

**Use PM2 when**: Running headless on server, automation scripts, CI/CD pipelines

**Use Airflow when**: Interactive development, debugging, real-time monitoring, multiple team members

## Troubleshooting

### DAG not appearing in UI

```bash
# 1. Check if DAG was synced
./scripts/sync_dags_to_airflow.sh

# 2. Check Airflow DAG list
airflow dags list | grep autonomous_fixing

# 3. Check for import errors
airflow dags list-import-errors

# 4. Refresh Airflow UI (F5)
```

### Task fails immediately

**Check prerequisites**:
```bash
# Redis must be running
redis-cli ping  # Should return PONG

# Virtual environment must exist
ls ~/.venv/air-executor/bin/python  # Should exist

# Claude CLI authenticated
claude login  # If not already logged in

# Target project exists
ls /home/rmondo/repos/money-making-app  # Should exist
```

### No streaming output visible

**Cause**: Output buffering

**Fix**: Already handled with `PYTHONUNBUFFERED=1` and `bufsize=1`

If still not working:
```python
# Check DAG configuration
env: {
    PYTHONUNBUFFERED: '1'  # Must be present
}
```

### Task timeout after 4 hours

**Expected**: Configured timeout is 4 hours

**Solutions**:
1. Reduce `max_iterations` parameter
2. Enable `simulation: true` for testing
3. Fix underlying issues causing slow progress
4. Increase timeout in DAG file (not recommended)

## Integration with Existing Workflows

### Combined with Other DAGs

```python
# upstream_dag.py
trigger_dag = TriggerDagRunOperator(
    task_id='trigger_fixing',
    trigger_dag_id='autonomous_fixing',
    conf={
        'max_iterations': 5,
        'simulation': False
    }
)
```

### Scheduled Execution

To enable scheduled runs (not recommended without monitoring):

```python
# In autonomous_fixing_dag.py
schedule='0 2 * * *'  # Daily at 2 AM
```

**Warning**: Only schedule if you're confident in:
- System stability
- Project health
- Error handling
- Notification setup

## Monitoring Best Practices

1. **Start with simulation**: Test with `"simulation": true` first
2. **Watch first run**: Monitor entire first execution in UI
3. **Check commits**: Verify commits in target project: `git log`
4. **Health tracking**: Watch health scores improving over iterations
5. **Error patterns**: Note repeated errors that need manual attention

## See Also

- `autonomous_fixing_dag.py` - DAG implementation
- `../scripts/README_AUTONOMOUS_FIXING.md` - All execution methods
- `autonomous_fixing/fix_orchestrator.py` - Core orchestration logic
- `../config/autonomous_fix.yaml` - Configuration options
