# 🔄 Dynamic Task Queuing in Air-Executor

## 🎯 The Core Feature

**From your original idea (`docs/idea.md`):**

> "if task runner decide it's bigger than single task, need more effort, different context, queue task(s) in need."

This is Air-Executor's **killer feature** - tasks can queue MORE tasks during execution!

---

## 📝 How It Works

### Concept:

1. Task starts executing
2. Task discovers it needs more work (e.g., finds 100 files to process)
3. Task **queues new tasks** by writing to `tasks.json`
4. Task completes and runner dies
5. Manager polls again, finds new tasks
6. Manager spawns new runners for new tasks
7. Repeat until no tasks remain

### Architecture:

```
Runner executes task
       ↓
  Discovers work needed
       ↓
  Appends to tasks.json (atomic write)
       ↓
  Runner dies
       ↓
Manager polls (5 seconds later)
       ↓
Finds new pending tasks
       ↓
Spawns new runners
       ↓
Cycle continues...
```

---

## 💻 Implementation Examples

### Example 1: Simple Task Queuing

```python
#!/usr/bin/env python3
"""
Example task that queues additional tasks during execution.

This script is executed by Air-Executor as a task.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def queue_tasks(job_name: str, new_tasks: list):
    """
    Queue additional tasks by appending to tasks.json.

    Args:
        job_name: Name of the current job
        new_tasks: List of task dictionaries to add
    """
    tasks_file = Path(f".air-executor/jobs/{job_name}/tasks.json")

    # Read existing tasks
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)

    # Add new tasks
    for task in new_tasks:
        # Ensure required fields
        task.setdefault('status', 'pending')
        task.setdefault('created_at', datetime.utcnow().isoformat() + 'Z')
        task.setdefault('started_at', None)
        task.setdefault('completed_at', None)
        task.setdefault('error', None)
        task['job_name'] = job_name

        tasks.append(task)

    # Atomic write (temp file + rename)
    temp_file = tasks_file.parent / f".{tasks_file.name}.tmp"
    with open(temp_file, 'w') as f:
        json.dump(tasks, f, indent=2)

    temp_file.rename(tasks_file)

    print(f"✅ Queued {len(new_tasks)} new tasks")


def main():
    """Main task logic that discovers need for more work."""

    job_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    print(f"🔍 Task executing for job: {job_name}")
    print("   Analyzing data...")

    # Simulate discovering work needs
    files_found = ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"]

    print(f"   Found {len(files_found)} files to process")
    print("   Queuing processing tasks...")

    # Queue one task per file
    new_tasks = []
    for i, filename in enumerate(files_found, 1):
        new_tasks.append({
            "id": f"process-{filename}",
            "command": "echo",
            "args": [f"Processing {filename}"],
            "dependencies": []  # No dependencies, can run in parallel
        })

    # Queue the tasks!
    queue_tasks(job_name, new_tasks)

    print(f"✅ Task complete. Queued {len(new_tasks)} processing tasks")
    print("   Air-Executor manager will pick them up in next poll cycle")


if __name__ == "__main__":
    main()
```

**Usage:**

```bash
# Create a job with a discovery task
./create_job.sh discovery-job

# Manually edit tasks.json to use the dynamic script:
{
  "id": "discover",
  "command": "python",
  "args": ["dynamic_discover.py", "discovery-job"],
  "dependencies": []
}
```

### Example 2: Fan-Out Pattern

```python
#!/usr/bin/env python3
"""
Fan-out pattern: Split large dataset into chunks and process in parallel.
"""

import json
import sys
from pathlib import Path


def split_and_queue(job_name: str, data_file: str, chunk_size: int = 100):
    """
    Read large dataset, split into chunks, queue processing tasks.
    """
    tasks_file = Path(f".air-executor/jobs/{job_name}/tasks.json")

    # Simulate reading large dataset
    total_records = 1000  # In reality, read from data_file
    num_chunks = (total_records + chunk_size - 1) // chunk_size

    print(f"📊 Dataset: {total_records} records")
    print(f"   Splitting into {num_chunks} chunks of {chunk_size}")

    # Read existing tasks
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)

    # Queue chunk processing tasks
    chunk_task_ids = []
    for i in range(num_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, total_records)

        task_id = f"process-chunk-{i}"
        chunk_task_ids.append(task_id)

        tasks.append({
            "id": task_id,
            "job_name": job_name,
            "command": "python",
            "args": ["process_chunk.py", str(start), str(end)],
            "dependencies": [],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "started_at": None,
            "completed_at": None,
            "error": None
        })

    # Queue a merge task that depends on ALL chunks
    tasks.append({
        "id": "merge-results",
        "job_name": job_name,
        "command": "python",
        "args": ["merge_results.py"],
        "dependencies": chunk_task_ids,  # Waits for all chunks!
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + 'Z',
        "started_at": None,
        "completed_at": None,
        "error": None
    })

    # Atomic write
    temp_file = tasks_file.parent / f".{tasks_file.name}.tmp"
    with open(temp_file, 'w') as f:
        json.dump(tasks, f, indent=2)
    temp_file.rename(tasks_file)

    print(f"✅ Queued {num_chunks} chunk tasks + 1 merge task")


if __name__ == "__main__":
    job_name = sys.argv[1]
    data_file = sys.argv[2]
    split_and_queue(job_name, data_file)
```

### Example 3: Conditional Task Generation

```python
#!/usr/bin/env python3
"""
Conditional task queuing based on runtime results.
"""

import json
import subprocess
from pathlib import Path


def analyze_and_queue(job_name: str):
    """
    Analyze results and queue appropriate next steps.
    """
    tasks_file = Path(f".air-executor/jobs/{job_name}/tasks.json")

    # Run analysis
    print("🔍 Running analysis...")
    result = subprocess.run(
        ["python", "analyze_data.py"],
        capture_output=True,
        text=True
    )

    analysis = json.loads(result.stdout)

    print(f"   Analysis complete:")
    print(f"   - Anomalies found: {analysis['anomalies']}")
    print(f"   - Data quality: {analysis['quality']}")

    # Read tasks
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)

    # Queue tasks based on results
    if analysis['anomalies'] > 10:
        print("⚠️  High anomalies detected - queuing deep investigation")
        tasks.append({
            "id": "deep-investigation",
            "job_name": job_name,
            "command": "python",
            "args": ["deep_investigation.py"],
            "dependencies": [],
            "status": "pending"
        })

    if analysis['quality'] < 0.8:
        print("⚠️  Low quality detected - queuing data cleaning")
        tasks.append({
            "id": "clean-data",
            "job_name": job_name,
            "command": "python",
            "args": ["clean_data.py"],
            "dependencies": [],
            "status": "pending"
        })

        # Queue reprocessing after cleaning
        tasks.append({
            "id": "reprocess-after-clean",
            "job_name": job_name,
            "command": "python",
            "args": ["process_data.py"],
            "dependencies": ["clean-data"],
            "status": "pending"
        })
    else:
        print("✅ Quality good - proceeding with standard pipeline")
        tasks.append({
            "id": "standard-processing",
            "job_name": job_name,
            "command": "python",
            "args": ["standard_pipeline.py"],
            "dependencies": [],
            "status": "pending"
        })

    # Atomic write
    temp_file = tasks_file.parent / f".{tasks_file.name}.tmp"
    with open(temp_file, 'w') as f:
        json.dump(tasks, f, indent=2)
    temp_file.rename(tasks_file)

    print(f"✅ Queued {len(tasks) - len(json.load(open(tasks_file)))} new tasks based on analysis")


if __name__ == "__main__":
    job_name = sys.argv[1]
    analyze_and_queue(job_name)
```

---

## 🎯 Use Cases

### 1. **Data Pipeline Discovery**

Initial task scans directory:
```python
files = os.listdir("/data/input/")
for file in files:
    queue_task(f"process-{file}", ["process.py", file])
```

### 2. **Web Scraping with Pagination**

```python
page = 1
while has_more_pages:
    scrape_page(page)
    if more_pages_found:
        queue_task(f"scrape-page-{page+1}", ["scrape.py", str(page+1)])
    page += 1
```

### 3. **Recursive Processing**

```python
result = process_item(item)
if result.needs_recursion:
    for sub_item in result.sub_items:
        queue_task(f"process-{sub_item}", ["process.py", sub_item])
```

### 4. **Testing with Dynamic Test Generation**

```python
test_cases = discover_test_cases()
for test in test_cases:
    queue_task(f"test-{test.id}", ["pytest", test.file])
```

---

## ⚙️ From Airflow

You can also queue tasks from Airflow DAG!

```python
def create_dynamic_job(**context):
    """Create job with initial discovery task."""
    from example_python_usage import AirExecutorClient

    client = AirExecutorClient()

    # Initial job with just ONE discovery task
    client.create_job("dynamic-workflow", [
        {
            "id": "discover",
            "command": "python",
            "args": ["discover_work.py", "dynamic-workflow"],
            "dependencies": []
        }
    ])

    # discover_work.py will queue 100s of tasks!
    # Airflow sensor will wait for all of them to complete
```

---

## 🔒 Safety Considerations

### 1. **Atomic Writes**

Always use temp file + rename:
```python
temp = tasks_file.with_suffix('.tmp')
with open(temp, 'w') as f:
    json.dump(tasks, f)
temp.rename(tasks_file)  # Atomic!
```

### 2. **Avoid Infinite Loops**

```python
# Bad: Could queue forever
queue_task("process", ["process.py"])  # Don't recurse infinitely!

# Good: Add termination condition
if depth < MAX_DEPTH:
    queue_task(f"process-{depth+1}", ["process.py", str(depth+1)])
```

### 3. **Task ID Uniqueness**

```python
# Ensure unique IDs
import uuid
task_id = f"task-{uuid.uuid4()}"
```

### 4. **Dependency Validation**

```python
# Make sure dependencies exist
existing_task_ids = {t['id'] for t in tasks}
for dep in new_task['dependencies']:
    assert dep in existing_task_ids, f"Dependency {dep} not found!"
```

---

## 📊 Monitoring Dynamic Tasks

### Watch Tasks Grow:

```bash
# Terminal 1: Watch task count
watch -n 1 'cat .air-executor/jobs/*/tasks.json | jq "length"'

# Terminal 2: Watch status
watch -n 2 ./status.sh
```

### Airflow Logs:

The sensor will show:
```
📊 Job dynamic-workflow state: working
   Tasks: 47/152 completed  # Growing from 1 → 152!
```

---

## 🎉 Summary

### How to Queue Tasks Dynamically:

1. **During Task Execution:**
   ```python
   # Read tasks.json
   tasks = json.load(open(tasks_file))

   # Add new tasks
   tasks.append(new_task)

   # Atomic write
   temp.write(tasks)
   temp.rename(tasks_file)
   ```

2. **Manager Picks Up Automatically:**
   - Next poll cycle (5 seconds)
   - Finds new pending tasks
   - Spawns runners for them

3. **Benefits:**
   - ✅ Adaptive workflows
   - ✅ Handle unknown task counts
   - ✅ Parallel processing discovered items
   - ✅ Simple file-based approach

**This is what makes Air-Executor unique!** 🚀

Standard workflow engines (Airflow, Prefect) require you to know all tasks upfront. Air-Executor lets tasks discover and queue work dynamically at runtime!
