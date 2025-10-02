# Scripts Documentation

## DAG Management Scripts

### `sync_dags_to_airflow.sh`

Syncs DAG files from the project to Airflow and validates them.

**Usage:**
```bash
./scripts/sync_dags_to_airflow.sh
```

**What it does:**
1. Copies DAG files from `airflow_dags/` to `/home/rmondo/airflow/dags/`
2. Validates Python syntax for each DAG
3. Tests imports for each DAG
4. Shows registered DAGs in Airflow

**Files synced:**
- `claude_query_dag.py` - Simple Claude CLI wrapper
- `claude_query_sdk.py` - Claude SDK wrapper (reusable)
- `python_cleanup_dag.py` - Python artifacts cleanup

### `validate_dags.sh`

Comprehensive DAG validation tool with detailed checks.

**Usage:**
```bash
./scripts/validate_dags.sh
```

**Validation checks:**
1. Python syntax validation
2. Import resolution
3. DAG definition presence
4. Common issues detection:
   - Hardcoded paths
   - print() statements (should use logging)
   - Missing docstrings
5. Airflow parsing validation

**Output:**
- Detailed validation report for each DAG
- Summary of all DAGs
- List of registered DAGs in Airflow

### `sync_claude_wrapper_to_airflow.sh`

Syncs the Claude wrapper script to Airflow scripts directory.

**Usage:**
```bash
./scripts/sync_claude_wrapper_to_airflow.sh
```

**What it does:**
- Copies `claude_wrapper.py` to `/home/rmondo/airflow/scripts/`
- Sets executable permissions

**When to use:**
- After modifying `scripts/claude_wrapper.py`
- When fixing bugs in Claude SDK execution
- When adding new features to the wrapper

## Error Detection

### Common Issues

**1. Import Errors**
- **Symptom:** `ModuleNotFoundError` in Airflow logs
- **Detection:** `airflow dags list-import-errors`
- **Fix:** Ensure imports use correct paths or add path setup

**2. DAG Not Appearing**
- **Symptom:** DAG doesn't show in `airflow dags list`
- **Detection:** Check `airflow dags list-import-errors`
- **Fix:** Wait for scheduler refresh or restart scheduler

**3. Hardcoded Paths**
- **Symptom:** DAG works locally but fails in different environment
- **Detection:** `validate_dags.sh` warns about hardcoded paths
- **Fix:** Use config files or environment variables

### Validation Workflow

```bash
# 1. Validate DAGs before syncing
./scripts/validate_dags.sh

# 2. Sync to Airflow (with validation)
./scripts/sync_dags_to_airflow.sh

# 3. Check Airflow sees the DAGs
source .venv/bin/activate
airflow dags list | grep -E "claude|python_cleanup"

# 4. Check for import errors
airflow dags list-import-errors
```

## Quick Reference

### Check if DAG is registered
```bash
airflow dags list | grep python_cleanup
```

### Check DAG import errors
```bash
airflow dags list-import-errors
```

### Force DAG rescan
```bash
airflow dags reserialize
```

### Test DAG locally
```bash
cd /home/rmondo/airflow/dags
python python_cleanup_dag.py
```

### Trigger DAG
```bash
# Default (uses project root)
airflow dags trigger python_cleanup

# With custom directory
airflow dags trigger python_cleanup --conf '{"working_directory": "/path/to/repo"}'
```

## Architecture Notes

### SSOT (Single Source of Truth)
- `claude_query_sdk.py` contains `run_claude_query_sdk()` - the reusable function
- Other DAGs import and reuse this function
- No duplication of Claude SDK execution logic

### SRP (Single Responsibility Principle)
- `run_claude_query_sdk()` - Handles Claude wrapper execution
- `cleanup_python_artifacts()` - Provides domain-specific configuration
- Each function has one clear responsibility

## Troubleshooting

### DAG shows error in Airflow UI
1. Check logs: `airflow dags list-import-errors`
2. Run validation: `./scripts/validate_dags.sh`
3. Test import manually:
   ```bash
   cd /home/rmondo/airflow/dags
   python -c "from python_cleanup_dag import dag; print(dag.dag_id)"
   ```

### Changes not reflected
1. DAGs are scanned every ~30 seconds
2. Force rescan: `airflow dags reserialize`
3. Restart scheduler if needed

### Import path issues
- DAGs should be self-contained or use explicit path setup
- See `python_cleanup_dag.py` for example of path setup
