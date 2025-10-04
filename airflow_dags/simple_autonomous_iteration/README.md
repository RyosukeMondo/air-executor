# Simple Autonomous Iteration

A lightweight autonomous AI orchestrator for iterative task execution.

## Overview

This module provides a simple way to:
1. Execute a prompt with Claude AI
2. Wait for completion
3. Check a completion condition (regex in a file)
4. Repeat until done or max iterations reached

Much simpler than the full `autonomous_fixing` orchestrator - just:
- **Single prompt**: One prompt executed repeatedly
- **Simple completion check**: Regex pattern in a markdown file
- **Max iterations**: Stop after N iterations

## Architecture

```
SimpleOrchestrator
├── Execute prompt → Claude
├── Wait for completion
├── Check completion condition (regex in file)
└── Loop until done or max iterations
```

Reuses infrastructure from `autonomous_fixing`:
- `ClaudeClient`: For Claude wrapper communication
- `claude_wrapper.py`: For Claude CLI integration

## Usage

### 1. Airflow DAG (Recommended)

Trigger via Airflow UI:

```json
{
  "prompt": "resume @claudedocs/testability-improvements-plan.md perform implementation one step at a time. when everything done, check 'everything done' sits at the very last of the md file. - [ ] everything done",
  "completion_file": "claudedocs/testability-improvements-plan.md",
  "completion_regex": "- \\[x\\] everything done",
  "max_iterations": 30,
  "project_path": "/home/rmondo/repos/air-executor"
}
```

**Steps**:
1. Go to http://localhost:8080
2. Find "simple_autonomous_iteration" DAG
3. Click "Trigger DAG w/ config"
4. Paste JSON config
5. Click "Logs" to see real-time output

### 2. Shell Script (Recommended for Local)

Run with monitoring in two terminals:

**Terminal 1** (Monitor):
```bash
./scripts/monitor.sh
```

**Terminal 2** (Execute):

**Option A: Plan Document Mode (Simplest)**
```bash
# Work on plan in current project
./scripts/simple_autonomous_iteration.sh \
  claudedocs/testability-improvements-plan.md

# Work on plan in different project
./scripts/simple_autonomous_iteration.sh \
  docs/implementation-plan.md \
  /path/to/your/project

# With custom max iterations
./scripts/simple_autonomous_iteration.sh \
  docs/implementation-plan.md \
  /path/to/your/project \
  50
```

**Option B: Config File Mode (More Control)**
```bash
# Use config file
./scripts/simple_autonomous_iteration.sh \
  airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json

# Override project path
./scripts/simple_autonomous_iteration.sh \
  config.json \
  /path/to/target/project
```

The script:
- Validates Python environment
- Parses JSON config
- Runs orchestrator with all parameters
- Writes to `logs/wrapper-realtime.log` for monitoring

### 3. Direct CLI Usage

Run directly from command line (without script):

```bash
.venv/bin/python3 airflow_dags/simple_autonomous_iteration/simple_orchestrator.py \
  --prompt "resume @claudedocs/testability-improvements-plan.md perform implementation one step at a time. when everything done, check 'everything done' sits at the very last of the md file. - [ ] everything done" \
  --completion-file "claudedocs/testability-improvements-plan.md" \
  --completion-regex "- \[x\] everything done" \
  --max-iterations 30 \
  --project-path "/home/rmondo/repos/air-executor"
```

## Configuration

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | str | Required | Prompt to send to Claude on each iteration |
| `completion_file` | str | Required | File to check for completion condition |
| `completion_regex` | str | `- \[x\] everything done` | Regex pattern for completion |
| `max_iterations` | int | 30 | Maximum number of iterations |
| `project_path` | str | `.` | Working directory for Claude |
| `wrapper_path` | str | `scripts/claude_wrapper.py` | Path to claude_wrapper.py |
| `python_exec` | str | `.venv/bin/python3` | Python executable |
| `circuit_breaker_threshold` | int | 3 | Stop after N iterations without progress |
| `require_git_changes` | bool | true | Require git changes to consider progress |

### Example Completion Conditions

**Markdown checkbox**:
```python
completion_regex = r"- \[x\] everything done"
```

**Multiple checkboxes (all must be checked)**:
```python
completion_regex = r"- \[x\] task1.*\n.*- \[x\] task2.*\n.*- \[x\] task3"
```

**Simple text marker**:
```python
completion_regex = r"STATUS: COMPLETE"
```

**JSON field**:
```python
completion_regex = r'"status":\s*"completed"'
```

## Example Prompts

### Resume work on plan
```
resume @claudedocs/testability-improvements-plan.md
perform implementation one step at a time.
when everything done, check "everything done" sits at the very last of the md file.
- [ ] everything done
```

### Implement feature with checklist
```
implement feature X according to @docs/feature-spec.md
complete all tasks in the checklist:
- [ ] task 1
- [ ] task 2
- [ ] task 3
- [ ] everything done
```

### Iterative refactoring
```
refactor codebase according to @docs/refactoring-plan.md
work through each section systematically.
mark complete when done: STATUS: COMPLETE
```

## Safety Features

### Circuit Breaker

**Prevents wasting API calls when Claude isn't making progress.**

- Tracks git changes after each iteration
- If no changes detected for N consecutive iterations (default: 3), stops execution
- Saves money by avoiding infinite loops
- Can be disabled with `require_git_changes: false` (not recommended)

**Example output**:
```
📝 Progress check: Git changes detected
📝 Progress check: No git changes detected
📝 Progress check: No git changes detected
📝 Progress check: No git changes detected
❌ Circuit breaker: 3 iterations without progress (threshold: 3)
```

### Git Change Tracking

**Ensures Claude is making actual progress, not just running.**

- Computes hash of `git diff HEAD` after each iteration
- Compares with previous iteration's hash
- Resets counter when changes detected
- Handles non-git repos gracefully

### Cost Protection

By combining circuit breaker + git tracking:
- ✅ Prevents infinite loops wasting API calls
- ✅ Detects when Claude is stuck and stops early
- ✅ Ensures iterations are productive (making code changes)
- ✅ Saves money on Claude API usage

## How It Works

### Iteration Flow

```
1. Start Iteration N
   ↓
2. Execute prompt with Claude
   ↓
3. Wait for Claude to complete
   ↓
4. Check completion file for regex match
   ↓
5. Check git changes (progress detection)
   ↓
6. Circuit breaker check
   ↓
7. If complete → SUCCESS, exit
   If no progress (3x) → ABORT (circuit breaker)
   If max iterations → STOP
   Otherwise → Wait 5s, go to step 1
```

### Session Continuity

The orchestrator maintains session continuity across iterations:
- First iteration: Creates new Claude session
- Subsequent iterations: Reuses same session
- Claude retains context from previous iterations

This allows Claude to:
- Remember previous work
- Build on earlier progress
- Maintain conversation context

## Monitoring

### Shell Script Monitoring

When using `./scripts/simple_autonomous_iteration.sh`, use `./scripts/monitor.sh` for real-time progress:

**Terminal 1**:
```bash
./scripts/monitor.sh
```

Output:
```
🔍 Monitoring wrapper execution...
   Log file: logs/wrapper-realtime.log

📋 Waiting for wrapper events...
   (Run './scripts/simple_autonomous_iteration.sh ...' in another terminal)

[12:34:56] stream (init)
[12:35:02] stream (tool: Edit)
[12:35:15] stream (tool: Read)
[12:35:20] run_completed
```

**Terminal 2**:
```bash
./scripts/simple_autonomous_iteration.sh \
  airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json
```

### Airflow UI

Real-time monitoring in Airflow logs:
```
🔁 ITERATION 1/30
================================================================================
Prompt: resume @claudedocs/testability-improvements-plan.md...
Project: /home/rmondo/repos/air-executor

⏱️  Iteration completed in 45.3s
✅ Success: True

🔍 Completion check: Completion pattern not found

⏳ Waiting 5s before next iteration...
```

### Log Files

Real-time wrapper logs:
```
logs/wrapper-realtime.log  # Live Claude wrapper events
```

## Comparison with Full Orchestrator

| Feature | Simple Iteration | Full Autonomous Fixing |
|---------|------------------|------------------------|
| **Prompt** | Single prompt | Multiple phases (P1, P2, P3) |
| **Completion** | Regex in file | Quality gates + scores |
| **Language Support** | Universal | Python, JavaScript, Go, Flutter |
| **Analysis** | None | Static analysis, tests, builds |
| **Fixing** | General | Issue-specific fixes |
| **Complexity** | ~200 LOC | ~3000 LOC |
| **Use Case** | General tasks | Code quality improvement |

## When to Use

**Use Simple Iteration when**:
- ✅ You have a single, clear task
- ✅ You can define completion with a simple check
- ✅ You want Claude to work iteratively on one thing
- ✅ You need flexibility and simplicity

**Use Full Orchestrator when**:
- ✅ You're improving code quality
- ✅ You need language-specific analysis
- ✅ You want progressive hook enforcement
- ✅ You need detailed metrics and scoring

## Advanced Usage

### Custom Completion Logic

Extend `SimpleOrchestrator.check_completion()` for custom logic:

```python
def check_completion(self) -> tuple[bool, str]:
    # Custom completion logic
    if self.completion_check_file.exists():
        content = self.completion_check_file.read_text()

        # Example: Check if all tests pass
        if "All tests passed" in content and "0 failures" in content:
            return True, "All tests passed"

    return False, "Tests not complete"
```

### Dynamic Prompts

Modify prompt based on iteration:

```python
def execute_iteration(self, iteration: int) -> dict:
    # Customize prompt per iteration
    dynamic_prompt = f"{self.prompt}\n\nIteration {iteration} of {self.max_iterations}"

    result = self.claude.query(
        prompt=dynamic_prompt,
        project_path=str(self.project_path),
        timeout=600,
        session_id=self.session_id,
    )
    return result
```

## Troubleshooting

### Issue: Iterations run too fast
**Solution**: Increase wait time between iterations:
```python
time.sleep(10)  # Wait 10s instead of 5s
```

### Issue: Claude session expires
**Solution**: Increase timeout or reduce iterations:
```python
timeout=1200  # 20 minutes per iteration
```

### Issue: Completion pattern never matches
**Solution**: Test regex pattern:
```python
import re
content = Path("claudedocs/testability-improvements-plan.md").read_text()
match = re.search(r"- \[x\] everything done", content)
print(f"Match found: {match is not None}")
```

### Issue: Circuit breaker triggers too early
**Solution**: Increase threshold or disable git check:
```python
circuit_breaker_threshold=5  # Allow 5 iterations without changes
# OR
require_git_changes=False  # Disable (not recommended - wastes API calls)
```

### Issue: Claude makes changes but circuit breaker still triggers
**Solution**: Check if changes are committed vs uncommitted:
- Circuit breaker only detects uncommitted changes (`git diff HEAD`)
- If Claude commits changes, they won't be detected
- Ensure Claude doesn't auto-commit during iterations

## Examples

See `examples/` directory for:
- `testability_iteration.json` - Resume testability improvements
- `feature_implementation.json` - Implement feature from spec
- `refactoring_iteration.json` - Systematic refactoring

## License

Same as parent project (air-executor)
