# Quick Answers to Your Questions

## 1. 🚀 How to Launch Airflow (Standalone Mode)

### Quick Start:
```bash
./start-airflow.sh
```

### Manual:
```bash
cd /home/rmondo/repos/air-executor
source venv/bin/activate
airflow standalone
```

### What It Does:
- Starts webserver on http://localhost:8080
- Starts scheduler (monitors DAGs)
- Starts triggerer (for async tasks)
- Creates admin user automatically
- Runs in **foreground** (Ctrl+C to stop)

### Login:
- **URL:** http://localhost:8080
- **Username:** `admin`
- **Password:** Check `~/airflow/simple_auth_manager_passwords.json.generated`

### To Run in Background:
```bash
airflow standalone &
```

---

## 2. ⚠️ What If Air-Executor Is Not Running?

### Short Answer:
**Jobs queue on disk until manager starts!**

### What Happens:

| Action | Result |
|--------|--------|
| Airflow creates job | ✅ SUCCESS (files written) |
| Tasks execute | ❌ NEVER (no manager) |
| Airflow sensor waits | ⏰ TIMEOUT after 5 min |
| DAG status | ❌ FAILED (timeout) |
| Job files | ✅ PERSIST on disk |

### What's NOT Possible:

❌ **Task execution** - No runners spawned
❌ **State changes** - Stays "waiting" forever
❌ **Sensor completion** - Will timeout

### What IS Possible:

✅ **Job creation** - Files written successfully
✅ **Queuing** - Jobs wait on disk
✅ **Recovery** - Start manager later → jobs auto-execute!

### Example:

```bash
# Trigger DAG while manager is OFF
# → Airflow creates job files
# → Sensor times out after 5 minutes
# → DAG fails

# Later, start manager:
./start-dev.sh

# → Manager finds waiting jobs
# → Executes them automatically
# → Can re-trigger DAG, will succeed!
```

### Queue Behavior:

Air-Executor uses **file-based queuing**:

```
.air-executor/jobs/
├── job-1/  (state: waiting) ← Queued
├── job-2/  (state: waiting) ← Queued
└── job-3/  (state: waiting) ← Queued

# Start manager:
./start-dev.sh

# All jobs execute automatically!
```

### Best Practice:

**Always start manager BEFORE triggering DAGs:**

```bash
# Terminal 1: Air-Executor manager
./start-dev.sh

# Terminal 2: Airflow
./start-airflow.sh

# Now trigger DAGs safely!
```

**Full details:** See `WHAT_IF_NOT_RUNNING.md`

---

## 3. ➕ How to Add Tasks Dynamically During Execution?

### Short Answer:
**Tasks can append to `tasks.json` during execution!**

### The Pattern:

```python
#!/usr/bin/env python3
# my_task.py - Executed by Air-Executor

import json
from pathlib import Path

def queue_tasks(job_name, new_tasks):
    """Queue additional tasks during execution."""
    tasks_file = Path(f".air-executor/jobs/{job_name}/tasks.json")

    # 1. Read existing tasks
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)

    # 2. Add new tasks
    for task in new_tasks:
        task['status'] = 'pending'
        task['job_name'] = job_name
        tasks.append(task)

    # 3. Atomic write (important!)
    temp = tasks_file.with_suffix('.tmp')
    with open(temp, 'w') as f:
        json.dump(tasks, f, indent=2)
    temp.rename(tasks_file)  # Atomic!

    print(f"✅ Queued {len(new_tasks)} tasks")

# Main task logic
job_name = "my-job"
files = ["file1.txt", "file2.txt", "file3.txt"]

# Queue processing tasks for each file
new_tasks = [
    {
        "id": f"process-{f}",
        "command": "python",
        "args": ["process.py", f],
        "dependencies": []
    }
    for f in files
]

queue_tasks(job_name, new_tasks)
```

### Flow:

```
1. Initial job has 1 task: "discover"
                ↓
2. "discover" task executes
   - Finds 100 files to process
   - Queues 100 new tasks
   - Task completes, runner dies
                ↓
3. Manager polls (5 seconds later)
   - Finds 100 pending tasks
   - Spawns runners for them
                ↓
4. 100 tasks execute in parallel
   - Each processes one file
   - All complete, runners die
                ↓
5. Manager polls
   - No pending tasks
   - Job state → completed
```

### Use Cases:

**1. Fan-Out (Parallel Processing):**
```python
# Discover work, queue parallel tasks
items = discover_items()
for item in items:
    queue_task(f"process-{item}", ["process.py", item])
```

**2. Conditional Logic:**
```python
# Queue different tasks based on results
result = analyze()
if result.anomaly:
    queue_task("investigate", ["investigate.py"])
else:
    queue_task("proceed", ["proceed.py"])
```

**3. Recursive Workflows:**
```python
# Task queues itself if more work needed
if has_more_work():
    queue_task("continue", ["process.py", next_batch])
```

### From Airflow:

```python
def create_dynamic_job(**context):
    """Airflow task that creates dynamic Air-Executor job."""
    client = AirExecutorClient()

    # Job starts with just 1 discovery task
    client.create_job("dynamic-job", [
        {
            "id": "discover",
            "command": "python",
            "args": ["discover.py", "dynamic-job"],
            "dependencies": []
        }
    ])

    # discover.py will queue 100s of tasks!
    # Airflow sensor waits for ALL tasks to complete
```

### Benefits:

✅ **Adaptive workflows** - Don't need to know task count upfront
✅ **Parallel processing** - Queue discovered items in parallel
✅ **Simple** - Just write to JSON file
✅ **Powerful** - Enables complex, data-driven workflows

**This is Air-Executor's killer feature!** Most workflow engines require all tasks defined upfront. Air-Executor lets tasks discover and queue work at runtime!

**Full details:** See `DYNAMIC_TASK_QUEUING.md`

---

## 🎯 Summary Table

| Question | Quick Answer | Full Doc |
|----------|-------------|----------|
| **How to start Airflow?** | `./start-airflow.sh` or `airflow standalone` | AIRFLOW_QUICKSTART.md |
| **What if manager not running?** | Jobs queue on disk, execute when manager starts | WHAT_IF_NOT_RUNNING.md |
| **How to add tasks dynamically?** | Append to `tasks.json` during execution | DYNAMIC_TASK_QUEUING.md |

---

## 📚 All Documentation

- ✅ **QUICK_ANSWERS.md** (this file) - Quick reference
- ✅ **AIRFLOW_QUICKSTART.md** - Complete Airflow guide
- ✅ **AIRFLOW_INTEGRATION.md** - Integration strategies
- ✅ **HOW_TO_SEE_JOBS_IN_AIRFLOW.md** - Visual guide
- ✅ **WHAT_IF_NOT_RUNNING.md** - Queue behavior explained
- ✅ **DYNAMIC_TASK_QUEUING.md** - Dynamic task examples
- ✅ **WHY_AIR_EXECUTOR.md** - Why it exists
- ✅ **PYTHON_USAGE_GUIDE.md** - Python API reference
- ✅ **IMPLEMENTATION_COMPLETE.md** - Technical details
- ✅ **README.md** - Getting started

---

## 🚀 Quick Commands

```bash
# Start everything
./start-dev.sh           # Air-Executor manager
./start-airflow.sh       # Airflow standalone

# Monitor
./status.sh              # Air-Executor jobs
watch -n 2 ./status.sh   # Live monitoring

# Create jobs
./create_job.sh my-job   # Simple job
python example_python_usage.py  # Python API

# Check services
curl localhost:8080      # Airflow UI
ps aux | grep run_manager  # Manager running?

# Stop
pkill -f run_manager     # Stop Air-Executor
pkill -f "airflow standalone"  # Stop Airflow
```

---

You're all set! 🎉
