# Airflow Design Patterns: DAG-to-DAG vs Shared Functions

## The Problem You Encountered

**Issue**: Real-time logging was lost when `commit_and_push_dag.py` delegated to `run_claude_query_sdk()`

**Root Cause**: The shared function was only printing event types (`📨 Event: stream`) but not the actual streaming content from Claude.

## Solution Applied: Fix the Shared Function (NOT DAG-to-DAG)

**Why this is correct**:
- Same logical workflow (git commit/push is one atomic operation)
- Real-time logging just needed proper `print()` with `flush=True`
- Shared function promotes DRY (Don't Repeat Yourself)
- Maintains single responsibility per DAG

### What We Fixed

**Before** (lost real-time logs):
```python
print(f"💬 Claude: {text[:100]}...")  # Truncated, buffered
```

**After** (real-time streaming):
```python
print(text, end='', flush=True)  # Full content, immediately flushed to Airflow logs
```

## Industry-Standard Patterns

### ✅ Pattern 1: Shared Functions (What We Use)

**Use when**:
- Common logic needed by multiple DAGs
- Same responsibility, different parameters
- Need to maintain DRY principle

**Example**:
```python
# airflow_dags/claude_query_sdk.py (reusable function)
def run_claude_query_sdk(**context):
    # Common logic for all Claude operations
    prompt = context['dag_run'].conf.get('prompt')
    # ... execute with real-time logging
    print(output, end='', flush=True)  # Key: flush for real-time logs

# airflow_dags/python_cleanup_dag.py
from claude_query_sdk import run_claude_query_sdk

with DAG('python_cleanup', ...):
    task = PythonOperator(
        task_id='cleanup',
        python_callable=lambda **ctx: run_claude_query_sdk(**ctx)
    )

# airflow_dags/commit_and_push_dag.py
from claude_query_sdk import run_claude_query_sdk

with DAG('commit_and_push', ...):
    task = PythonOperator(
        task_id='commit',
        python_callable=lambda **ctx: run_claude_query_sdk(**ctx)
    )
```

**Pros**:
- ✅ Single source of truth
- ✅ Easy to maintain and debug
- ✅ Real-time logs work naturally
- ✅ Simple to test

**Cons**:
- ❌ None for this use case

---

### ✅ Pattern 2: DAG-to-DAG Triggering (TriggerDagRunOperator)

**Use when**:
- **Separate business workflows** that need to be orchestrated
- Need to trigger different workflows based on conditions
- Workflows can run at different schedules
- Need audit trail of which DAG triggered which

**Example**:
```python
# airflow_dags/ingest_data_dag.py
with DAG('ingest_data', ...):
    ingest = PythonOperator(...)

    # Trigger processing DAG after ingestion
    trigger_process = TriggerDagRunOperator(
        task_id='trigger_processing',
        trigger_dag_id='process_data',
        conf={'data_path': '{{ ti.xcom_pull(key="output_path") }}'},
    )

    ingest >> trigger_process

# airflow_dags/process_data_dag.py (separate workflow)
with DAG('process_data', ...):
    process = PythonOperator(
        task_id='process',
        python_callable=lambda **ctx: process_data(
            ctx['dag_run'].conf.get('data_path')
        )
    )
```

**When to use**:
- ✅ Ingest → Process → Analytics (separate domains)
- ✅ Parent DAG runs daily, child on-demand
- ✅ Different retry strategies for each workflow
- ✅ Need to audit which upstream DAG triggered downstream

**When NOT to use** (your case):
- ❌ Same workflow just with shared logic
- ❌ Adds complexity without benefit
- ❌ Makes debugging harder (two DAG runs instead of one)

---

### ✅ Pattern 3: ExternalTaskSensor (DAG Dependencies)

**Use when**:
- DAG B should wait for DAG A to complete
- **Separate schedules** but coordinated execution
- Dependency across teams/domains

**Example**:
```python
# Team A's DAG
with DAG('team_a_etl', schedule='@daily', ...):
    extract = PythonOperator(...)
    transform = PythonOperator(...)

# Team B's DAG (waits for Team A)
with DAG('team_b_analytics', schedule='@daily', ...):
    wait_for_etl = ExternalTaskSensor(
        task_id='wait_for_team_a',
        external_dag_id='team_a_etl',
        external_task_id='transform',
        timeout=7200,
    )

    analytics = PythonOperator(...)

    wait_for_etl >> analytics
```

**When to use**:
- ✅ Cross-team dependencies
- ✅ Different schedules, coordinated execution
- ✅ Need to wait for specific task in another DAG

---

### ✅ Pattern 4: SubDAGs (Deprecated - Use TaskGroups)

**Don't use SubDAGs** - They're deprecated in Airflow 2.0+

**Use TaskGroups instead**:
```python
from airflow.utils.task_group import TaskGroup

with DAG('complex_pipeline', ...):
    with TaskGroup('preprocessing') as preprocessing:
        clean = PythonOperator(...)
        validate = PythonOperator(...)

    with TaskGroup('processing') as processing:
        transform = PythonOperator(...)
        enrich = PythonOperator(...)

    preprocessing >> processing
```

---

## Real-Time Logging Best Practices

### ✅ Correct: Flush stdout immediately

```python
def run_claude_query_sdk(**context):
    for chunk in stream:
        print(chunk, end='', flush=True)  # ✅ Real-time in Airflow UI
```

### ❌ Wrong: Buffered output

```python
def run_claude_query_sdk(**context):
    output = []
    for chunk in stream:
        output.append(chunk)  # ❌ User sees nothing until end
    print(''.join(output))
```

### Key Points for Airflow Logging:

1. **Use `flush=True`**: Forces output to Airflow logs immediately
2. **Use `end=''`**: For streaming without newlines
3. **Print incrementally**: Don't collect and print at end
4. **Log to stdout**: Airflow captures stdout, not files

**Example - Perfect Streaming**:
```python
import sys

def stream_processing(**context):
    for i, item in enumerate(large_dataset):
        result = process(item)

        # Real-time progress in Airflow UI
        print(f"Processed {i+1}/{total}: {result}", flush=True)

        # For continuous streaming (like Claude responses)
        print(result, end='', flush=True)

    # Final newline after streaming
    print("\n", flush=True)
```

---

## Decision Tree: Which Pattern to Use?

```
Is it the same logical workflow?
├─ YES → Use shared functions (Pattern 1) ✅ YOUR CASE
│         Example: run_claude_query_sdk() shared by multiple DAGs
│
└─ NO → Are they separate business domains?
    ├─ YES → Do they need sequencing?
    │   ├─ YES → Use TriggerDagRunOperator (Pattern 2)
    │   │         Example: Ingest DAG → Process DAG → Analytics DAG
    │   │
    │   └─ NO → Independent DAGs, no pattern needed
    │             Example: Daily reports (separate schedules)
    │
    └─ NO → Do they run on different schedules but depend on each other?
        ├─ YES → Use ExternalTaskSensor (Pattern 3)
        │         Example: Team A daily ETL → Team B daily analytics
        │
        └─ NO → Use shared functions or organize with TaskGroups
```

---

## Your Use Case Analysis

### ❌ Why DAG-to-DAG Would Be Wrong

```python
# BAD: Unnecessary complexity
with DAG('commit_and_push', ...):
    trigger_claude = TriggerDagRunOperator(
        task_id='trigger_claude_query',
        trigger_dag_id='claude_query_generic',  # ❌ Separate DAG for shared logic
        conf={'prompt': GIT_COMMIT_PROMPT}
    )

# Problems:
# 1. Two DAG runs for one logical operation
# 2. Harder to debug (check two DAG logs)
# 3. More complex monitoring
# 4. No real benefit
```

### ✅ Why Shared Function Is Correct

```python
# GOOD: Simple, maintainable
from claude_query_sdk import run_claude_query_sdk

with DAG('commit_and_push', ...):
    task = PythonOperator(
        task_id='commit_and_push',
        python_callable=run_claude_query_sdk,  # ✅ Reusable function
    )

# Benefits:
# 1. Single DAG run (one workflow)
# 2. All logs in one place
# 3. Easy to test and debug
# 4. Clear responsibility
```

---

## When You WOULD Use DAG-to-DAG

### Example: Data Pipeline Orchestration

```python
# Scenario: Multi-stage data pipeline across teams

# Team A: Data Ingestion (runs every hour)
with DAG('ingest_raw_data', schedule='@hourly', ...):
    fetch = PythonOperator(task_id='fetch_from_api', ...)
    store = PythonOperator(task_id='store_to_s3', ...)

    # Trigger processing after ingestion
    trigger_process = TriggerDagRunOperator(
        task_id='trigger_processing',
        trigger_dag_id='process_data',
        conf={'batch_id': '{{ ds }}'}
    )

    fetch >> store >> trigger_process

# Team B: Data Processing (triggered by Team A)
with DAG('process_data', schedule=None, ...):  # Manual/triggered only
    validate = PythonOperator(...)
    transform = PythonOperator(...)
    load = PythonOperator(...)

    # Trigger analytics after processing
    trigger_analytics = TriggerDagRunOperator(
        task_id='trigger_analytics',
        trigger_dag_id='run_analytics'
    )

    validate >> transform >> load >> trigger_analytics

# Team C: Analytics (triggered by Team B)
with DAG('run_analytics', schedule=None, ...):
    compute_metrics = PythonOperator(...)
    generate_reports = PythonOperator(...)
```

**Why this works**:
- ✅ Different teams own different DAGs
- ✅ Different retry/timeout strategies per stage
- ✅ Clear audit trail of pipeline flow
- ✅ Can run independently during development

---

## Summary

| Pattern | Use Case | Your Scenario |
|---------|----------|---------------|
| **Shared Functions** | Same logic, different params | ✅ **YOU SHOULD USE THIS** |
| **TriggerDagRunOperator** | Separate workflows, sequenced | ❌ Overkill for shared logic |
| **ExternalTaskSensor** | Cross-DAG dependencies | ❌ Not needed |
| **TaskGroups** | Organize within DAG | ⚠️  Optional for complex DAGs |

## Testing Your Changes

Run the DAG and check logs show real-time streaming:

```bash
# Trigger the DAG
airflow dags trigger commit_and_push

# Watch logs (you should now see full streamed content)
tail -f ~/airflow/logs/dag_id=commit_and_push/.../commit_and_push/*/attempt=1.log
```

**Before fix**: Only saw `📨 Event: stream` repeatedly
**After fix**: See actual Claude output streaming in real-time ✅
