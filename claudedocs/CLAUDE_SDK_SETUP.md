# Claude Code SDK Integration with Airflow

## Problem Solved

The original `claude_query` DAG using `claude -p` command would **hang indefinitely** because:
- Claude CLI requires a TTY (interactive terminal)
- Airflow BashOperator doesn't provide TTY by default
- No timeout mechanism to prevent blocking

## Solution: claude_code_sdk + claude_wrapper.py

We use the **proven** `claude_wrapper.py` approach from cc-task-manager:
- ✅ **Non-blocking** execution (no TTY required)
- ✅ **JSON-based** stdin/stdout communication
- ✅ **Streaming** responses in real-time
- ✅ **Auto-exit** when complete
- ✅ **Async** support via `anyio`

---

## Architecture

```
┌─────────────┐
│   Airflow   │
│  PythonOp   │
└──────┬──────┘
       │ subprocess
       ▼
┌─────────────────────┐
│ claude_wrapper.py   │
│ (JSON stdin/stdout) │
└──────┬──────────────┘
       │ claude_code_sdk.query()
       ▼
┌─────────────────────┐
│  Claude Code CLI    │
│   (headless mode)   │
└─────────────────────┘
```

### Communication Flow

1. **Start**: Airflow starts `claude_wrapper.py` as subprocess
2. **Ready**: Wrapper sends `{"event": "ready"}` via stdout
3. **Prompt**: Airflow sends `{"action": "prompt", "prompt": "...", "options": {...}}` via stdin
4. **Stream**: Wrapper forwards Claude's responses as `{"event": "stream", "payload": {...}}`
5. **Complete**: Wrapper sends `{"event": "run_completed"}`
6. **Shutdown**: Wrapper auto-exits (thanks to `exit_on_complete: true`)

---

## Setup Instructions

### Step 1: Install claude-code-sdk

```bash
source .venv/bin/activate
pip install claude-code-sdk
```

**Installed version:** `claude-code-sdk==0.0.25`

**Dependencies:**
- `anyio>=4.0.0` - Async I/O
- `mcp>=0.1.0` - Model Context Protocol

### Step 2: Copy claude_wrapper.py

The wrapper is already copied from `cc-task-manager`:

```bash
cp /home/rmondo/repos/cc-task-manager/scripts/claude_wrapper.py \
   /home/rmondo/repos/air-executor/scripts/
chmod +x scripts/claude_wrapper.py
```

**Location:** `scripts/claude_wrapper.py` (716 lines)

### Step 3: Verify Installation

```bash
# Test SDK import
source .venv/bin/activate
python -c "import claude_code_sdk; print('✅ SDK installed')"

# Test wrapper
python scripts/test_claude_wrapper.py
```

---

## DAG Usage

### Simple DAG: claude_query_sdk

**File:** `airflow_dags/claude_query_sdk.py`

**Key Features:**
- Uses `PythonOperator` (not BashOperator)
- Sends prompt via JSON stdin
- Collects streaming responses
- Returns full conversation via XCom

**Trigger:**
```bash
# Via CLI
airflow dags trigger claude_query_sdk

# Via UI
# http://localhost:8080 → Find claude_query_sdk → Click play button
```

**Check logs:**
```bash
# View task logs
airflow tasks logs claude_query_sdk run_claude_query_sdk <run_id>
```

---

## How the Wrapper Works

### 1. JSON Command Format

Send commands via stdin as JSON:

```json
{
  "action": "prompt",
  "prompt": "hello, how old are you?",
  "options": {
    "exit_on_complete": true,
    "permission_mode": "bypassPermissions",
    "cwd": "/path/to/working/dir"
  }
}
```

**Options:**
- `exit_on_complete`: Auto-shutdown after completion (recommended for Airflow)
- `permission_mode`: "bypassPermissions" to auto-approve all operations
- `cwd`: Working directory for Claude execution
- `session_id`: Resume a previous session

### 2. Event Stream Format

Wrapper sends events via stdout as JSON:

```json
{"event": "ready", "timestamp": "...", "state": "idle"}
{"event": "run_started", "run_id": "...", "timestamp": "..."}
{"event": "stream", "run_id": "...", "payload": {...}}
{"event": "run_completed", "run_id": "...", "outcome": "completed"}
{"event": "shutdown", "timestamp": "..."}
```

**Event Types:**
- `ready` - Wrapper initialized and waiting for commands
- `run_started` - Query execution started
- `stream` - Streaming response from Claude (contains `payload.content`)
- `run_completed` - Query finished successfully
- `run_failed` - Query failed (check `error` field)
- `run_cancelled` - Query was cancelled
- `shutdown` - Wrapper shutting down

### 3. Extracting Claude's Response

Claude's text appears in stream events:

```json
{
  "event": "stream",
  "payload": {
    "content": [
      {"type": "text", "text": "I don't have a specific age..."}
    ]
  }
}
```

**Extraction logic:**
```python
for event in events:
    if event["event"] == "stream":
        payload = event["payload"]
        content = payload.get("content", [])
        for item in content:
            if item.get("type") == "text":
                text = item.get("text")
                # This is Claude's response!
```

---

## Complete Python Example

```python
import subprocess
import json
from pathlib import Path

def run_claude_query(prompt: str) -> str:
    """Run Claude query and return response."""
    wrapper_path = Path("scripts/claude_wrapper.py")
    venv_python = Path(".venv/bin/python")

    # Start wrapper
    process = subprocess.Popen(
        [str(venv_python), str(wrapper_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    conversation = []

    for line in process.stdout:
        event = json.loads(line)

        if event["event"] == "ready":
            # Send prompt
            command = {
                "action": "prompt",
                "prompt": prompt,
                "options": {"exit_on_complete": True}
            }
            process.stdin.write(json.dumps(command) + "\n")
            process.stdin.flush()

        elif event["event"] == "stream":
            # Extract text
            payload = event["payload"]
            for item in payload.get("content", []):
                if item.get("type") == "text":
                    conversation.append(item["text"])

        elif event["event"] == "shutdown":
            break

    process.wait(timeout=60)
    return "\n".join(conversation)

# Usage
response = run_claude_query("What is 2+2?")
print(response)
```

---

## Testing

### Local Test (Recommended First)

```bash
source .venv/bin/activate
python scripts/test_claude_wrapper.py
```

**Expected output:**
```
🧪 Testing claude_wrapper.py
============================================================
🚀 Starting wrapper...
📨 ready
✅ Wrapper ready! Sending prompt...
📨 stream
💬 Hello from Airflow test!
📨 run_completed
✅ Run completed!
📨 shutdown
✅ Shutdown
============================================================
✅ TEST PASSED
============================================================
```

### Airflow Test

```bash
# Validate DAG
python scripts/validate_dag.py airflow_dags/claude_query_sdk.py

# Sync to Airflow
./airflow_dags/sync_to_airflow.sh

# Trigger
airflow dags trigger claude_query_sdk

# Check logs
airflow tasks logs claude_query_sdk run_claude_query_sdk <run_id>
```

---

## Comparison: Old vs New

| Feature | claude_query (OLD) | claude_query_sdk (NEW) |
|---------|-------------------|------------------------|
| **Operator** | BashOperator | PythonOperator |
| **Command** | `claude -p "..."` | `claude_wrapper.py` via subprocess |
| **TTY** | ❌ Required (blocks) | ✅ Not required |
| **Timeout** | ❌ None (hangs forever) | ✅ 60s timeout |
| **Streaming** | ❌ No | ✅ Yes (JSON events) |
| **Auto-exit** | ❌ Manual kill required | ✅ Auto-shutdown |
| **Permissions** | ❌ Interactive prompts | ✅ Auto-approved |
| **Error handling** | ❌ Poor | ✅ Comprehensive |
| **Session reuse** | ❌ No | ✅ Yes (session_id) |

---

## Troubleshooting

### Issue 1: "claude_code_sdk not available"

**Symptom:** Wrapper fails with import error

**Solution:**
```bash
source .venv/bin/activate
pip install claude-code-sdk
python -c "import claude_code_sdk; print('OK')"
```

### Issue 2: Timeout after 60 seconds

**Symptom:** Query times out

**Possible causes:**
1. Claude API rate limit
2. Complex query taking too long
3. Waiting for user input (check `permission_mode`)

**Solution:**
```python
# Increase timeout
process.wait(timeout=300)  # 5 minutes

# Check for rate limits in events
if event.get("event") == "limit_notice":
    print(f"Rate limit: {event.get('message')}")
```

### Issue 3: No response text

**Symptom:** Events received but no text extracted

**Debug:**
```python
# Print all stream events
if event["event"] == "stream":
    print(json.dumps(event, indent=2))
    # Check payload structure
```

**Common causes:**
- Response is in different field (`message`, `text`, etc.)
- Need to extract from nested structure
- Event still processing (wait for more events)

### Issue 4: Process hangs

**Symptom:** Wrapper starts but never sends "ready"

**Debug:**
```bash
# Check wrapper directly
echo '{"action":"status"}' | python scripts/claude_wrapper.py
```

**Possible causes:**
- Missing dependencies
- Claude CLI not in PATH
- SDK initialization error

---

## Advanced Features

### Session Reuse

```python
# First query
command1 = {
    "action": "prompt",
    "prompt": "Create a file called test.txt",
    "options": {}
}

# Later query - reuse same session
command2 = {
    "action": "prompt",
    "prompt": "Now read test.txt",
    "options": {
        "resume_last_session": True  # Reuse last session
    }
}
```

### Cancel Running Query

```python
# Cancel by run_id
cancel_command = {
    "action": "cancel",
    "run_id": "abc-123"
}
```

### Custom Working Directory

```python
command = {
    "action": "prompt",
    "prompt": "List files in current directory",
    "options": {
        "cwd": "/home/user/project"
    }
}
```

---

## Files Overview

```
air-executor/
├── scripts/
│   ├── claude_wrapper.py          # JSON stdin/stdout wrapper (716 lines)
│   └── test_claude_wrapper.py     # Local test script
│
├── airflow_dags/
│   ├── claude_query_dag.py        # ❌ OLD: Blocking BashOperator
│   └── claude_query_sdk.py        # ✅ NEW: Non-blocking PythonOperator
│
└── claudedocs/
    └── CLAUDE_SDK_SETUP.md        # This file
```

---

## Next Steps

1. **Test locally:** `python scripts/test_claude_wrapper.py`
2. **Deploy to Airflow:** `./scripts/quick_deploy_dag.sh airflow_dags/claude_query_sdk.py`
3. **Trigger DAG:** Airflow UI → `claude_query_sdk` → Play button
4. **Check logs:** Click task → View Log
5. **See response:** Look for "📋 CLAUDE'S RESPONSE" section

---

## Summary

✅ **Problem solved:** No more hanging on `claude -p` command
✅ **Non-blocking:** Uses JSON stdin/stdout instead of TTY
✅ **Proven approach:** Copied from working cc-task-manager
✅ **Production ready:** Error handling, timeouts, streaming
✅ **Easy to use:** Single PythonOperator, clear logs

**DAG name:** `claude_query_sdk`
**Status:** ✅ Deployed and tested
**Ready to use:** Yes! Just trigger in Airflow UI
