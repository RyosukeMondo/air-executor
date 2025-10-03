# Running Autonomous Code Fixing

Quick guide to run the autonomous fixing orchestrator.

## Prerequisites

1. **Redis** (required for state management):
   ```bash
   redis-server
   # Verify: redis-cli ping (should return PONG)
   ```

2. **Python virtual environment** with dependencies:
   ```bash
   python -m venv ~/.venv/air-executor
   source ~/.venv/air-executor/bin/activate
   pip install redis pyyaml
   ```

3. **Flutter** (for Flutter projects):
   ```bash
   # Should be at ~/flutter/bin/flutter
   ```

4. **Claude Code** CLI authentication:
   ```bash
   claude login
   ```

## Running with Launch Script (Easiest)

```bash
# Test run (1 iteration)
./scripts/run_autonomous_fixing.sh --max-iterations=1

# Normal run (10 iterations)
./scripts/run_autonomous_fixing.sh --max-iterations=10

# Simulation (no actual changes)
./scripts/run_autonomous_fixing.sh --max-iterations=5 --simulation
```

## Running with PM2 (Best for Terminal Monitoring)

```bash
# Start orchestrator in background
pm2 start config/pm2.config.js

# Watch logs in realtime
pm2 logs autonomous-fixing --lines 50

# Follow logs (tail -f style)
pm2 logs autonomous-fixing --lines 0

# Check status
pm2 status

# Stop
pm2 stop autonomous-fixing

# Restart
pm2 restart autonomous-fixing
```

## Running with Airflow (Best for Web UI Monitoring)

```bash
# 1. Ensure Airflow is running
# Check if Airflow webserver and scheduler are running

# 2. Sync DAG to Airflow
./scripts/sync_dags_to_airflow.sh

# 3. Open Airflow web UI
# Go to: http://localhost:8080

# 4. Trigger the DAG with parameters
# - Find "autonomous_fixing" in the DAG list
# - Click "Trigger DAG w/ config"
# - Enter JSON parameters:
{
  "max_iterations": 10,
  "target_project": "/home/rmondo/repos/money-making-app",
  "simulation": false
}

# 5. Monitor streaming output in real-time
# - Click on the running task
# - Click "Logs" tab
# - See streaming Claude output with health checks, fixes, commits
```

**Airflow Benefits**:
- ✅ Real-time streaming logs in web browser
- ✅ Full Claude wrapper output visible
- ✅ Task history and execution times
- ✅ Can trigger with custom parameters
- ✅ Accessible from anywhere on network

## Configuration

Edit `config/autonomous_fix.yaml`:

```yaml
# Mega batch mode (ONE comprehensive fix)
issue_grouping:
  mega_batch_mode: true

batch_sizes:
  build_fixes: 1  # ONE task fixes ALL build errors
  test_fixes: 1
  lint_fixes: 1

# Smart batch mode (human-reviewable commits)
issue_grouping:
  mega_batch_mode: false
  max_cleanup_batch_size: 50
  max_location_batch_size: 20

batch_sizes:
  build_fixes: 3  # 3 focused batches
  test_fixes: 2
  lint_fixes: 2
```

## Monitoring Progress

### With Airflow Web UI (Recommended)
```bash
# 1. Open browser to http://localhost:8080
# 2. Click on "autonomous_fixing" DAG
# 3. Click on running task instance
# 4. Click "Logs" tab
# 5. See streaming output with:
#    - Health check results
#    - Issues being fixed
#    - Claude's reasoning
#    - Commit messages
#    - Progress through iterations
```

### With PM2
```bash
# Realtime logs
pm2 logs autonomous-fixing

# Logs location
tail -f logs/autonomous-fixing-out.log
tail -f logs/autonomous-fixing-error.log
```

### Check Git Commits
```bash
cd /home/rmondo/repos/money-making-app
git log --oneline -10
git show HEAD  # See latest commit
```

### Check Redis State
```bash
# View queued tasks
redis-cli ZRANGE autonomous_fix:task_queue 0 -1 WITHSCORES

# View run history
redis-cli LRANGE autonomous_fix:run_history 0 -1

# View failure count
redis-cli GET autonomous_fix:failure_count

# Clear everything (if needed)
redis-cli FLUSHDB
```

## Expected Output

```
🚀 Starting Autonomous Code Fixing Orchestrator
============================================================
Project: money-making-app
Mode: LIVE
============================================================

============================================================
🔄 Run #1 - run_20251002_233653
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
     Errors: 2090
  ⚠️ Code Quality: 47%
     Files: 360, Avg: 171 lines
     ⚠️ 10 files > 300 lines
     ⚠️ Max nesting: 9 levels

⏭️ Dynamic checks skipped (static score: 19% < 60%)

⚠️ Overall Health: 13%
   Mode: static_only
   Status: Needs Attention
============================================================

📍 Phase: build
🔍 Discovering build issues...
  Found 2090 build errors

📦 Mega Batch Mode:
   Input tasks: 2090
   Output: 1 comprehensive mega-batch

📝 Queueing 1 tasks (found 1 total)

🔨 Executing 1 tasks...

  [1/1] fix_mega_batch...

🚀 Running task: fix_mega_batch (task_87880b3b)
    [Claude is fixing 2090 issues... this may take 10-15 minutes]

✅ Task task_87880b3b: Success
   Duration: 843.2s

  ✅ Fixed 1/1 tasks
```

## Troubleshooting

### No commits appearing
```bash
# Check if wrapper can access claude
which claude
# Should be /usr/local/bin/claude

# Test wrapper manually
cd /home/rmondo/repos/money-making-app
echo '{"action":"prompt","prompt":"hello","options":{"cwd":"."}}' | \
  python ~/.venv/air-executor/bin/python \
  /home/rmondo/repos/air-executor/scripts/claude_wrapper.py
```

### Redis connection failed
```bash
redis-server  # Start Redis
redis-cli ping  # Should return PONG
```

### Python module not found
```bash
source ~/.venv/air-executor/bin/activate
pip install redis pyyaml
```

## Performance

**Mega Batch Mode** (mega_batch_mode: true):
- 2090 errors → 1 task → 1 Claude session → ~15 minutes → 1 commit

**Smart Batch Mode** (mega_batch_mode: false):
- 2090 errors → ~7 batches → 7 Claude sessions → ~60 minutes → 7 commits

## See Also

- `fix_orchestrator.py` - Main orchestration logic
- `config/autonomous_fix.yaml` - Configuration
- `README_BATCHING_MODES.md` - Batching strategy guide
- `README_BATCH_FIXING.md` - Batch fixing details
