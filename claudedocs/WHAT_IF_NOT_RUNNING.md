# What Happens If Air-Executor Manager Is Not Running?

## 🤔 The Question

What happens when you trigger an Airflow DAG that creates Air-Executor jobs, but the Air-Executor manager (`run_manager.py`) is **not running**?

---

## 📋 Answer: Jobs Queue Until Manager Starts

### ✅ What WILL Happen:

1. **Airflow Creates Job Files**
   - The `create_air_executor_job` task **succeeds**
   - Job directory created: `.air-executor/jobs/airflow-...`
   - Files written:
     - `state.json` (state: "waiting")
     - `tasks.json` (all tasks: "pending")

2. **Airflow Sensor Waits**
   - The `wait_for_air_executor_completion` task starts
   - Keeps checking every 2 seconds
   - Logs: "⏳ Waiting for job to be picked up..."
   - **Will timeout after 5 minutes** (configurable)

3. **Jobs Queued on Disk**
   - All created jobs remain in `waiting` state
   - Files persist on disk (file-based queue!)
   - **No data loss** - jobs are saved

### ❌ What WILL NOT Happen:

- ❌ **Jobs won't execute** (no manager to spawn runners)
- ❌ **Tasks won't run** (no runners created)
- ❌ **State won't change** (stays "waiting" forever)

### ⏰ What Happens When You Start Manager Later?

**Perfect recovery!** When you start the Air-Executor manager:

```bash
./start-dev.sh
# or
python run_manager.py
```

**Immediately:**
1. ✅ Manager scans `.air-executor/jobs/` directory
2. ✅ Finds ALL waiting jobs (even old ones!)
3. ✅ Starts executing them in order
4. ✅ Airflow sensors detect the state changes
5. ✅ DAG completes successfully!

---

## 🔄 Example Timeline

### Scenario: Manager Not Running

```
Time    Airflow                             Air-Executor Manager
------  ----------------------------------  ---------------------
0:00    Trigger DAG                         [NOT RUNNING]
0:01    create_job: SUCCESS ✅              (Job files created)
0:02    wait_sensor: Checking...            [NOT RUNNING]
0:04    wait_sensor: Still waiting...       [NOT RUNNING]
0:06    wait_sensor: Still waiting...       [NOT RUNNING]
...     ...                                 ...
5:00    wait_sensor: TIMEOUT ❌             [NOT RUNNING]
        DAG FAILED (timeout)

--- Later: You start manager ---

5:30    (DAG already failed)                ./start-dev.sh
5:31    (Can re-trigger DAG manually)       Manager finds waiting job!
5:32    Re-trigger DAG                      Executing tasks...
5:33    wait_sensor: state=working ✅       Task 1 complete
5:36    wait_sensor: state=completed ✅     All tasks done
5:37    get_results: SUCCESS ✅
        DAG SUCCESS ✅
```

---

## 💡 The Queue Behavior

Air-Executor uses **file-based queuing**:

### How It Works:

```
.air-executor/jobs/
├── job-1/
│   ├── state.json       # state: "waiting"
│   └── tasks.json       # Ready to execute
├── job-2/
│   ├── state.json       # state: "waiting"
│   └── tasks.json       # Ready to execute
└── job-3/
    ├── state.json       # state: "waiting"
    └── tasks.json       # Ready to execute
```

**When manager starts:**
- Scans directory
- Processes jobs in order found
- Updates state files as it goes
- Airflow sensors see the updates

### Benefits:

✅ **Persistent Queue**: Jobs survive manager restarts
✅ **No Message Broker Needed**: Files are the queue
✅ **Easy Debugging**: Just look at JSON files
✅ **Git-Friendly**: Can version control job state
✅ **Crash Recovery**: Manager restart picks up where it left off

---

## 🚨 Timeout Scenarios

### Airflow Sensor Timeout (Default: 5 minutes)

**What happens:**
```python
wait_for_job = PythonSensor(
    task_id='wait_for_completion',
    poke_interval=2,
    timeout=300,  # 5 minutes = 300 seconds
)
```

If Air-Executor manager doesn't start within 5 minutes:
1. Sensor task **fails** with timeout error
2. DAG marked as **FAILED**
3. Job files remain on disk in "waiting" state
4. You can **manually re-trigger** the DAG later

### How to Handle:

**Option 1: Increase Timeout**
```python
timeout=1800,  # 30 minutes
```

**Option 2: Infinite Wait (Not Recommended)**
```python
timeout=0,  # Wait forever
```

**Option 3: Retry Policy**
```python
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
}
```

**Option 4: Skip Sensor, Check Manually**
```bash
# Check job status
./status.sh

# Or directly:
cat .air-executor/jobs/airflow-*/state.json
```

---

## 🎯 Best Practices

### 1. **Always Start Manager First**

**Before triggering Airflow DAGs:**
```bash
# Terminal 1: Start Air-Executor manager
./start-dev.sh

# Terminal 2: Start Airflow
./start-airflow.sh

# Terminal 3: Trigger DAG via UI or:
airflow dags trigger air_executor_demo
```

### 2. **Monitor Both Systems**

**Terminal 4: Watch Air-Executor status**
```bash
watch -n 2 ./status.sh
```

**Browser: Watch Airflow UI**
- http://localhost:8080

### 3. **Health Check Script**

```bash
#!/bin/bash
# check-services.sh

echo "Checking Air-Executor Manager..."
if pgrep -f "run_manager.py" > /dev/null; then
    echo "✅ Air-Executor Manager: RUNNING"
else
    echo "❌ Air-Executor Manager: NOT RUNNING"
    echo "   Start with: ./start-dev.sh"
fi

echo ""
echo "Checking Airflow..."
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null; then
    echo "✅ Airflow: RUNNING (http://localhost:8080)"
else
    echo "❌ Airflow: NOT RUNNING"
    echo "   Start with: ./start-airflow.sh"
fi
```

### 4. **Graceful Degradation**

**If you know manager will be down:**

Don't use PythonSensor, use separate DAGs:

```python
# DAG 1: Just create jobs
create_jobs_dag = DAG('create_air_executor_jobs', ...)

# DAG 2: Just check results (run later)
check_results_dag = DAG('check_air_executor_results', ...)
```

---

## 🔧 Recovery Commands

### Restart Manager to Process Queued Jobs

```bash
# Stop manager if running
pkill -f run_manager.py

# Start fresh
./start-dev.sh
```

### Check Waiting Jobs

```bash
# List all waiting jobs
find .air-executor/jobs -name "state.json" -exec grep -l '"waiting"' {} \; | xargs dirname
```

### Manually Trigger Job Execution

```bash
# The manager will pick it up automatically if it's in "waiting" state
# Just make sure manager is running:
./start-dev.sh
```

### Clear Stuck Jobs (Nuclear Option)

```bash
# Remove all jobs (careful!)
rm -rf .air-executor/jobs/*

# Or remove specific failed jobs:
rm -rf .air-executor/jobs/airflow-failed-job-*
```

---

## 📊 Comparison: With vs Without Manager

| Aspect | Manager Running ✅ | Manager Not Running ❌ |
|--------|-------------------|------------------------|
| **Job Creation** | ✅ Success | ✅ Success (files created) |
| **Task Execution** | ✅ Runs immediately | ❌ Never runs |
| **Airflow Sensor** | ✅ Completes | ❌ Times out (5 min) |
| **DAG Status** | ✅ SUCCESS | ❌ FAILED (timeout) |
| **Job Files** | ✅ Persistent | ✅ Persistent (queued) |
| **Recovery** | N/A | ✅ Start manager → auto-runs |

---

## 🎉 The Beautiful Part

**File-based queuing means:**

You can:
1. ✅ Create jobs anytime (via Airflow or scripts)
2. ✅ Stop/start manager freely
3. ✅ Jobs wait patiently on disk
4. ✅ No message broker complexity
5. ✅ Version control your queue state
6. ✅ Debug by reading JSON files

**This is Air-Executor's superpower!**

Unlike traditional job queues (RabbitMQ, Redis, SQS) that lose jobs on restart, Air-Executor's file-based approach means **jobs never disappear**.

---

## 💭 Summary

**Q: What if Air-Executor manager is not running?**

**A: Jobs wait patiently on disk until manager starts!**

- ✅ Airflow can create jobs (writes files)
- ❌ Jobs won't execute (no runners spawned)
- ⏰ Airflow sensor will timeout after 5 minutes
- 🔄 Start manager later → jobs auto-execute
- 📁 No data loss (file-based persistence)

**Best practice:** Start manager before triggering DAGs, but recovery is always possible! 🚀
