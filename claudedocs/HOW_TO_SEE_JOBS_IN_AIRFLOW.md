# 🎯 How Air-Executor Jobs Appear in Airflow

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow Web UI                           │
│                  http://localhost:8080                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ DAG: air_executor_demo                                │ │
│  │                                                       │ │
│  │  [Create Job] → [Wait] → [Get Results]              │ │
│  │       ↓            ↓          ↓                       │ │
│  │    Running      Waiting    Success                   │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
                          ↓ Creates job via Python
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              Air-Executor Job Manager                       │
│              (run_manager.py)                              │
│                                                             │
│  Polling: .air-executor/jobs/                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Job: airflow-manual__2025-10-02T07:30:00+00:00       │ │
│  │ State: working                                        │ │
│  │ Tasks: 2/3 completed                                  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step-by-Step: See Your Job in Airflow

### Step 1: Access Airflow UI

1. Open browser: **http://localhost:8080**
2. Login:
   - Username: `admin`
   - Password: `rBUUEXuhQxwAvHpw`

### Step 2: Find the DAG

After logging in, you'll see the main DAGs page.

**Look for: `air_executor_demo`**
- It has tags: `air-executor`, `demo`, `integration`
- Description: "Demo: Airflow orchestrating Air-Executor jobs"

**Wait ~30 seconds** if you don't see it (DAG processor scans every 30s)

### Step 3: Trigger the DAG

1. Click the **▶️ (Play) button** on the right side of `air_executor_demo`
2. Click **"Trigger DAG"** in the popup
3. Optionally add a run ID or leave default
4. Click **"Trigger"**

### Step 4: Watch Execution in Airflow

#### View 1: **Graph View** (Recommended!)

1. Click on the DAG name: `air_executor_demo`
2. Click **"Graph"** tab at the top
3. You'll see:
   ```
   [create_air_executor_job] → [wait_for_air_executor_completion] → [get_air_executor_results]
   ```
4. Watch the boxes change color:
   - 🟡 **Yellow** = Running
   - 🟢 **Green** = Success
   - 🔴 **Red** = Failed
   - ⚪ **White** = Not started

#### View 2: **Grid View**

1. Click **"Grid"** tab
2. See the timeline of task execution
3. Hover over squares to see task status

#### View 3: **Logs** (See Air-Executor Details!)

1. While in Graph or Grid view
2. Click on any task box (e.g., `wait_for_air_executor_completion`)
3. Click **"Log"** button
4. You'll see **real-time Air-Executor job progress**:
   ```
   📊 Job airflow-manual__2025-10-02T07:30:00+00:00 state: working
      Tasks: 2/3 completed
   ```

### Step 5: See Results

Once all tasks are green:

1. Click the **`get_air_executor_results`** task
2. Click **"Log"**
3. You'll see beautiful formatted output:

```
==============================================================
🎉 Air-Executor Job Results
==============================================================
Job Name: airflow-manual__2025-10-02T07:30:00+00:00
Final State: completed
Created: 2025-10-02T07:30:15.000000Z
Updated: 2025-10-02T07:30:25.000000Z

Task Execution Details:
--------------------------------------------------------------
✅ greet: completed
   Command: echo Hello from Airflow DAG run: manual__2025-10-02T07:30:00+00:00
   Started: 2025-10-02 07:30:16.123456
   Completed: 2025-10-02 07:30:16.234567

✅ process: completed
   Command: sleep 3
   Started: 2025-10-02 07:30:20.345678
   Completed: 2025-10-02 07:30:23.456789

✅ complete: completed
   Command: echo Air-Executor job completed successfully!
   Started: 2025-10-02 07:30:24.567890
   Completed: 2025-10-02 07:30:24.678901

==============================================================
```

## 🎨 What You See in Airflow UI

### Main Features:

#### 1. **DAG Overview**
- DAG name: `air_executor_demo`
- Schedule: Manual trigger only
- Last run status
- Next run time (N/A for manual)

#### 2. **Task Dependencies (Graph View)**
```
create_air_executor_job
         ↓
wait_for_air_executor_completion
         ↓
get_air_executor_results
```

#### 3. **Task Status Colors**
- ⚪ **None/Queued**: Task not started yet
- 🟡 **Running**: Task currently executing
- 🟢 **Success**: Task completed successfully
- 🔴 **Failed**: Task failed
- 🟠 **Up for retry**: Will retry soon
- 🟣 **Upstream failed**: Parent task failed

#### 4. **Live Logs**
Real-time output from Air-Executor:
- Job creation confirmation
- Polling updates every 2 seconds
- Task completion notifications
- Final results with timing

## 🔄 How the Integration Works

### Flow Diagram:

```
┌─────────────────────────────────────────────────────┐
│ 1. Airflow Task: create_air_executor_job            │
│    - Creates JSON files in .air-executor/jobs/      │
│    - Returns job_name                               │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ 2. Air-Executor Manager (running separately)        │
│    - Polls every 5 seconds                          │
│    - Finds new job (state: waiting)                 │
│    - Spawns ephemeral runners for tasks             │
│    - Updates state.json and tasks.json              │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ 3. Airflow Sensor: wait_for_air_executor_completion │
│    - Polls state.json every 2 seconds               │
│    - Logs progress to Airflow UI                    │
│    - Succeeds when state = completed                │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ 4. Airflow Task: get_air_executor_results           │
│    - Reads final state and task details             │
│    - Formats and displays in logs                   │
│    - Fails Airflow task if job failed               │
└─────────────────────────────────────────────────────┘
```

## 💡 Monitoring Both Systems

### Terminal 1: Airflow Logs
```bash
# See Airflow scheduler activity
tail -f ~/airflow/logs/scheduler/latest/*.log
```

### Terminal 2: Air-Executor Status
```bash
cd /home/rmondo/repos/air-executor
watch -n 2 ./status.sh
```

### Browser: Airflow UI
- http://localhost:8080
- Watch Graph view update in real-time

## 🎯 Try It Now!

### Quick Test:

1. **Open Airflow UI**: http://localhost:8080
2. **Find DAG**: `air_executor_demo`
3. **Click Play ▶️**: Trigger the DAG
4. **Click "Graph"**: Watch tasks execute
5. **Click task → "Log"**: See Air-Executor details
6. **Terminal**: Run `./status.sh` to see both systems

### Expected Timeline:

```
Time    Airflow UI                          Air-Executor
------- ----------------------------------- --------------------------
0:00    create_job starts (yellow)          Job created
0:01    create_job success (green)          State: waiting
        wait_for_completion starts (yellow)
0:05    Sensor logs: "waiting..."           Manager polls, finds job
0:06    Sensor logs: "working, 0/3"         Task 1 executing
0:07    Sensor logs: "working, 1/3"         Task 1 complete
0:10    Sensor logs: "working, 2/3"         Task 2 executing (sleep 3)
0:13    Sensor logs: "working, 3/3"         Task 2 complete
0:14    Sensor logs: "completed"            Task 3 executing
0:15    wait_for_completion success (green) All tasks complete
        get_results starts (yellow)
0:16    get_results success (green)         Job state: completed
        Shows formatted results in logs
```

## 📊 Benefits of This Integration

### What You Get:

✅ **Airflow's Rich UI**
- Visual DAG graphs
- Historical run tracking
- Task logs and monitoring
- Scheduling capabilities

✅ **Air-Executor's Efficiency**
- Ephemeral runners (no resource waste)
- Dynamic task queuing
- File-based state (version controllable)
- Simple local execution

✅ **Best of Both Worlds**
- Use Airflow for orchestration and monitoring
- Use Air-Executor for efficient execution
- Easy local development
- Production-ready when needed

## 🆘 Troubleshooting

### DAG Not Appearing?

```bash
# Check DAG processor logs
tail -f ~/airflow/logs/dag_processor_manager/dag_processor_manager.log

# Or wait 30 seconds and refresh
```

### Jobs Not Executing?

```bash
# Check Air-Executor manager is running
ps aux | grep run_manager

# If not running:
cd /home/rmondo/repos/air-executor
source venv/bin/activate
python run_manager.py &
```

### Sensor Timing Out?

- Default timeout: 5 minutes
- Check Air-Executor manager logs:
  ```bash
  cat .air-executor/manager.log
  ```

### See Job Files Directly

```bash
# List all Airflow-created jobs
ls -la .air-executor/jobs/ | grep airflow

# Check specific job
cat .air-executor/jobs/airflow-manual__*/state.json
cat .air-executor/jobs/airflow-manual__*/tasks.json
```

---

## 🎉 You're All Set!

Now you can:
1. ✅ See Air-Executor jobs in Airflow UI
2. ✅ Monitor execution in real-time
3. ✅ View detailed logs and results
4. ✅ Use Airflow's powerful features
5. ✅ Keep Air-Executor's efficiency

Go trigger that DAG and watch the magic happen! 🚀
