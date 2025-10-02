# DAG Sync Script - Automated Detection and Fixes

## Problem Summary

**What caused `commit_and_push` DAG to be invisible:**

1. **Stale Metadata**: Old `claude_query_sdk` DAG definition existed in Airflow's metastore even after we removed it from the source code
2. **Paused by Default**: New DAGs are created in paused state by default
3. **No Auto-Cleanup**: Manual intervention was required to clean up stale metadata

## Solution: Unified Sync Script

The improved `sync_dags_to_airflow.sh` now automatically:

### ✅ Auto-Detection Features
- **Auto-discovery**: Finds all `.py` files automatically (no hardcoded lists)
- **Stale DAG Detection**: Scans Airflow metastore and identifies DAGs that:
  - Reference deleted files
  - Are defined in files that no longer contain them
- **Validation**: Syntax and import checks before deployment

### ✅ Auto-Fix Features
- **Stale Cleanup** (`--cleanup`): Automatically removes stale DAG metadata
- **Auto-Unpause** (`--auto-unpause`): Automatically activates new DAGs
- **File Cleanup**: Removes synced files that no longer exist in source

## Usage

### Basic Sync (Copy Mode)
```bash
./scripts/sync_dags_to_airflow.sh
```

### Development Mode (Symlink + Auto-unpause)
```bash
./scripts/sync_dags_to_airflow.sh --symlink --auto-unpause
```

### Full Cleanup (Recommended After Changes)
```bash
./scripts/sync_dags_to_airflow.sh --cleanup --auto-unpause
```

### Check What Would Change (Dry Run)
```bash
./scripts/sync_dags_to_airflow.sh --dry-run
```

## Options

| Option | Description |
|--------|-------------|
| `--symlink` | Create symlinks instead of copying (changes auto-sync, good for dev) |
| `--copy` | Copy files (default, safe for production) |
| `--auto-unpause` | Automatically unpause new/paused DAGs |
| `--cleanup` | Clean up stale DAG metadata from database |
| `--dry-run` | Show what would be done without executing |
| `--help` | Show help message |

## What Gets Cleaned Up

When using `--cleanup`, the script removes:

1. **Stale DAG Entries**: DAGs in database but not in source files
2. **Orphaned Task Instances**: Task runs for deleted DAGs
3. **Old DAG Runs**: Execution history for removed DAGs
4. **Stale Logs**: Log entries for non-existent DAGs
5. **Deleted Files**: Synced files that no longer exist in source

## Example Output

```bash
$ ./scripts/sync_dags_to_airflow.sh --cleanup --auto-unpause

📦 Syncing DAG files to Airflow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Auto-discovering DAG files...
Found 5 files:
   - air_executor_integration.py
   - claude_query_sdk.py
   - commit_and_push_dag.py
   - hybrid_control_example.py
   - python_cleanup_dag.py

📁 Syncing files...
✓ Copied: commit_and_push_dag.py
✓ Copied: python_cleanup_dag.py
...

🔍 Detecting stale DAG metadata...
Found 1 stale DAG(s): claude_query_sdk
Cleaning up...
  ✓ Deleted claude_query_sdk: 1 DAG, 6 runs, 6 tasks, 16 logs
✅ Cleaned up 1 stale DAG(s)

🔓 Auto-unpausing DAGs...
Found 2 paused DAG(s)
  ✓ Unpaused: commit_and_push
  ✓ Unpaused: python_cleanup
✅ Unpaused 2 DAG(s)

✅ Sync complete!
```

## Why We Consolidated Scripts

Previously had two scripts:
- `scripts/sync_dags_to_airflow.sh` - Validation-focused
- `airflow_dags/sync_to_airflow.sh` - Symlink-focused

**Problem**: Duplication, different features, confusing

**Solution**: Unified script with all features:
- Auto-discovery (no hardcoded lists)
- Symlink OR copy mode
- Validation
- Auto-cleanup
- Auto-unpause

## Best Practices

### Development Workflow
```bash
# Initial setup - use symlinks for auto-sync
./scripts/sync_dags_to_airflow.sh --symlink --auto-unpause

# Work on DAGs (changes auto-sync via symlinks)
# ... edit files ...

# Periodically clean up stale metadata
./scripts/sync_dags_to_airflow.sh --cleanup
```

### Production Workflow
```bash
# Sync with validation and cleanup
./scripts/sync_dags_to_airflow.sh --copy --cleanup --auto-unpause

# Verify DAGs are active
airflow dags list | grep -E '(python_cleanup|commit_and_push)'
```

### After Major Changes
```bash
# Full cleanup after refactoring DAGs
./scripts/sync_dags_to_airflow.sh --cleanup --auto-unpause

# Restart scheduler for fresh parse
# (handled by systemd or manual restart)
```

## Troubleshooting

### DAG Not Appearing in UI

1. **Check if synced**:
   ```bash
   ls ~/airflow/dags/ | grep your_dag.py
   ```

2. **Check if paused**:
   ```bash
   airflow dags list | grep your_dag
   # Last column shows pause status (False = active)
   ```

3. **Unpause if needed**:
   ```bash
   ./scripts/sync_dags_to_airflow.sh --auto-unpause
   ```

4. **Clean stale metadata**:
   ```bash
   ./scripts/sync_dags_to_airflow.sh --cleanup
   ```

### Stale DAGs Persisting

If old DAGs remain after cleanup:
```bash
# Manual database cleanup
source .venv/bin/activate
python3 << 'EOF'
from airflow import settings
from airflow.models import DagModel
session = settings.Session()
dag = session.query(DagModel).filter(DagModel.dag_id == 'old_dag_id').first()
if dag:
    session.delete(dag)
    session.commit()
    print(f"Deleted {dag.dag_id}")
session.close()
EOF
```

### Validation Failures

Check syntax and imports:
```bash
# Validate locally
source .venv/bin/activate
python3 -m py_compile airflow_dags/your_dag.py

# Check imports
cd airflow_dags
python3 -c "import your_dag"
```

## Migration Guide

### From Old Scripts

**Before** (hardcoded list):
```bash
# Had to manually update file list
DAG_FILES=(
    "dag1.py"
    "dag2.py"
)
```

**After** (auto-discovery):
```bash
# Just add/remove files, script auto-detects
./scripts/sync_dags_to_airflow.sh
```

### From Manual Management

**Before**:
1. Copy files manually
2. Check Airflow UI
3. Notice missing DAG
4. Manually unpause
5. Manually clean stale entries

**After**:
```bash
./scripts/sync_dags_to_airflow.sh --cleanup --auto-unpause
# Everything handled automatically
```

## Technical Details

### Stale Detection Algorithm

1. Query all DAGs from Airflow metastore
2. For each DAG:
   - Check if source file exists
   - Check if file still defines the DAG ID
   - Mark as stale if either check fails
3. Delete stale entries in order:
   - Task instances → DAG runs → Logs → DAG model

### Auto-Unpause Logic

1. Query all paused DAGs
2. Set `is_paused = False` for each
3. Commit changes to metastore
4. Scheduler picks up changes automatically

## Future Improvements

- [ ] Add git hook for automatic sync on commit
- [ ] Add pre-commit validation
- [ ] Support for DAG versioning
- [ ] Rollback capability
- [ ] Sync performance metrics
