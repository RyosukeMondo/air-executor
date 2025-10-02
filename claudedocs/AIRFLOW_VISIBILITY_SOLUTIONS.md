# 📊 Airflow Visibility Solutions

## The Problem

When Air-Executor takes control, Airflow loses detailed visibility:
- ✅ Knows when job starts
- ❌ Can't see task discovery
- ❌ Can't see execution progress
- ❌ Can't see individual task status
- ✅ Knows when job completes

This document shows how to improve visibility.

---

## Solution 1: Enhanced Sensor Logging (Simple)

**Idea:** Make the sensor log more details during polling.

### Implementation:

```python
def enhanced_wait_for_completion(**context):
    """
    Enhanced sensor with detailed progress logging.
    """
    job_name = context['task_instance'].xcom_pull(
        task_ids='create_job',
        key='job_name'
    )

    state_file = Path(f".air-executor/jobs/{job_name}/state.json")
    tasks_file = state_file.parent / "tasks.json"

    if not state_file.exists():
        print("⏳ Waiting for Air-Executor to start...")
        return False

    with open(state_file) as f:
        state = json.load(f)

    with open(tasks_file) as f:
        tasks = json.load(f)

    # Calculate detailed stats
    total = len(tasks)
    completed = sum(1 for t in tasks if t['status'] == 'completed')
    running = sum(1 for t in tasks if t['status'] == 'running')
    failed = sum(1 for t in tasks if t['status'] == 'failed')
    pending = sum(1 for t in tasks if t['status'] == 'pending')

    # Store in XCom for graphing
    context['task_instance'].xcom_push(
        key=f'progress_{datetime.now().timestamp()}',
        value={
            'total': total,
            'completed': completed,
            'running': running,
            'failed': failed,
            'pending': pending,
        }
    )

    # Detailed logging
    print("="*60)
    print(f"📊 Air-Executor Progress Report")
    print("="*60)
    print(f"Job: {job_name}")
    print(f"State: {state['state']}")
    print()
    print(f"Tasks Overview:")
    print(f"  Total:     {total:>5}")
    print(f"  Completed: {completed:>5} ({completed/total*100:>5.1f}%)")
    print(f"  Running:   {running:>5}")
    print(f"  Pending:   {pending:>5}")
    print(f"  Failed:    {failed:>5}")
    print()

    if completed > 0:
        # Show recently completed tasks
        recent = [t for t in tasks if t['status'] == 'completed'][-5:]
        print(f"Recently completed tasks:")
        for task in recent:
            print(f"  ✅ {task['id']}")
        print()

    if running > 0:
        # Show currently running tasks
        current = [t for t in tasks if t['status'] == 'running']
        print(f"Currently running tasks:")
        for task in current[:5]:  # Show max 5
            print(f"  🔄 {task['id']}")
        print()

    if failed > 0:
        # Show failed tasks
        failures = [t for t in tasks if t['status'] == 'failed']
        print(f"⚠️ Failed tasks:")
        for task in failures:
            print(f"  ❌ {task['id']}: {task.get('error', 'Unknown error')}")
        print()

    # Estimate completion
    if completed > 0 and pending > 0:
        # Simple ETA calculation
        time_per_task = 5  # rough estimate in seconds
        eta_seconds = pending * time_per_task / max(running, 1)
        print(f"📅 Estimated time remaining: ~{eta_seconds/60:.1f} minutes")
        print()

    print("="*60)

    return state['state'] in ['completed', 'failed']
```

**Now Airflow logs show:**
```
============================================================
📊 Air-Executor Progress Report
============================================================
Job: my-dynamic-job
State: working

Tasks Overview:
  Total:      1234
  Completed:   789 ( 63.9%)
  Running:      45
  Pending:     400
  Failed:        0

Recently completed tasks:
  ✅ process-chunk-784
  ✅ process-chunk-785
  ✅ process-chunk-786
  ✅ process-chunk-787
  ✅ process-chunk-788

Currently running tasks:
  🔄 process-chunk-789
  🔄 process-chunk-790
  🔄 process-chunk-791
  🔄 process-chunk-792
  🔄 process-chunk-793

📅 Estimated time remaining: ~2.3 minutes
============================================================
```

**Benefits:**
- ✅ See progress in Airflow task logs
- ✅ No code changes to Air-Executor
- ✅ Simple to implement
- ❌ Still need to open logs to see details

---

## Solution 2: XCom Progress Updates (Better)

**Idea:** Push progress metrics to XCom, visualize in Airflow UI.

### Implementation:

```python
def wait_with_xcom_updates(**context):
    """
    Sensor that pushes progress to XCom for charting.
    """
    job_name = context['task_instance'].xcom_pull(
        task_ids='create_job',
        key='job_name'
    )

    # ... (same progress calculation as above)

    # Push metrics to XCom
    ti = context['task_instance']
    ti.xcom_push(key='total_tasks', value=total)
    ti.xcom_push(key='completed_tasks', value=completed)
    ti.xcom_push(key='progress_percent', value=completed/total*100)
    ti.xcom_push(key='failed_tasks', value=failed)

    # Also push timestamped snapshot for charting
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'total': total,
        'completed': completed,
        'running': running,
        'failed': failed,
        'pending': pending,
    }

    # Store in list for time-series
    history_key = f'progress_history_{job_name}'
    history = ti.xcom_pull(key=history_key) or []
    history.append(snapshot)
    ti.xcom_push(key=history_key, value=history)

    return state['state'] in ['completed', 'failed']


def visualize_progress(**context):
    """
    Post-processing task that creates a progress chart.
    """
    import matplotlib.pyplot as plt
    from datetime import datetime

    ti = context['task_instance']
    job_name = ti.xcom_pull(task_ids='create_job', key='job_name')
    history = ti.xcom_pull(
        task_ids='wait_for_completion',
        key=f'progress_history_{job_name}'
    )

    if not history:
        print("No progress history found")
        return

    # Extract data
    timestamps = [datetime.fromisoformat(h['timestamp']) for h in history]
    completed = [h['completed'] for h in history]
    total = [h['total'] for h in history]

    # Create chart
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, completed, label='Completed', linewidth=2)
    plt.plot(timestamps, total, label='Total (may grow)', linestyle='--')
    plt.xlabel('Time')
    plt.ylabel('Tasks')
    plt.title(f'Air-Executor Progress: {job_name}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save chart
    chart_path = f'/tmp/progress_{job_name}.png'
    plt.savefig(chart_path)
    print(f"✅ Progress chart saved: {chart_path}")

    # Can also upload to S3, send to Slack, etc.
```

**Benefits:**
- ✅ Programmatic access to progress
- ✅ Can create charts/graphs
- ✅ Can trigger alerts based on progress
- ❌ Still need extra task to visualize

---

## Solution 3: Airflow Metrics (Advanced)

**Idea:** Push custom metrics to Airflow's metrics system.

### Implementation:

```python
def wait_with_metrics(**context):
    """
    Sensor that publishes Air-Executor metrics to Airflow.
    """
    from airflow.metrics import Stats

    # ... (calculate progress as before)

    # Push to Airflow metrics
    Stats.gauge(f'air_executor.{job_name}.total_tasks', total)
    Stats.gauge(f'air_executor.{job_name}.completed_tasks', completed)
    Stats.gauge(f'air_executor.{job_name}.running_tasks', running)
    Stats.gauge(f'air_executor.{job_name}.failed_tasks', failed)
    Stats.gauge(f'air_executor.{job_name}.progress_percent', completed/total*100)

    # Increment counter for each poll
    Stats.incr(f'air_executor.{job_name}.polls')

    return state['state'] in ['completed', 'failed']
```

**Benefits:**
- ✅ Metrics exported to Prometheus/StatsD
- ✅ Can create Grafana dashboards
- ✅ Real-time monitoring
- ❌ Requires metrics infrastructure

---

## Solution 4: Hybrid Dashboard (Best UX)

**Idea:** Create a simple web endpoint that shows Air-Executor progress.

### Implementation:

```python
# In Air-Executor: Add a simple HTTP endpoint

from flask import Flask, jsonify
import json
from pathlib import Path

app = Flask(__name__)

@app.route('/jobs/<job_name>/progress')
def get_progress(job_name):
    """
    Endpoint to get current progress of a job.
    """
    state_file = Path(f".air-executor/jobs/{job_name}/state.json")
    tasks_file = state_file.parent / "tasks.json"

    if not state_file.exists():
        return jsonify({'error': 'Job not found'}), 404

    with open(state_file) as f:
        state = json.load(f)

    with open(tasks_file) as f:
        tasks = json.load(f)

    return jsonify({
        'job_name': job_name,
        'state': state['state'],
        'total_tasks': len(tasks),
        'completed': sum(1 for t in tasks if t['status'] == 'completed'),
        'running': sum(1 for t in tasks if t['status'] == 'running'),
        'failed': sum(1 for t in tasks if t['status'] == 'failed'),
        'pending': sum(1 for t in tasks if t['status'] == 'pending'),
        'tasks': tasks,
    })

# Run: flask run --port 5001
```

```python
# In Airflow: Sensor calls the endpoint

import requests

def wait_with_api(**context):
    """
    Sensor that calls Air-Executor API for progress.
    """
    job_name = context['task_instance'].xcom_pull(
        task_ids='create_job',
        key='job_name'
    )

    # Call Air-Executor API
    response = requests.get(
        f'http://localhost:5001/jobs/{job_name}/progress'
    )

    if response.status_code == 404:
        print("⏳ Job not started yet...")
        return False

    data = response.json()

    # Beautiful formatted progress
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  Air-Executor Progress                                   ║
╠══════════════════════════════════════════════════════════╣
║  Job: {data['job_name']:<48} ║
║  State: {data['state']:<46} ║
║                                                          ║
║  📊 Progress:                                            ║
║     Total:     {data['total_tasks']:>5}                                    ║
║     Completed: {data['completed']:>5} ({data['completed']/data['total_tasks']*100:>5.1f}%)                      ║
║     Running:   {data['running']:>5}                                    ║
║     Failed:    {data['failed']:>5}                                    ║
║     Pending:   {data['pending']:>5}                                    ║
╚══════════════════════════════════════════════════════════╝
    """)

    return data['state'] in ['completed', 'failed']
```

**Benefits:**
- ✅ Clean API for progress
- ✅ Can build custom UIs
- ✅ Other tools can query
- ✅ Decoupled from Airflow
- ❌ Requires running Flask app

---

## Solution 5: Database Progress Tracking (Production)

**Idea:** Air-Executor writes progress to shared database.

### Implementation:

```python
# Air-Executor: Update progress in DB after each task

def update_progress_in_db(job_name):
    """
    Called by Air-Executor after each task completes.
    """
    import psycopg2

    tasks_file = Path(f".air-executor/jobs/{job_name}/tasks.json")
    with open(tasks_file) as f:
        tasks = json.load(f)

    stats = {
        'total': len(tasks),
        'completed': sum(1 for t in tasks if t['status'] == 'completed'),
        'running': sum(1 for t in tasks if t['status'] == 'running'),
        'failed': sum(1 for t in tasks if t['status'] == 'failed'),
    }

    conn = psycopg2.connect(database="airflow")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO air_executor_progress
        (job_name, timestamp, total_tasks, completed_tasks, running_tasks, failed_tasks)
        VALUES (%s, NOW(), %s, %s, %s, %s)
    """, (job_name, stats['total'], stats['completed'], stats['running'], stats['failed']))
    conn.commit()
    conn.close()
```

```python
# Airflow: Query DB for progress

def wait_with_db(**context):
    """
    Sensor that queries database for progress.
    """
    from airflow.hooks.postgres_hook import PostgresHook

    job_name = context['task_instance'].xcom_pull(
        task_ids='create_job',
        key='job_name'
    )

    pg_hook = PostgresHook(postgres_conn_id='airflow_db')

    # Get latest progress
    result = pg_hook.get_first("""
        SELECT total_tasks, completed_tasks, running_tasks, failed_tasks, timestamp
        FROM air_executor_progress
        WHERE job_name = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """, parameters=[job_name])

    if not result:
        print("⏳ No progress yet...")
        return False

    total, completed, running, failed, ts = result

    print(f"""
    Progress as of {ts}:
      {completed}/{total} completed ({completed/total*100:.1f}%)
      {running} running, {failed} failed
    """)

    # Check Air-Executor state file for completion
    state_file = Path(f".air-executor/jobs/{job_name}/state.json")
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        return state['state'] in ['completed', 'failed']

    return False
```

**Benefits:**
- ✅ Historical progress tracking
- ✅ Can query from anywhere
- ✅ Survives restarts
- ✅ Can create analytics
- ❌ Requires database setup
- ❌ Air-Executor needs DB writes

---

## Comparison: Solutions

| Solution | Effort | Visibility | Real-time | Production-Ready |
|----------|--------|------------|-----------|------------------|
| **Enhanced Logging** | Low | Medium | Yes | ✅ Yes |
| **XCom Updates** | Low | Medium | Yes | ✅ Yes |
| **Metrics** | Medium | High | Yes | ✅ Yes (with infra) |
| **HTTP API** | Medium | High | Yes | ✅ Yes |
| **Database** | High | Very High | Yes | ✅ Yes |

---

## Recommended Approach

### For Development:
**Use Enhanced Logging (Solution 1)**
- Quick to implement
- Good enough for debugging
- No infrastructure needed

### For Production:
**Combine Solutions 2 + 3 + 5**
1. **XCom Updates** - For Airflow UI visibility
2. **Metrics** - For Grafana dashboards
3. **Database** - For historical analysis

---

## Example: Full Implementation

```python
# Complete sensor with all visibility features

def comprehensive_wait(**context):
    """
    Sensor with maximum visibility into Air-Executor.
    """
    from airflow.metrics import Stats
    from airflow.hooks.postgres_hook import PostgresHook

    job_name = context['task_instance'].xcom_pull(
        task_ids='create_job',
        key='job_name'
    )

    state_file = Path(f".air-executor/jobs/{job_name}/state.json")
    tasks_file = state_file.parent / "tasks.json"

    if not state_file.exists():
        return False

    with open(state_file) as f:
        state = json.load(f)

    with open(tasks_file) as f:
        tasks = json.load(f)

    # Calculate stats
    total = len(tasks)
    completed = sum(1 for t in tasks if t['status'] == 'completed')
    running = sum(1 for t in tasks if t['status'] == 'running')
    failed = sum(1 for t in tasks if t['status'] == 'failed')
    pending = sum(1 for t in tasks if t['status'] == 'pending')

    # 1. Detailed logging
    print(f"[Progress] {completed}/{total} tasks ({completed/total*100:.1f}%)")

    # 2. XCom for Airflow
    ti = context['task_instance']
    ti.xcom_push(key='progress_percent', value=completed/total*100)

    # 3. Metrics for Grafana
    Stats.gauge(f'air_executor.{job_name}.progress', completed/total*100)

    # 4. Database for history (optional)
    # pg_hook.run(...)

    return state['state'] in ['completed', 'failed']
```

---

## The Trade-off

You're absolutely right about the drawback:

**Airflow's visibility during Air-Executor execution:**
- ❌ **Limited by default** - Only sees start/end
- ✅ **Can be improved** - With the solutions above
- ⚖️ **Trade-off** - Simplicity vs. Visibility

**The question is:** How much visibility do you need?

- **Development:** Enhanced logging is usually enough
- **Production:** Consider metrics + database for full observability

---

## Summary

**Yes, you're correct:** The main drawback is limited visibility during Air-Executor execution.

**But:** This can be mitigated with:
1. Enhanced sensor logging
2. XCom progress updates
3. Metrics publishing
4. HTTP APIs
5. Database tracking

**The key insight:** You identified the trade-off perfectly! Air-Executor gains dynamic execution power but gives up Airflow's granular task-level UI. The solutions above help bridge that gap. 🎯
