# 🗂️ DAG Version Control Best Practices

## 🎯 The Problem

Airflow DAGs are Python files that live in `~/airflow/dags/`, which is **not a git repository**. This means:
- ❌ No version history
- ❌ No code review process
- ❌ No rollback capability
- ❌ No team collaboration tracking

## ✅ The Solution

Keep DAG source code in a **git-tracked directory** and sync to Airflow.

---

## 📁 Recommended Structure

```
air-executor/                    # Git repository root
├── airflow_dags/                # DAG source code (version controlled)
│   ├── README.md
│   ├── sync_to_airflow.sh       # Deployment script
│   ├── air_executor_integration.py
│   └── hybrid_control_example.py
├── src/                         # Air-Executor source
├── tests/                       # Tests
└── ...

~/airflow/                       # Airflow home (NOT git repo)
├── dags/                        # Where Airflow reads DAGs
│   ├── air_executor_integration.py  ← Symlink or copy from git repo
│   └── hybrid_control_example.py    ← Symlink or copy from git repo
├── airflow.db                   # SQLite database
└── airflow.cfg                  # Configuration
```

---

## 🔄 Deployment Strategies

### Strategy 1: Symlinks (Recommended for Development)

**Setup (one-time):**
```bash
cd ~/repos/air-executor/airflow_dags
./sync_to_airflow.sh --symlink
```

**Workflow:**
```bash
# 1. Edit DAG in git repo
vim ~/repos/air-executor/airflow_dags/my_dag.py

# 2. Changes are immediately visible to Airflow (symlink auto-syncs!)
# Wait ~30 seconds for Airflow to detect changes

# 3. Commit to git
git add airflow_dags/my_dag.py
git commit -m "Update DAG logic"
```

**Pros:**
- ✅ Automatic sync (no manual deployment step)
- ✅ Fast iteration during development
- ✅ Always in sync with git repo

**Cons:**
- ⚠️ Not suitable for production (security/stability concerns)
- ⚠️ Accidental uncommitted changes visible to Airflow

### Strategy 2: Manual Copy (Safe for All Environments)

**Setup:**
```bash
cd ~/repos/air-executor/airflow_dags
./sync_to_airflow.sh --copy
```

**Workflow:**
```bash
# 1. Edit DAG in git repo
vim ~/repos/air-executor/airflow_dags/my_dag.py

# 2. Commit to git FIRST
git add airflow_dags/my_dag.py
git commit -m "Update DAG logic"

# 3. Deploy to Airflow
./airflow_dags/sync_to_airflow.sh
```

**Pros:**
- ✅ Explicit deployment step (safer)
- ✅ Only committed code reaches Airflow
- ✅ Works in production

**Cons:**
- ⚠️ Manual step required
- ⚠️ Can forget to deploy

### Strategy 3: Git-Sync (Production Standard)

**How it works:**
- Airflow runs a sidecar container that continuously pulls from git
- DAGs auto-sync when you push to git repo

**Example (Kubernetes):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: airflow-scheduler
spec:
  template:
    spec:
      containers:
      - name: scheduler
        image: apache/airflow:2.7.0
        volumeMounts:
        - name: dags
          mountPath: /opt/airflow/dags

      - name: git-sync
        image: registry.k8s.io/git-sync/git-sync:v3.6.3
        env:
        - name: GIT_SYNC_REPO
          value: "https://github.com/your-org/airflow-dags.git"
        - name: GIT_SYNC_BRANCH
          value: "main"
        - name: GIT_SYNC_ROOT
          value: "/git"
        - name: GIT_SYNC_DEST
          value: "dags"
        - name: GIT_SYNC_WAIT
          value: "60"  # Sync every 60 seconds
        volumeMounts:
        - name: dags
          mountPath: /git

      volumes:
      - name: dags
        emptyDir: {}
```

**Pros:**
- ✅ Fully automated
- ✅ Production-grade
- ✅ Multi-environment support (dev/staging/prod branches)

**Cons:**
- ⚠️ Requires Kubernetes or Docker Compose setup
- ⚠️ More complex infrastructure

### Strategy 4: CI/CD Pipeline (Enterprise)

**Workflow:**
```yaml
# .github/workflows/deploy-dags.yml
name: Deploy DAGs

on:
  push:
    branches: [main]
    paths:
      - 'airflow_dags/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Airflow
        run: |
          scp airflow_dags/*.py airflow-server:/opt/airflow/dags/
          ssh airflow-server 'airflow dags reserialize'
```

**Pros:**
- ✅ Automated on git push
- ✅ Can include testing/linting
- ✅ Audit trail via CI/CD logs

---

## 🛠️ Development Workflow

### Daily Development

```bash
# Morning: Start services
cd ~/repos/air-executor
./start-dev.sh              # Air-Executor
./start-airflow.sh          # Airflow

# Work on DAGs
vim airflow_dags/my_dag.py

# If using symlinks: changes auto-visible to Airflow
# If using copy: deploy manually
./airflow_dags/sync_to_airflow.sh

# Test in Airflow UI (http://localhost:8080)
# Trigger DAG, check logs

# Commit when working
git add airflow_dags/my_dag.py
git commit -m "Add data processing DAG"
git push
```

### Testing DAGs Locally

```bash
# Check for syntax errors
airflow dags list-import-errors

# Test DAG parsing
python airflow_dags/my_dag.py

# Test DAG execution (dry run)
airflow dags test my_dag 2025-10-02

# Test specific task
airflow tasks test my_dag my_task 2025-10-02
```

### Code Review Process

```bash
# Create feature branch
git checkout -b feature/new-etl-dag

# Develop DAG
vim airflow_dags/etl_pipeline.py
git add airflow_dags/etl_pipeline.py
git commit -m "Add ETL pipeline DAG"

# Push and create PR
git push origin feature/new-etl-dag
# Create PR on GitHub/GitLab

# After approval, merge to main
git checkout main
git merge feature/new-etl-dag

# Deploy to production
./airflow_dags/sync_to_airflow.sh  # or via CI/CD
```

---

## 📊 What's Stored Where

| Data Type | Location | Version Controlled? |
|-----------|----------|---------------------|
| **DAG Source Code** | `~/repos/air-executor/airflow_dags/*.py` | ✅ Yes (git) |
| **DAG Files (Runtime)** | `~/airflow/dags/*.py` | ❌ No (symlink/copy target) |
| **DAG Metadata** | `~/airflow/airflow.db` → `dag` table | ❌ No (runtime state) |
| **Task Instances** | `~/airflow/airflow.db` → `task_instance` table | ❌ No (execution history) |
| **DAG Runs** | `~/airflow/airflow.db` → `dag_run` table | ❌ No (execution history) |
| **XCom Data** | `~/airflow/airflow.db` → `xcom` table | ❌ No (runtime data) |
| **Logs** | `~/airflow/logs/` | ❌ No (execution logs) |
| **Configuration** | `~/airflow/airflow.cfg` | ⚠️ Should be (config as code) |

**Key Insight:**
- **DAG code** = Version controlled in git
- **DAG execution data** = Stored in database (not version controlled)

---

## 🔐 Production Best Practices

### 1. Separate Environments

```
Git Repository Branches:
├── main              → Production DAGs
├── staging           → Staging DAGs
└── development       → Development DAGs

Airflow Instances:
├── prod.airflow.com      → Syncs from main branch
├── staging.airflow.com   → Syncs from staging branch
└── dev.airflow.com       → Syncs from development branch
```

### 2. DAG Testing in CI/CD

```yaml
# .github/workflows/test-dags.yml
name: Test DAGs

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Airflow
        run: |
          pip install apache-airflow==2.7.0
          airflow db migrate

      - name: Test DAG Parsing
        run: |
          for dag in airflow_dags/*.py; do
            python "$dag"
          done

      - name: Run Airflow DAG Tests
        run: |
          pytest tests/dags/
```

### 3. Configuration as Code

```bash
# Version control Airflow config too
git add airflow_configs/airflow.cfg
git add airflow_configs/webserver_config.py

# Deploy alongside DAGs
./deploy_configs.sh
```

### 4. Secrets Management

```python
# ❌ Bad: Hardcoded credentials in DAG
api_key = "sk-1234567890"

# ✅ Good: Use Airflow Connections/Variables
from airflow.models import Variable
api_key = Variable.get("api_key")

# ✅ Better: Use external secrets backend
# Set in airflow.cfg:
# [secrets]
# backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
```

---

## 🚀 Quick Setup (Current Project)

```bash
# 1. DAGs are already in git-tracked directory
ls ~/repos/air-executor/airflow_dags/

# 2. Choose deployment method:

# Option A: Symlinks (development - instant sync)
cd ~/repos/air-executor/airflow_dags
./sync_to_airflow.sh --symlink

# Option B: Copy (safer - manual deployment)
cd ~/repos/air-executor/airflow_dags
./sync_to_airflow.sh --copy

# 3. Verify deployment
ls -l ~/airflow/dags/

# 4. Check Airflow picks them up
source venv/bin/activate
airflow dags list | grep -E "(air_executor|hybrid)"
```

---

## 📚 Related Documentation

- `airflow_dags/README.md` - DAG directory documentation
- `AIRFLOW_INTEGRATION.md` - Integration strategies
- `HYBRID_CONTROL_FLOW.md` - Control flow patterns
- `QUICK_ANSWERS.md` - FAQ

---

## 🎯 Summary

**Best Practice: Version control DAG source code in git repo, sync to Airflow**

**Development:**
- Use symlinks for instant feedback
- Edit in git repo, test in Airflow UI, commit when working

**Production:**
- Use git-sync or CI/CD for automated deployment
- Test DAGs in CI pipeline before merging
- Separate environments (dev/staging/prod)

**Your Current Setup:**
- ✅ DAGs in `~/repos/air-executor/airflow_dags/` (git-tracked)
- ✅ Sync script available (`sync_to_airflow.sh`)
- ✅ Ready to commit and collaborate!
