# ✅ E2E Test Ready!

## 🎉 Everything is Set Up

All systems are **GO** for Airflow E2E testing!

### Pre-flight Check: ALL PASSED ✅

```
✅ Config file exists
✅ Config loads successfully
✅ claude_code_sdk installed
✅ claude_wrapper.py exists and executable
✅ claude_query_sdk registered in Airflow
✅ claude_query_sdk is unpaused (ready to run)
✅ Airflow scheduler is running
```

---

## 🚀 How to Run E2E Test

### Step 1: Open Airflow UI

```
http://localhost:8080
```

### Step 2: Find the DAG

Look for: **`claude_query_sdk`**

Tags: `claude`, `sdk`, `non-blocking`

### Step 3: Trigger

Click the **▶️ Play button** → **Trigger DAG**

### Step 4: Watch Execution

- Task will turn **yellow** (running)
- After ~10-15 seconds, turns **green** (success)

### Step 5: View Logs

1. Click on the green task box
2. Click **Log** button
3. Scroll to find:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CLAUDE'S RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Claude's response to "hello, how old are you?"]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📋 What You'll See

### Expected Timeline

| Time | Event |
|------|-------|
| 0s | Task queued |
| 1s | Task starts, loads config |
| 2s | claude_wrapper.py starts |
| 3s | Wrapper sends "ready" |
| 4s | Prompt sent to Claude |
| 5-10s | Claude streaming response |
| 12s | Task completes ✅ |

### Expected Log Output

```
[INFO] 🚀 Starting claude_wrapper.py with prompt: hello, how old are you?
[INFO] 📨 Event: ready
[INFO] ✅ Wrapper ready, sending prompt...
[INFO] 📨 Event: stream
[INFO] 💬 Claude: I don't have a specific age...
[INFO] 📨 Event: run_completed
[INFO] ✅ Run completed successfully!
[INFO] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[INFO] 📋 CLAUDE'S RESPONSE
[INFO] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[INFO] [Full conversation text here]
[INFO] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ✅ Success Criteria

Your test **passes** if:

- [x] Task shows **green** (success)
- [x] Duration is **~10-15 seconds** (not 60s timeout)
- [x] Logs contain **📋 CLAUDE'S RESPONSE**
- [x] Response text is visible
- [x] No errors in logs

---

## 🔧 Troubleshooting (if needed)

### If Something Goes Wrong

**Run pre-flight check:**
```bash
./scripts/airflow_preflight_check.sh
```

**Check specific issues:**

| Issue | Solution |
|-------|----------|
| Config not found | `cp config/air-executor.example.toml config/air-executor.toml` |
| Module not found | `pip install claude-code-sdk` |
| DAG not visible | `./airflow_dags/sync_to_airflow.sh && airflow dags reserialize` |
| Task timeout | Increase timeout in `config/air-executor.toml` |

**View detailed guide:**
- `claudedocs/AIRFLOW_E2E_TEST_GUIDE.md` - Complete testing guide
- `claudedocs/CLAUDE_SDK_TROUBLESHOOTING.md` - Troubleshooting

---

## 📊 What This Tests

This E2E test validates:

1. ✅ **Config system** - Loads TOML config correctly
2. ✅ **Path resolution** - Finds wrapper and venv via config
3. ✅ **Wrapper execution** - Starts claude_wrapper.py successfully
4. ✅ **JSON communication** - Stdin/stdout works correctly
5. ✅ **Claude SDK** - claude_code_sdk functions properly
6. ✅ **Streaming** - Receives and parses stream events
7. ✅ **Timeout handling** - Completes before timeout
8. ✅ **Response extraction** - Captures Claude's text correctly
9. ✅ **Auto-exit** - Wrapper shuts down gracefully
10. ✅ **Airflow integration** - DAG runs successfully in Airflow

**This is a comprehensive end-to-end test of the entire stack!**

---

## 🎯 Quick Commands

```bash
# Pre-flight check
./scripts/airflow_preflight_check.sh

# Trigger via CLI (alternative to UI)
airflow dags trigger claude_query_sdk

# View latest log
find ~/airflow/logs/dag_id=claude_query_sdk -name "*.log" -type f | tail -1 | xargs cat

# Check status
airflow dags state claude_query_sdk <run_id>
```

---

## 🔗 Resources

- **Airflow UI:** http://localhost:8080
- **DAG Direct Link:** http://localhost:8080/dags/claude_query_sdk/grid
- **Test Guide:** `claudedocs/AIRFLOW_E2E_TEST_GUIDE.md`
- **Config Guide:** `claudedocs/CONFIG_USAGE_GUIDE.md`
- **SDK Setup:** `claudedocs/CLAUDE_SDK_SETUP.md`

---

## 🎬 You're Ready!

**Everything is configured and tested. Just:**

1. Open http://localhost:8080
2. Find `claude_query_sdk`
3. Click ▶️ and watch it run!

**Enjoy your E2E test! 🚀**

---

## 📸 Expected Result

After running, you should see:

```
DAG: claude_query_sdk
  └─ Task: run_claude_query_sdk [🟢 SUCCESS] (12.5s)

Logs:
  ✅ Config loaded
  ✅ Wrapper started
  ✅ Prompt sent
  ✅ Response received
  ✅ Task completed

XCom:
  claude_response: "I don't have a specific age..."
  events_count: 8
  status: "success"
```

**That's a successful E2E test! 🎉**
