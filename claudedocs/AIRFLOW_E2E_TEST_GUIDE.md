# Airflow E2E Test Guide for Claude Query SDK

## ✅ Ready to Test

The `claude_query_sdk` DAG is:
- ✅ Synced to Airflow
- ✅ Registered and discovered
- ✅ Unpaused and ready to trigger
- ✅ Using config (environment-independent)

---

## 🚀 How to Run in Airflow UI

### Step 1: Access Airflow UI

Open your browser:
```
http://localhost:8080
```

**Login credentials** (if prompted):
- Username: `airflow` (or check your setup)
- Password: `airflow` (or check your setup)

### Step 2: Find the DAG

1. On the **DAGs** page, look for `claude_query_sdk`
2. You should see it in the list with:
   - **Tags:** `claude`, `sdk`, `non-blocking`
   - **Paused:** OFF (toggle should be on/green)
   - **Schedule:** None (manual trigger only)

**Search tip:** Use the search box at top, type: `claude`

### Step 3: Trigger the DAG

**Method 1: Quick Trigger (Recommended)**
1. Find `claude_query_sdk` in the DAG list
2. Click the **▶️ Play button** on the right side
3. Click **Trigger DAG** in the popup

**Method 2: Detailed Trigger**
1. Click on the DAG name `claude_query_sdk`
2. Click **▶️ Trigger DAG** button (top right)
3. Click **Trigger** to confirm

### Step 4: Monitor Execution

After triggering, you'll see a new DAG run:

1. **Grid View** (default):
   - Click on the DAG name to see runs
   - Latest run appears at the top
   - Task: `run_claude_query_sdk`

2. **Watch Task Status:**
   - ⚪ **Queued** - Waiting to start
   - 🟡 **Running** - Executing now
   - 🟢 **Success** - Completed successfully
   - 🔴 **Failed** - Error occurred

### Step 5: View Logs

**To see Claude's response:**

1. Click on the task square (`run_claude_query_sdk`)
2. Click **Log** button
3. Scroll through the logs

**What to look for:**
```
🚀 Starting claude_wrapper.py with prompt: hello, how old are you?
📨 Event: ready
✅ Wrapper ready, sending prompt...
📨 Event: stream
💬 Claude: [Response text here]
📨 Event: run_completed
✅ Run completed successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CLAUDE'S RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Full conversation here]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 What to Expect

### Expected Flow

1. **Task starts** (~1 second)
   - Loads config from `config/air-executor.toml`
   - Starts `claude_wrapper.py` subprocess

2. **Wrapper initializes** (~2 seconds)
   - Wrapper sends "ready" event
   - DAG sends prompt to wrapper

3. **Claude responds** (~5-10 seconds)
   - Streaming events appear in logs
   - Text content extracted

4. **Completion** (~1 second)
   - Wrapper sends "run_completed"
   - Process exits gracefully
   - DAG marks task as success

**Total time:** ~10-15 seconds

### Success Indicators

✅ **Task shows green** (success status)
✅ **Logs contain:** "📋 CLAUDE'S RESPONSE"
✅ **Response text visible** in logs
✅ **No errors** in stderr

### Possible Issues

#### Issue 1: Config not found

**Log shows:**
```
RuntimeError: Failed to load config: Config file not found
```

**Solution:**
```bash
# Create config file
cp config/air-executor.example.toml config/air-executor.toml
# Restart Airflow scheduler
```

#### Issue 2: Import error (claude_code_sdk)

**Log shows:**
```
ModuleNotFoundError: No module named 'claude_code_sdk'
```

**Solution:**
```bash
source .venv/bin/activate
pip install claude-code-sdk
# Restart Airflow
```

#### Issue 3: Timeout

**Log shows:**
```
RuntimeError: Claude query timed out after 60 seconds
```

**Solution:**
```toml
# Edit config/air-executor.toml
[claude]
timeout_seconds = 120  # Increase to 2 minutes
```

#### Issue 4: Rate limit

**Log shows:**
```
limit_notice: rate limit reached
```

**This is normal!** The wrapper handles it gracefully and still completes.

---

## 📊 Viewing Results

### XCom (Cross-Communication)

Results are stored in XCom for downstream tasks:

1. Click on the task
2. Click **XCom** tab
3. You'll see:
   - `claude_response` - Full conversation text
   - `events_count` - Number of events received
   - `return_value` - Task result dictionary

### Task Instance Details

Click on task → **Details** tab to see:
- Start time
- End time
- Duration
- Task arguments
- Return value

---

## 🔄 Running Multiple Times

You can trigger the DAG multiple times:

1. Each trigger creates a new DAG run
2. Runs are independent (fresh sessions)
3. All logs are preserved
4. Run ID format: `manual__YYYY-MM-DDTHH:MM:SS+00:00`

**View all runs:**
- **Grid View** - Shows all runs as columns
- **List View** - Table format of all runs

---

## 🧪 Testing Different Prompts

To test with different prompts, you can:

### Option 1: Edit DAG (Quick Test)

```python
# airflow_dags/claude_query_sdk.py

# Change this line:
prompt = "hello, how old are you?"

# To:
prompt = "What is 2+2?"

# Then re-sync:
./airflow_dags/sync_to_airflow.sh
```

### Option 2: DAG Parameters (Advanced)

Create a parameterized DAG:

```python
def run_claude_query_sdk(**context):
    # Get prompt from DAG run config
    prompt = context['dag_run'].conf.get('prompt', 'hello, how old are you?')
```

Trigger with custom prompt:
```bash
airflow dags trigger claude_query_sdk \
  --conf '{"prompt": "What is Python?"}'
```

Or in UI:
1. Trigger DAG
2. Add JSON in **Configuration** field:
   ```json
   {"prompt": "What is Python?"}
   ```

---

## 📋 Pre-Flight Checklist

Before triggering, verify:

- [ ] Config file exists: `config/air-executor.toml`
- [ ] Paths are correct in config
- [ ] `claude-code-sdk` installed in venv
- [ ] `claude_wrapper.py` exists and is executable
- [ ] Airflow scheduler is running
- [ ] DAG appears in UI (not paused)

**Quick verify:**
```bash
# Check config
python -c "from air_executor.config import load_config; print(load_config())"

# Check DAG
airflow dags list | grep claude_query_sdk

# Check scheduler
ps aux | grep "airflow scheduler"
```

---

## 🎉 Success Criteria

Your E2E test is **successful** if:

1. ✅ DAG triggers without errors
2. ✅ Task completes in ~10-15 seconds
3. ✅ Task status shows **green/success**
4. ✅ Logs contain Claude's response
5. ✅ XCom has `claude_response` value
6. ✅ No timeout or import errors

---

## 📸 Expected Screenshots

### DAG List
```
┌─────────────────┬────────────┬──────────┐
│ DAG             │ Schedule   │ Status   │
├─────────────────┼────────────┼──────────┤
│ claude_query_sdk│ None       │ ⚪ Active │  ← Look for this
└─────────────────┴────────────┴──────────┘
```

### Grid View (After Trigger)
```
claude_query_sdk
├─ run_claude_query_sdk  🟢 Success  (12s)
```

### Logs
```
[2025-10-02 08:55:00] INFO - 🚀 Starting claude_wrapper.py
[2025-10-02 08:55:02] INFO - ✅ Wrapper ready, sending prompt...
[2025-10-02 08:55:05] INFO - 💬 Claude: I don't have a specific age...
[2025-10-02 08:55:10] INFO - ✅ Run completed successfully!
[2025-10-02 08:55:10] INFO - ━━━━━━━━━━━━━━━━━━━━━
[2025-10-02 08:55:10] INFO - 📋 CLAUDE'S RESPONSE
[2025-10-02 08:55:10] INFO - ━━━━━━━━━━━━━━━━━━━━━
[2025-10-02 08:55:10] INFO - [Full response text]
```

---

## 🔗 Quick Links

- **Airflow UI:** http://localhost:8080
- **DAG:** http://localhost:8080/dags/claude_query_sdk/grid
- **Docs:** `claudedocs/CLAUDE_SDK_SETUP.md`
- **Config:** `config/air-executor.toml`

---

## 💡 Tips

1. **Keep logs open** - Refresh to see real-time progress
2. **Check task duration** - Should be ~10-15s, not 60s (timeout)
3. **Use Grid View** - Best for monitoring single runs
4. **Use Graph View** - See task dependencies (single task here)
5. **Enable auto-refresh** - UI auto-updates run status

---

## 🎬 Ready to Test!

Everything is set up and ready. Just:

1. Open http://localhost:8080
2. Find `claude_query_sdk`
3. Click ▶️ Play button
4. Watch it run!
5. Check logs for Claude's response

**Good luck with your E2E test! 🚀**
