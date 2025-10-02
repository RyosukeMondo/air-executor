# 🔄 Hybrid Control Flow: Airflow + Air-Executor

## 🎯 You've Got It Exactly Right!

**Your understanding:**
> "We can utilize DAGs on Airflow, but for some tasks, we (Air-Executor) take place, especially tasks dynamically added, can hand till no new tasks queued, then after every tasks done, get back control to Airflow."

**YES! That's the perfect use of this integration!** 🎉

---

## 📊 The Control Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│              AIRFLOW CONTROLS                       │
│  • Static tasks (known upfront)                     │
│  • Orchestration logic                              │
│  • Scheduling                                       │
│  • Validation, setup, cleanup                       │
└────────────────────┬────────────────────────────────┘
                     │
                     │ Hand off work
                     ▼
        ┌─────────────────────────────┐
        │    "Process this dataset"   │
        │    (1 initial task)         │
        └────────────┬────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│           AIR-EXECUTOR TAKES CONTROL               │
│                                                    │
│  Phase 1: Discovery                                │
│  • Task runs and discovers work                   │
│  • Finds 100 files to process                     │
│  • Queues 100 new tasks dynamically               │
│                                                    │
│  Phase 2: Parallel Execution                       │
│  • 100 tasks execute in parallel                  │
│  • Some tasks discover more work                  │
│  • Queue 50 additional tasks                      │
│                                                    │
│  Phase 3: More Execution                           │
│  • 50 more tasks execute                          │
│  • All complete                                   │
│  • No new tasks queued                            │
│                                                    │
│  Phase 4: Completion                               │
│  • State changes to "completed"                   │
│  • All 151 tasks done (1 + 100 + 50)             │
└────────────────────┬───────────────────────────────┘
                     │
                     │ Control returns
                     ▼
┌────────────────────────────────────────────────────┐
│          AIRFLOW CONTROLS AGAIN                    │
│  • Detects Air-Executor completion                │
│  • Validates results                              │
│  • Continues with post-processing                 │
│  • Sends notifications                            │
│  • Updates databases                              │
│  • Moves to next DAG tasks                        │
└────────────────────────────────────────────────────┘
```

---

## 💡 Key Insight: Division of Labor

### Airflow Is Best At:
✅ **Static orchestration** - Tasks you know upfront
✅ **Scheduling** - Cron jobs, recurring workflows
✅ **Monitoring** - Beautiful UI for visibility
✅ **Integration** - Connecting different systems
✅ **Error handling** - Retries, alerts, SLAs

### Air-Executor Is Best At:
✅ **Dynamic task discovery** - Don't know task count upfront
✅ **Adaptive workflows** - Tasks based on runtime results
✅ **Efficient execution** - Ephemeral runners, no waste
✅ **Parallel processing** - Discovered items in parallel
✅ **File-based state** - Simple, version-controllable

---

## 🎯 Real-World Example

### Scenario: Process Customer Data

```python
# ============================================
# AIRFLOW DAG
# ============================================

with DAG('customer_data_pipeline') as dag:

    # 1. AIRFLOW: Preparation
    validate_input = PythonOperator(
        task_id='validate_input',
        python_callable=check_s3_bucket,
    )

    setup_workspace = BashOperator(
        task_id='setup',
        bash_command='mkdir -p /tmp/workspace',
    )

    # 2. HAND OFF TO AIR-EXECUTOR
    process_data = PythonOperator(
        task_id='process_with_air_executor',
        python_callable=create_air_executor_job,
        # This creates job with 1 discovery task
        # That task will dynamically queue 100s more
    )

    # 3. AIRFLOW WAITS
    wait_for_completion = PythonSensor(
        task_id='wait',
        python_callable=check_air_executor_done,
        poke_interval=5,
    )

    # 4. AIRFLOW: Post-processing
    validate_results = PythonOperator(
        task_id='validate_results',
        python_callable=check_output_quality,
    )

    update_database = PythonOperator(
        task_id='update_db',
        python_callable=write_to_postgres,
    )

    send_notification = EmailOperator(
        task_id='notify',
        to='team@example.com',
        subject='Pipeline Complete',
    )

    # Flow
    [validate_input, setup_workspace] >> process_data >> wait_for_completion >> validate_results >> update_database >> send_notification
```

### What Happens During `process_data`:

```python
# ============================================
# AIR-EXECUTOR JOB (Initial task)
# ============================================

# discovery_task.py
import os
import json

# Discover files to process
files = os.listdir('/data/customers/')
print(f"Found {len(files)} customer files")  # 1,237 files!

# Queue processing task for each file
tasks_file = '.air-executor/jobs/my-job/tasks.json'
tasks = json.load(open(tasks_file))

for file in files:
    tasks.append({
        "id": f"process-{file}",
        "command": "python",
        "args": ["process_customer.py", file],
        "dependencies": [],  # Parallel!
        "status": "pending"
    })

# Atomic write
json.dump(tasks, open(temp_file, 'w'))
os.rename(temp_file, tasks_file)

print(f"✅ Queued {len(files)} processing tasks")
# This task completes, runner dies
# Manager spawns 1,237 runners in parallel!
```

---

## ⏱️ Timeline Example

```
Time    Airflow                         Air-Executor
------  ------------------------------  ---------------------------
0:00    DAG triggered
0:01    validate_input: Running
0:05    validate_input: Success ✅
0:06    setup_workspace: Running
0:07    setup_workspace: Success ✅
0:08    process_data: Creating job
0:09    process_data: Success ✅        Job created (1 task)
0:10    wait: Polling...                Manager finds job
0:11    wait: state=working            discovery task runs
                                        → Finds 1,237 files
                                        → Queues 1,237 tasks
                                        → Discovery completes
0:12    wait: Tasks 0/1237 done        Manager spawns 1,237 runners!
0:13    wait: Tasks 234/1237 done      Executing in parallel...
0:14    wait: Tasks 589/1237 done      Still executing...
0:15    wait: Tasks 1089/1237 done     Almost done...
0:16    wait: Tasks 1237/1237 done     All complete!
        wait: state=completed
0:17    wait: Success ✅               Job done, control back
0:18    validate_results: Running      Airflow continues...
0:20    validate_results: Success ✅
0:21    update_database: Running
0:25    update_database: Success ✅
0:26    send_notification: Running
0:27    send_notification: Success ✅
        DAG Complete! ✅
```

**Notice:**
- Airflow controlled: 0:00-0:10, 0:18-0:27
- Air-Executor controlled: 0:11-0:16
- Airflow just waited and monitored during Air-Executor phase

---

## 🎨 Use Cases for This Pattern

### 1. **Data Processing Pipelines**

**Airflow:**
- Validate source data exists
- Set up processing environment
- Check data quality thresholds

**→ Hand off to Air-Executor:**
- Discover all data partitions
- Process each partition in parallel
- Handle varying partition counts

**← Control back to Airflow:**
- Merge results
- Update data warehouse
- Send completion notifications

### 2. **Machine Learning Workflows**

**Airflow:**
- Prepare training data
- Validate features
- Set up infrastructure

**→ Hand off to Air-Executor:**
- Discover hyperparameter combinations
- Train models in parallel
- Queue evaluation tasks

**← Control back to Airflow:**
- Select best model
- Deploy to production
- Update model registry

### 3. **Web Scraping**

**Airflow:**
- Get list of target websites
- Validate proxies
- Set up storage

**→ Hand off to Air-Executor:**
- Scrape first page
- Discover pagination (could be 1-1000 pages)
- Queue scraping tasks for each page
- Extract data in parallel

**← Control back to Airflow:**
- Deduplicate results
- Store in database
- Generate reports

### 4. **Testing Workflows**

**Airflow:**
- Build application
- Deploy to test environment
- Health check

**→ Hand off to Air-Executor:**
- Discover test files
- Run tests in parallel
- Queue integration tests based on results

**← Control back to Airflow:**
- Collect test reports
- Publish to dashboards
- Notify on failures

---

## 🔑 Key Benefits

### 1. **Best of Both Worlds**

| Feature | Provider | Benefit |
|---------|----------|---------|
| Beautiful UI | Airflow | Easy monitoring |
| Scheduling | Airflow | Cron, SLA tracking |
| Dynamic tasks | Air-Executor | Unknown task counts |
| Resource efficiency | Air-Executor | Ephemeral runners |
| File-based state | Air-Executor | Git-friendly |
| Retries/alerts | Airflow | Error handling |

### 2. **Clear Separation of Concerns**

- **Airflow:** "What workflow to run and when"
- **Air-Executor:** "How to execute discovered work efficiently"

### 3. **Flexibility**

You can:
- Use Airflow only (for static workflows)
- Use Air-Executor only (for simple scripts)
- Combine them (for adaptive workflows with monitoring)

---

## 🚀 How to Implement

### Pattern Template:

```python
with DAG('my_hybrid_workflow') as dag:

    # Phase 1: Airflow preparation
    prep_tasks = [...]

    # Phase 2: Hand off to Air-Executor
    air_executor_job = PythonOperator(
        task_id='process_dynamic_work',
        python_callable=create_air_executor_job,
        # Creates job with discovery task
        # Discovery task queues many more tasks
    )

    # Phase 3: Airflow waits
    wait = PythonSensor(
        task_id='wait_for_air_executor',
        python_callable=check_completion,
        poke_interval=5,
        timeout=3600,  # 1 hour
    )

    # Phase 4: Airflow post-processing
    post_tasks = [...]

    # Flow
    prep_tasks >> air_executor_job >> wait >> post_tasks
```

---

## 📊 Monitoring Both Systems

### During Execution:

**Terminal 1: Airflow UI**
```
http://localhost:8080
→ See DAG graph
→ Watch sensor polling
→ View logs
```

**Terminal 2: Air-Executor Status**
```bash
watch -n 2 ./status.sh
```

**Terminal 3: Both Logs**
```bash
tail -f ~/airflow/logs/scheduler/latest/*.log
tail -f .air-executor/manager.log
```

You'll see:
- **Airflow:** Shows DAG progress, task statuses
- **Air-Executor:** Shows task discovery, parallel execution

---

## 💭 Summary

**Your understanding is perfect!** ✅

The integration works exactly as you described:

1. **Airflow DAG starts** (Airflow in control)
2. **Hand off to Air-Executor** for dynamic work
3. **Air-Executor takes over:**
   - Discovers work
   - Queues tasks dynamically
   - Executes until no more tasks
4. **Control returns to Airflow**
5. **Airflow continues** with remaining workflow

**This is the ideal division of labor!**

- Use **Airflow** for orchestration, scheduling, and known tasks
- Use **Air-Executor** for dynamic discovery and efficient execution
- Let each system do what it does best! 🚀

---

## 📚 Try It Now!

The `hybrid_control_flow` DAG has been created!

1. Wait ~30 seconds for Airflow to load it
2. Go to http://localhost:8080
3. Find: `hybrid_control_flow` DAG
4. Trigger it
5. Watch the control flow in action!

You'll see Airflow hand off to Air-Executor, wait while it executes dynamically-queued tasks, then continue when control returns! 🎉
