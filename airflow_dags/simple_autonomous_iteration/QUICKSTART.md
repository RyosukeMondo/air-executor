# Quick Start Guide - Simple Autonomous Iteration

Get started in 3 minutes with iterative AI execution.

## 🚀 Fastest Start (Shell Script + Monitor)

### Step 1: Open Terminal 1 - Start Monitor

```bash
cd /home/rmondo/repos/air-executor
./scripts/monitor.sh
```

You should see:
```
🔍 Monitoring wrapper execution...
   Log file: logs/wrapper-realtime.log

📋 Waiting for wrapper events...
```

### Step 2: Open Terminal 2 - Run Iteration

```bash
cd /home/rmondo/repos/air-executor

# Use project path from config
./scripts/simple_autonomous_iteration.sh \
  airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json

# OR override project path (work on different project)
./scripts/simple_autonomous_iteration.sh \
  airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json \
  /path/to/your/project
```

You should see:
```
================================================================================
🔁 Simple Autonomous Iteration
================================================================================
✓ Config file: airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json

[1/3] Detecting Python environment...
✓ Using project venv: .venv/bin/python3
✓ Python 3.10.x

[2/3] Validating config file...
✓ Config valid
   Prompt: resume @claudedocs/testability-improvements-plan.md...
   Completion file: claudedocs/testability-improvements-plan.md
   Max iterations: 30
   Circuit breaker: 3 iterations without progress

[3/3] Starting orchestrator...
================================================================================
🔁 Launching Simple Autonomous Iteration
================================================================================

🔁 ITERATION 1/30
...
```

### Step 3: Watch Progress

In **Terminal 1** (monitor), you'll see real-time Claude activity:
```
[12:34:56] stream (init)
[12:35:02] stream (tool: Read)
[12:35:15] stream (tool: Edit)
[12:35:20] stream (tool: Bash)
[12:35:30] run_completed
```

In **Terminal 2** (orchestrator), you'll see iteration progress:
```
🔁 ITERATION 1/30
⏱️  Iteration completed in 45.3s
✅ Success: True
🔍 Completion check: Completion pattern not found
📝 Progress check: Git changes detected

⏳ Waiting 5s before next iteration...

🔁 ITERATION 2/30
...
```

### Step 4: Completion

When done, you'll see either:

**Success**:
```
🎉 COMPLETION CONDITION MET in iteration 5!

================================================================================
📊 FINAL RESULT
================================================================================
Success: True
Reason: completion_condition_met
Iterations: 5
Duration: 267.3s
================================================================================
```

**Circuit Breaker (No Progress)**:
```
❌ Circuit breaker: 3 iterations without progress (threshold: 3)

================================================================================
📊 FINAL RESULT
================================================================================
Success: False
Reason: circuit_breaker_triggered
Iterations: 8
Duration: 342.1s
================================================================================
```

## 📝 Using Your Own Config

### Create Custom JSON Config

```json
{
  "prompt": "Your custom prompt here. Include completion instruction: - [ ] TASK COMPLETE",
  "completion_file": "docs/your-file.md",
  "completion_regex": "- \\[x\\] TASK COMPLETE",
  "max_iterations": 20,
  "project_path": "/path/to/your/project",
  "wrapper_path": "scripts/claude_wrapper.py",
  "python_exec": ".venv/bin/python3",
  "circuit_breaker_threshold": 3,
  "require_git_changes": true
}
```

Save to: `my-config.json`

### Run Your Config

```bash
# Terminal 1
./scripts/monitor.sh

# Terminal 2
./scripts/simple_autonomous_iteration.sh my-config.json
```

## 🎯 Common Use Cases

### 1. Resume Work on Plan

```json
{
  "prompt": "resume @docs/implementation-plan.md work through each task. Mark complete: - [ ] all done",
  "completion_file": "docs/implementation-plan.md",
  "completion_regex": "- \\[x\\] all done",
  "max_iterations": 30
}
```

### 2. Implement Feature

```json
{
  "prompt": "implement feature X according to @specs/feature-x.md. Complete checklist at end",
  "completion_file": "specs/feature-x.md",
  "completion_regex": "- \\[x\\] implementation complete",
  "max_iterations": 20
}
```

### 3. Systematic Refactoring

```json
{
  "prompt": "refactor @docs/refactoring-plan.md methodically. Mark: STATUS: DONE",
  "completion_file": "docs/refactoring-plan.md",
  "completion_regex": "STATUS:\\s*DONE",
  "max_iterations": 25
}
```

## ⚙️ Configuration Tips

### Increase Iteration Limit

For complex tasks:
```json
{
  "max_iterations": 50
}
```

### Adjust Circuit Breaker

Allow more iterations without changes:
```json
{
  "circuit_breaker_threshold": 5
}
```

### Disable Git Check (Not Recommended)

Only if you know Claude won't make file changes:
```json
{
  "require_git_changes": false
}
```

## 🔧 Troubleshooting

### Script says "Config file not found"

**Problem**: Path is wrong

**Solution**: Use absolute or relative path from project root
```bash
# ✅ Right
./scripts/simple_autonomous_iteration.sh airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json

# ❌ Wrong
./scripts/simple_autonomous_iteration.sh examples/testability_iteration.json
```

### Circuit breaker triggers immediately

**Problem**: Threshold too low or Claude not making changes

**Solutions**:
1. Increase threshold: `"circuit_breaker_threshold": 5`
2. Check if Claude is actually making changes (git status)
3. Verify prompt is clear about making changes

### Monitor shows nothing

**Problem**: Wrong log file or orchestrator not running

**Solutions**:
1. Check `logs/wrapper-realtime.log` exists
2. Ensure orchestrator is running in Terminal 2
3. Try clearing log: `> logs/wrapper-realtime.log`

### Python not found

**Problem**: Virtual environment not activated

**Solution**: Script auto-detects `.venv/bin/python3` - ensure it exists:
```bash
ls -la .venv/bin/python3
```

## 📚 Next Steps

- Read [Full README](README.md) for comprehensive docs
- Check [Examples](examples/) for more configs
- Learn about [Safety Features](README.md#safety-features)
- Try [Airflow DAG](../simple_autonomous_iteration_dag.py) for production

## 💡 Pro Tips

1. **Always use monitor.sh** - See what Claude is doing in real-time
2. **Start with low iterations** - Test with `max_iterations: 5` first
3. **Clear completion marker** - Make sure file has `- [ ] task done` before starting
4. **Check git status** - Ensure working directory is clean before starting
5. **Use circuit breaker** - Prevents wasting API calls when stuck
6. **Test regex first** - Verify completion pattern matches in Python:
   ```python
   import re
   content = open("your-file.md").read()
   match = re.search(r"- \[x\] task done", content)
   print(f"Will match: {match is not None}")
   ```

## 🆘 Need Help?

- Issues? Check [Troubleshooting](README.md#troubleshooting)
- Questions? Read [Full Documentation](README.md)
- Stuck? Review [Examples](examples/)
