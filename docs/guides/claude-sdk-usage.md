# Claude SDK Integration - Quick Start

## ✅ Problem Solved

**Before:** `claude_query` DAG hung indefinitely (required TTY, blocked forever)

**After:** `claude_query_sdk` DAG runs cleanly (no TTY, auto-exits, returns results)

---

## 🚀 Quick Start

### 1. Install (Already Done)

```bash
source .venv/bin/activate
pip install claude-code-sdk  # ✅ Installed
```

### 2. Deploy DAG

```bash
# Validate and deploy
./scripts/quick_deploy_dag.sh airflow_dags/claude_query_sdk.py
```

### 3. Run in Airflow

1. Open http://localhost:8080
2. Find DAG: `claude_query_sdk`
3. Unpause (toggle switch)
4. Trigger (play button)
5. View logs to see Claude's response

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `airflow_dags/claude_query_sdk.py` | ✅ **NEW** Non-blocking DAG |
| `airflow_dags/claude_query_dag.py` | ❌ **OLD** Blocking DAG (deprecated) |
| `scripts/claude_wrapper.py` | JSON wrapper for claude_code_sdk |
| `scripts/test_claude_wrapper.py` | Local test script |
| `claudedocs/CLAUDE_SDK_SETUP.md` | Complete documentation |

---

## 🧪 Test Locally First

```bash
source .venv/bin/activate
python scripts/test_claude_wrapper.py
```

**Expected:**
```
✅ TEST PASSED
Response:
Hello from Airflow test!
```

---

## 🎯 How It Works

```
Airflow → claude_wrapper.py → claude_code_sdk → Claude CLI
         (JSON stdin/stdout)   (async Python)    (headless)
```

**Key features:**
- ✅ No TTY required
- ✅ Timeout protection (60s)
- ✅ Auto-exit on completion
- ✅ Streaming responses
- ✅ Auto-approve permissions

---

## 📚 Documentation

**Full guide:** `claudedocs/CLAUDE_SDK_SETUP.md`

**Topics covered:**
- Architecture overview
- Setup instructions
- DAG usage examples
- JSON command format
- Event streaming
- Troubleshooting
- Advanced features

---

## ⚡ Comparison

| Feature | OLD (claude -p) | NEW (claude_wrapper) |
|---------|----------------|---------------------|
| Blocking | ❌ Yes (hangs) | ✅ No |
| TTY required | ❌ Yes | ✅ No |
| Timeout | ❌ None | ✅ 60s |
| Auto-exit | ❌ No | ✅ Yes |
| Status | ❌ Deprecated | ✅ Recommended |

---

## 🎉 Ready to Use

The `claude_query_sdk` DAG is:
- ✅ Created
- ✅ Validated
- ✅ Deployed to Airflow
- ✅ Registered in DAG list
- ✅ Ready to trigger

**Just open Airflow UI and click play!**
