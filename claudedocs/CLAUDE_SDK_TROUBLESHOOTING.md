# Claude SDK Troubleshooting

## Issue: FileNotFoundError - claude_wrapper.py not found

### Symptom
```
FileNotFoundError: claude_wrapper.py not found at /home/rmondo/airflow/scripts/claude_wrapper.py
```

### Root Cause
When DAG files are copied to `~/airflow/dags/`, the code uses `Path(__file__).parent.parent` which resolves to `/home/rmondo/airflow/` instead of the project directory `/home/rmondo/repos/air-executor/`.

### Solution ✅

**Option 1: Use Absolute Paths (Implemented)**

Updated DAG to use hardcoded absolute paths:

```python
# airflow_dags/claude_query_sdk.py
wrapper_path = Path("/home/rmondo/repos/air-executor/scripts/claude_wrapper.py")
venv_python = Path("/home/rmondo/repos/air-executor/.venv/bin/python")
```

**Pros:**
- ✅ Works immediately
- ✅ Points to actual project files
- ✅ No extra sync needed

**Cons:**
- ⚠️  Not portable to other machines (hardcoded path)

**Option 2: Copy Wrapper to Airflow (Fallback)**

Copy wrapper to Airflow's directory structure:

```bash
# Run once
./scripts/sync_wrapper_to_airflow.sh
```

This creates:
- `~/airflow/scripts/claude_wrapper.py`

**Pros:**
- ✅ Self-contained in Airflow directory
- ✅ Portable (uses relative paths)

**Cons:**
- ⚠️  Need to re-sync when wrapper changes
- ⚠️  Duplicate file maintenance

---

## Current Setup (After Fix)

### File Locations

```
/home/rmondo/repos/air-executor/
├── scripts/
│   ├── claude_wrapper.py              # ✅ Original (used by DAG)
│   └── sync_wrapper_to_airflow.sh     # Helper script
├── .venv/bin/python                   # ✅ Used by DAG
└── airflow_dags/
    └── claude_query_sdk.py            # Uses absolute paths

/home/rmondo/airflow/
├── dags/
│   └── claude_query_sdk.py            # Copied from above
└── scripts/
    └── claude_wrapper.py              # ⚠️ Optional backup copy
```

### Path Resolution in DAG

```python
# BEFORE (Broken)
project_root = Path(__file__).parent.parent  # → /home/rmondo/airflow/
wrapper_path = project_root / "scripts" / "claude_wrapper.py"
# → /home/rmondo/airflow/scripts/claude_wrapper.py ❌

# AFTER (Fixed)
wrapper_path = Path("/home/rmondo/repos/air-executor/scripts/claude_wrapper.py")
venv_python = Path("/home/rmondo/repos/air-executor/.venv/bin/python")
# → Points to actual files ✅
```

---

## Verification Steps

### 1. Check Paths Exist

```bash
# Verify wrapper
ls -la /home/rmondo/repos/air-executor/scripts/claude_wrapper.py

# Verify Python venv
ls -la /home/rmondo/repos/air-executor/.venv/bin/python

# Both should exist and be accessible
```

### 2. Test Locally

```bash
source .venv/bin/activate
python scripts/test_claude_wrapper.py
```

**Expected:**
```
✅ TEST PASSED
```

### 3. Check Airflow Logs

```bash
# Find latest log
find ~/airflow/logs/dag_id=claude_query_sdk -type f -name "*.log" | tail -1

# View it
cat <path_to_log>

# Should NOT see:
# ❌ FileNotFoundError: claude_wrapper.py not found
```

### 4. Trigger DAG

```bash
# Via CLI
airflow dags trigger claude_query_sdk

# Check status
airflow dags state claude_query_sdk <run_id>
```

---

## Other Common Issues

### Issue: ModuleNotFoundError: claude_code_sdk

**Symptom:**
```
ModuleNotFoundError: No module named 'claude_code_sdk'
```

**Solution:**
```bash
source .venv/bin/activate
pip install claude-code-sdk
```

### Issue: Permission Denied

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/home/rmondo/repos/air-executor/scripts/claude_wrapper.py'
```

**Solution:**
```bash
chmod +x /home/rmondo/repos/air-executor/scripts/claude_wrapper.py
```

### Issue: Timeout After 60 Seconds

**Symptom:**
```
RuntimeError: Claude query timed out after 60 seconds
```

**Solutions:**

1. **Increase timeout** in DAG:
```python
# In claude_query_sdk.py
return_code = process.wait(timeout=300)  # 5 minutes
```

2. **Check for rate limits:**
Look for `limit_notice` events in the stream

3. **Simplify prompt:**
Complex queries take longer

### Issue: No Response Text

**Symptom:**
DAG completes but `claude_response` is empty

**Debug:**
```python
# Add debug logging in DAG
if event["event"] == "stream":
    print(f"DEBUG: Full event: {json.dumps(event, indent=2)}")
```

Look for where text appears in the payload structure.

---

## Deployment Checklist

When deploying `claude_query_sdk`:

- [ ] `claude-code-sdk` installed in venv
- [ ] `claude_wrapper.py` exists and is executable
- [ ] Absolute paths in DAG are correct for your system
- [ ] DAG validates successfully
- [ ] Local test passes (`scripts/test_claude_wrapper.py`)
- [ ] DAG synced to Airflow
- [ ] DAG appears in `airflow dags list`
- [ ] Test trigger succeeds

---

## Quick Fix Commands

```bash
# Fix paths
ls /home/rmondo/repos/air-executor/scripts/claude_wrapper.py
ls /home/rmondo/repos/air-executor/.venv/bin/python

# Fix permissions
chmod +x /home/rmondo/repos/air-executor/scripts/claude_wrapper.py

# Install SDK
source .venv/bin/activate
pip install claude-code-sdk

# Redeploy DAG
./airflow_dags/sync_to_airflow.sh
source .venv/bin/activate
airflow dags reserialize

# Test
airflow dags trigger claude_query_sdk
```

---

## Making It Portable

To make the DAG work on different machines, use environment variables:

```python
# airflow_dags/claude_query_sdk.py
import os

# Use environment variable with fallback
PROJECT_ROOT = os.getenv(
    "AIR_EXECUTOR_PATH",
    "/home/rmondo/repos/air-executor"
)

wrapper_path = Path(f"{PROJECT_ROOT}/scripts/claude_wrapper.py")
venv_python = Path(f"{PROJECT_ROOT}/.venv/bin/python")
```

Then set in Airflow:

```bash
# In airflow.cfg or environment
export AIR_EXECUTOR_PATH="/path/to/air-executor"
```

Or add to DAG default_args:

```python
default_args = {
    'env': {
        'AIR_EXECUTOR_PATH': '/home/rmondo/repos/air-executor'
    }
}
```

---

## Summary

✅ **Fixed:** Changed from relative to absolute paths
✅ **Status:** DAG now finds wrapper and venv correctly
✅ **Ready:** Can trigger and run successfully

**Key learning:** When DAGs are copied to `~/airflow/dags/`, `__file__` changes, so use absolute paths or environment variables.
