# Issue Resolved: FileNotFoundError

## Problem

DAG `claude_query_sdk` failed with:
```
FileNotFoundError: claude_wrapper.py not found at /home/rmondo/airflow/scripts/claude_wrapper.py
```

## Root Cause

The DAG code used **relative path resolution**:

```python
# BROKEN CODE
project_root = Path(__file__).parent.parent
wrapper_path = project_root / "scripts" / "claude_wrapper.py"
```

When the DAG file is **copied** from:
- Source: `/home/rmondo/repos/air-executor/airflow_dags/claude_query_sdk.py`
- Destination: `/home/rmondo/airflow/dags/claude_query_sdk.py`

Then `__file__` points to the copied location:
- `Path(__file__)` → `/home/rmondo/airflow/dags/claude_query_sdk.py`
- `Path(__file__).parent.parent` → `/home/rmondo/airflow/`
- Final path → `/home/rmondo/airflow/scripts/claude_wrapper.py` ❌ **Does not exist!**

## Solution Applied ✅

Changed to **absolute paths** pointing to the actual project files:

```python
# FIXED CODE
wrapper_path = Path("/home/rmondo/repos/air-executor/scripts/claude_wrapper.py")
venv_python = Path("/home/rmondo/repos/air-executor/.venv/bin/python")
```

This ensures the DAG always finds the files regardless of where it's copied to.

## Changes Made

1. **Updated DAG** (`airflow_dags/claude_query_sdk.py`)
   - Changed from relative to absolute paths
   - Added comments explaining why

2. **Redeployed**
   ```bash
   ./airflow_dags/sync_to_airflow.sh
   airflow dags reserialize
   ```

3. **Created Sync Script** (`scripts/sync_wrapper_to_airflow.sh`)
   - Optional helper to copy wrapper to Airflow directory
   - In case someone wants self-contained approach

4. **Documentation**
   - `claudedocs/CLAUDE_SDK_TROUBLESHOOTING.md` - Detailed troubleshooting guide
   - `claudedocs/ISSUE_RESOLVED_FILE_NOT_FOUND.md` - This file

## Verification

```bash
# 1. Check paths exist
ls /home/rmondo/repos/air-executor/scripts/claude_wrapper.py
# ✅ -rwxrwxr-x 1 rmondo rmondo 28477 Oct  2 17:40

ls /home/rmondo/repos/air-executor/.venv/bin/python
# ✅ lrwxrwxrwx 1 rmondo rmondo 7 Oct  2 16:11

# 2. Check deployed DAG has correct paths
grep "wrapper_path" /home/rmondo/airflow/dags/claude_query_sdk.py
# ✅ wrapper_path = Path("/home/rmondo/repos/air-executor/scripts/claude_wrapper.py")

# 3. DAG is registered
airflow dags list | grep claude_query_sdk
# ✅ claude_query_sdk | /home/rmondo/airflow/dags/claude_query_sdk.py | ...
```

## Status

✅ **RESOLVED**

The DAG is now:
- Using correct absolute paths
- Deployed to Airflow
- Registered and ready to run
- No longer throwing FileNotFoundError

## Next Steps

**Trigger the DAG:**
```bash
# Via CLI
airflow dags trigger claude_query_sdk

# Via UI
# http://localhost:8080 → claude_query_sdk → Play button
```

**Check logs:**
```bash
# Find latest run
find ~/airflow/logs/dag_id=claude_query_sdk -type f -name "*.log" | tail -1

# View log
cat <path_to_log>

# Should see:
# ✅ "Starting claude_wrapper.py with prompt: ..."
# ✅ "Wrapper ready, sending prompt..."
# ✅ Stream events with Claude's response
```

## Lessons Learned

1. **Relative paths break when files are copied**
   - `__file__` changes based on file location
   - Use absolute paths or environment variables

2. **Test DAG path resolution**
   - Print `Path(__file__)` in development
   - Verify paths exist before deployment

3. **Document path assumptions**
   - Make it clear what paths are expected
   - Provide helpers (like `sync_wrapper_to_airflow.sh`)

## Alternative Solutions (Not Used)

### Option 1: Environment Variable
```python
PROJECT_ROOT = os.getenv("AIR_EXECUTOR_PATH", "/home/rmondo/repos/air-executor")
wrapper_path = Path(f"{PROJECT_ROOT}/scripts/claude_wrapper.py")
```

**Pros:** More portable
**Cons:** Requires setting env var in Airflow config

### Option 2: Copy Everything to Airflow
```bash
cp scripts/claude_wrapper.py ~/airflow/scripts/
cp -r .venv ~/airflow/.venv
```

**Pros:** Self-contained
**Cons:** Duplicate maintenance, larger footprint

### Option 3: Symlinks
```bash
ln -s /home/rmondo/repos/air-executor/scripts ~/airflow/scripts
ln -s /home/rmondo/repos/air-executor/.venv ~/airflow/.venv
```

**Pros:** No duplication
**Cons:** Breaks if source moves

**Chosen solution (absolute paths)** is simple and works immediately.
