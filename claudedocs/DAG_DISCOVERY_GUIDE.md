# DAG Discovery Guide: How to Make DAGs Appear Instantly

## Root Cause Analysis

### What Happened?
The `claude_query` DAG took several minutes to appear because:

**The scheduler scans for new DAGs every 5 minutes by default** (`dag_dir_list_interval = 300` seconds)

### Timeline
1. ✅ DAG file created at `~/airflow/dags/claude_query_dag.py`
2. ✅ DAG syntax was valid (no import errors)
3. ⏳ **Waited ~5 minutes** for scheduler to scan
4. ✅ DAG discovered after running `airflow dags reserialize`

---

## How to Avoid Waiting (3 Solutions)

### Solution 1: Force Immediate Discovery ⚡ (Recommended)

After creating/updating a DAG, force immediate discovery:

```bash
source .venv/bin/activate
airflow dags reserialize
```

This tells Airflow to scan for DAGs **immediately** instead of waiting 5 minutes.

### Solution 2: Use the Validation Script 🔍 (Best Practice)

We created a validation script that:
- ✅ Validates DAG syntax
- ✅ Forces immediate discovery
- ✅ Checks registration
- ✅ Provides next steps

**Usage:**
```bash
source .venv/bin/activate
python scripts/validate_dag.py airflow_dags/your_dag.py
```

**Example Output:**
```
============================================================
🚀 DAG Validation and Discovery Tool
============================================================
🔍 Validating claude_query_dag.py...
✅ Valid! Found DAG(s): claude_query

============================================================
🔄 Forcing DAG discovery...
✅ DAG reserialize completed

============================================================
🔎 Checking if 'claude_query' is registered in Airflow...
✅ DAG 'claude_query' is registered!

============================================================
📋 Next Steps:
============================================================
1. Copy DAG to Airflow: ./airflow_dags/sync_to_airflow.sh
2. Access Airflow UI: http://localhost:8080
3. Find DAG: 'claude_query'
4. Unpause DAG: Toggle the switch in UI
5. Trigger DAG: Click the play button
============================================================
```

### Solution 3: Reduce Scan Interval (System-Wide Change)

Edit `~/airflow/airflow.cfg`:

```ini
[scheduler]
# Reduce from 300 to 30 seconds (faster discovery, more CPU)
dag_dir_list_interval = 30
```

**Trade-offs:**
- ✅ Faster discovery (30 seconds instead of 5 minutes)
- ❌ More CPU usage (scheduler scans more frequently)

**Recommended for:**
- Development environments
- Rapid DAG iteration

**Not recommended for:**
- Production (use default 300 seconds)
- Systems with 100+ DAGs

---

## Complete Workflow: Creating a New DAG

### Quick Reference

```bash
# 1. Create DAG file
vim airflow_dags/my_new_dag.py

# 2. Validate and discover (ONE COMMAND!)
source .venv/bin/activate
python scripts/validate_dag.py airflow_dags/my_new_dag.py

# 3. Sync to Airflow
./airflow_dags/sync_to_airflow.sh

# 4. Open Airflow UI
# http://localhost:8080
```

### Detailed Steps

#### Step 1: Create DAG File

```python
# airflow_dags/my_new_dag.py
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 10, 2),
}

with DAG(
    'my_new_dag',
    default_args=default_args,
    description='My new DAG',
    schedule=None,
    catchup=False,
    tags=['custom'],
) as dag:

    task = BashOperator(
        task_id='my_task',
        bash_command='echo "Hello World"',
    )
```

#### Step 2: Validate Locally (Catch Errors Early)

```bash
# Test import in Python
source .venv/bin/activate
python -c "import airflow_dags.my_new_dag; print('✅ Valid!')"

# Or use validation script
python scripts/validate_dag.py airflow_dags/my_new_dag.py
```

#### Step 3: Sync to Airflow

```bash
./airflow_dags/sync_to_airflow.sh
```

#### Step 4: Force Discovery (Don't Wait!)

```bash
source .venv/bin/activate
airflow dags reserialize
```

#### Step 5: Verify Registration

```bash
# Check if DAG is listed
airflow dags list | grep my_new_dag

# Should show:
# my_new_dag | /home/rmondo/airflow/dags/my_new_dag.py | airflow | True | ...
```

#### Step 6: Unpause and Trigger

```bash
# Unpause (enable DAG)
airflow dags unpause my_new_dag

# Trigger a run
airflow dags trigger my_new_dag
```

---

## Common Issues and Solutions

### Issue 1: DAG Not Appearing After 10+ Minutes

**Symptoms:**
- DAG file in `~/airflow/dags/`
- No import errors
- Still not showing in UI

**Diagnosis:**
```bash
# Check for import errors
airflow dags list-import-errors

# Check scheduler logs
tail -50 ~/airflow/logs/scheduler/latest/*.log
```

**Solutions:**
1. Check DAG has valid DAG object (not just Python file)
2. Restart scheduler: `./scripts/stop-airflow.sh && ./scripts/start-airflow.sh`
3. Check file permissions: `ls -la ~/airflow/dags/`

### Issue 2: DAG Shows Import Error

**Symptoms:**
- DAG appears with red "Import Error" badge
- Not executable

**Diagnosis:**
```bash
# See specific error
airflow dags list-import-errors

# Test import manually
cd ~/airflow/dags
python -c "import my_dag_file"
```

**Common Causes:**
- Missing dependency/import
- Deprecated import path (e.g., old BashOperator import)
- Syntax error
- Circular import

**Solutions:**
1. Fix import error in DAG file
2. Update imports to modern paths:
   ```python
   # ❌ Old (deprecated)
   from airflow.operators.bash import BashOperator

   # ✅ New (Airflow 3.x)
   from airflow.providers.standard.operators.bash import BashOperator
   ```
3. Re-sync and reserialize

### Issue 3: DAG Appears but is Paused

**Symptoms:**
- DAG visible in UI
- Toggle switch is OFF (grey)
- Cannot trigger

**Solution:**
```bash
# Unpause via CLI
airflow dags unpause my_dag_id

# Or click toggle in UI
```

---

## Best Practices

### ✅ DO

1. **Validate before deploying**
   ```bash
   python scripts/validate_dag.py airflow_dags/my_dag.py
   ```

2. **Force discovery after sync**
   ```bash
   airflow dags reserialize
   ```

3. **Use modern imports**
   ```python
   from airflow.providers.standard.operators.bash import BashOperator
   ```

4. **Test DAG locally first**
   ```bash
   python -c "import airflow_dags.my_dag"
   ```

5. **Use descriptive DAG IDs**
   ```python
   dag_id='data_pipeline_daily'  # Good
   dag_id='dag1'                 # Bad
   ```

### ❌ DON'T

1. **Don't wait 5 minutes** - use `airflow dags reserialize`

2. **Don't skip validation** - catch errors before deploying

3. **Don't use deprecated imports** - update to Airflow 3.x paths

4. **Don't restart Airflow for every change** - use reserialize instead

5. **Don't commit broken DAGs** - validate first

---

## Quick Commands Reference

```bash
# Validate DAG
python scripts/validate_dag.py airflow_dags/my_dag.py

# Force discovery (INSTANT!)
airflow dags reserialize

# List all DAGs
airflow dags list

# Check import errors
airflow dags list-import-errors

# Unpause DAG
airflow dags unpause my_dag_id

# Trigger DAG
airflow dags trigger my_dag_id

# Check DAG info
airflow dags show my_dag_id

# Test specific task
airflow tasks test my_dag_id my_task_id 2025-10-02
```

---

## Development Workflow Optimization

### Fast Iteration Cycle

```bash
# 1. Make DAG changes
vim airflow_dags/my_dag.py

# 2. Validate + Discover (one command!)
python scripts/validate_dag.py airflow_dags/my_dag.py

# 3. Sync
./airflow_dags/sync_to_airflow.sh

# 4. Test
airflow tasks test my_dag_id my_task_id 2025-10-02

# Total time: ~10 seconds (vs 5+ minutes waiting!)
```

### Automation Script

Create `scripts/quick_deploy_dag.sh`:

```bash
#!/bin/bash
# Quick DAG deployment with validation

DAG_FILE=$1

if [ -z "$DAG_FILE" ]; then
    echo "Usage: ./scripts/quick_deploy_dag.sh <dag_file>"
    exit 1
fi

source .venv/bin/activate

# Validate
python scripts/validate_dag.py "$DAG_FILE" || exit 1

# Sync
./airflow_dags/sync_to_airflow.sh

# Force discovery
airflow dags reserialize

echo "✅ DAG deployed and discovered!"
```

Usage:
```bash
./scripts/quick_deploy_dag.sh airflow_dags/my_dag.py
```

---

## Summary

### The Problem
- Default scan interval: **5 minutes**
- No immediate feedback on DAG validity
- Unclear when DAG will appear

### The Solution
1. **Use validation script** - catch errors early
2. **Force reserialize** - instant discovery
3. **Follow workflow** - consistent, reliable process

### Time Savings
- ❌ Before: 5+ minutes per DAG deployment
- ✅ After: ~10 seconds per DAG deployment

**That's a 30x speedup! 🚀**
