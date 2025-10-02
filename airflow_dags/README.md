# Airflow DAGs for Air-Executor

This directory contains Airflow DAG definitions that integrate with Air-Executor.

## 📁 Directory Structure

```
airflow_dags/
├── README.md                       # This file
├── air_executor_integration.py     # Basic integration DAG
├── hybrid_control_example.py       # Hybrid control flow example
└── sync_to_airflow.sh             # Deployment script
```

## 🔄 Deployment

### Development (Local)

**Symlink Approach** (Recommended for development):
```bash
# One-time setup: Link this directory to Airflow's dags folder
ln -sf ~/repos/air-executor/airflow_dags/* ~/airflow/dags/

# Changes to files here are immediately visible to Airflow
```

**Copy Approach** (Manual sync):
```bash
# Use the sync script
./sync_to_airflow.sh

# Or manually copy
cp *.py ~/airflow/dags/
```

### Production

**Option 1: Git-Sync Sidecar**
- Airflow runs a git-sync container that automatically pulls DAGs from git repo
- Most common production pattern

**Option 2: CI/CD Pipeline**
```bash
# In your CI/CD pipeline
git checkout main
cp airflow_dags/*.py /airflow/dags/
airflow dags reserialize
```

## 🎯 Best Practices

### Version Control
- ✅ Keep DAG source code in git (this directory)
- ✅ Track changes, create branches, review via PRs
- ❌ Never edit files directly in `~/airflow/dags/`

### Development Workflow
```bash
# 1. Edit DAG in git repo
vim ~/repos/air-executor/airflow_dags/my_dag.py

# 2. Commit changes
git add airflow_dags/my_dag.py
git commit -m "Update DAG logic"

# 3. Sync to Airflow (if not using symlinks)
./airflow_dags/sync_to_airflow.sh

# 4. Test in Airflow UI
# DAG will refresh within ~30 seconds
```

### Testing
```bash
# Test DAG for syntax errors
airflow dags list-import-errors

# Test specific DAG
airflow dags test air_executor_demo 2025-10-02

# Test specific task
airflow tasks test air_executor_demo create_job 2025-10-02
```

## 🔧 Configuration

### Airflow DAGs Folder
Default location: `~/airflow/dags/`

To change:
```bash
# Edit ~/airflow/airflow.cfg
dags_folder = /path/to/your/dags
```

### Multiple DAG Sources
You can configure multiple DAG folders:
```python
# ~/airflow/airflow.cfg
dags_folder = /home/rmondo/airflow/dags
dag_discovery_safe_mode = False
```

Then use symlinks:
```bash
ln -s ~/repos/air-executor/airflow_dags ~/airflow/dags/air_executor
ln -s ~/repos/other-project/dags ~/airflow/dags/other_project
```

## 📚 Available DAGs

### air_executor_demo
**File:** `air_executor_integration.py`

Basic integration showing:
- How to create Air-Executor jobs from Airflow
- PythonSensor for monitoring job completion
- XCom for passing data between tasks

**Trigger:**
```bash
airflow dags trigger air_executor_demo
```

### hybrid_control_flow
**File:** `hybrid_control_example.py`

Advanced example demonstrating:
- Airflow preparation phase
- Handoff to Air-Executor for dynamic work
- Air-Executor discovers and queues tasks dynamically
- Control returns to Airflow for post-processing

**Trigger:**
```bash
airflow dags trigger hybrid_control_flow
```

## 🚀 Quick Start

```bash
# Setup symlinks (one-time)
cd ~/repos/air-executor/airflow_dags
chmod +x sync_to_airflow.sh
./sync_to_airflow.sh --symlink

# Start services
cd ~/repos/air-executor
./start-dev.sh              # Air-Executor manager
./start-airflow.sh          # Airflow standalone

# Access Airflow UI
open http://localhost:8080
# Login with credentials from ~/airflow/simple_auth_manager_passwords.json.generated
```

## 📖 Documentation

See the main docs directory for more information:
- `AIRFLOW_INTEGRATION.md` - Integration strategies
- `HYBRID_CONTROL_FLOW.md` - Control flow patterns
- `AIRFLOW_VISIBILITY_SOLUTIONS.md` - Monitoring approaches
- `QUICK_ANSWERS.md` - FAQ and quick reference
