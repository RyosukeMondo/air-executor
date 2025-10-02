# DAG Parameters Guide

## Overview

The `claude_query_sdk` DAG accepts parameters via DAG run configuration, allowing you to customize:
- **prompt**: The question/task to send to Claude
- **working_directory**: The directory where Claude wrapper executes (important for context)

---

## Methods to Pass Parameters

### Method 1: Airflow UI

1. Navigate to http://localhost:8080
2. Find `claude_query_sdk` DAG
3. Click **▶️ Trigger DAG** button
4. In the trigger dialog, add JSON configuration:

```json
{
  "prompt": "Explain how async/await works in Python",
  "working_directory": "/home/user/my-project"
}
```

5. Click **Trigger**

---

### Method 2: Airflow CLI

**Basic trigger (uses defaults):**
```bash
airflow dags trigger claude_query_sdk
```

**Trigger with custom prompt:**
```bash
airflow dags trigger claude_query_sdk \
  --conf '{"prompt": "What is the difference between list and tuple?"}'
```

**Trigger with custom prompt and directory:**
```bash
airflow dags trigger claude_query_sdk \
  --conf '{
    "prompt": "Review the code in this project",
    "working_directory": "/home/rmondo/repos/my-app"
  }'
```

**Trigger with escaped quotes (bash):**
```bash
airflow dags trigger claude_query_sdk \
  --conf "{\"prompt\": \"Explain decorators in Python\"}"
```

---

### Method 3: REST API

```bash
curl -X POST \
  http://localhost:8080/api/v1/dags/claude_query_sdk/dagRuns \
  -H 'Content-Type: application/json' \
  -u admin:password \
  -d '{
    "conf": {
      "prompt": "What are Python type hints?",
      "working_directory": "/home/rmondo/repos/air-executor"
    }
  }'
```

---

## Parameter Details

### `prompt` (string)

The question or task to send to Claude.

**Default:** `"hello, how old are you?"`

**Examples:**
```json
{"prompt": "Explain list comprehensions"}
{"prompt": "Review the authentication code in auth.py"}
{"prompt": "What are the best practices for error handling?"}
```

**Tips:**
- Keep prompts focused and specific
- For code review, reference specific files if needed
- Claude has access to the working directory contents

---

### `working_directory` (string, path)

The directory where the Claude wrapper process launches. This is important because:
- Claude can access files relative to this directory
- The wrapper's context is set to this location
- Project-specific `.clauderc` files are loaded from here

**Default:** Project root from config (`/home/rmondo/repos/air-executor`)

**Examples:**
```json
{"working_directory": "/home/rmondo/repos/my-app"}
{"working_directory": "/home/rmondo/projects/web-service"}
{"working_directory": "/tmp/test-project"}
```

**Important:**
- Path must be absolute (not relative)
- Directory must exist
- User must have read/write permissions
- Wrapper inherits this as `cwd` (current working directory)

---

## Use Cases

### Use Case 1: Quick Question
```bash
airflow dags trigger claude_query_sdk \
  --conf '{"prompt": "What is Python GIL?"}'
```

### Use Case 2: Code Review in Specific Project
```bash
airflow dags trigger claude_query_sdk \
  --conf '{
    "prompt": "Review the API endpoints in src/api/",
    "working_directory": "/home/rmondo/repos/web-service"
  }'
```

### Use Case 3: Documentation Generation
```bash
airflow dags trigger claude_query_sdk \
  --conf '{
    "prompt": "Generate README.md for this project",
    "working_directory": "/home/rmondo/repos/my-library"
  }'
```

### Use Case 4: Bug Investigation
```bash
airflow dags trigger claude_query_sdk \
  --conf '{
    "prompt": "Investigate why tests are failing in test_auth.py",
    "working_directory": "/home/rmondo/repos/api-server"
  }'
```

### Use Case 5: Refactoring Suggestions
```bash
airflow dags trigger claude_query_sdk \
  --conf '{
    "prompt": "Suggest refactoring for the database connection pooling code",
    "working_directory": "/home/rmondo/repos/data-pipeline"
  }'
```

---

## Checking Results

### View Logs (UI)
1. Click on the green task box
2. Click **Log** button
3. Scroll to find:
   ```
   📋 CLAUDE'S RESPONSE
   [Response here]
   ```

### View XCom Output (UI)
1. Click on the task
2. Click **XCom** tab
3. Key: `claude_response`
4. Value: Full response text

### View Logs (CLI)
```bash
# Find latest log file
find ~/airflow/logs/dag_id=claude_query_sdk -name "*.log" -type f | tail -1 | xargs cat

# Or use airflow command
airflow tasks logs claude_query_sdk run_claude_query_sdk <run_id>
```

---

## Parameter Validation

The DAG handles missing parameters gracefully:

| Parameter | If Missing | Behavior |
|-----------|------------|----------|
| `prompt` | Uses default | `"hello, how old are you?"` |
| `working_directory` | Uses default | Project root from config |
| Invalid JSON | DAG fails | Error in logs, task marked failed |
| Invalid path | Wrapper fails | Error: directory not found |

---

## Advanced: Programmatic Triggering

### From Python Script

```python
from airflow.api.client.local_client import Client

client = Client(None, None)

client.trigger_dag(
    dag_id='claude_query_sdk',
    conf={
        'prompt': 'Explain Python metaclasses',
        'working_directory': '/home/rmondo/repos/learning-python'
    }
)
```

### From Another DAG

```python
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

trigger_claude = TriggerDagRunOperator(
    task_id='trigger_claude_review',
    trigger_dag_id='claude_query_sdk',
    conf={
        'prompt': 'Review the latest changes',
        'working_directory': '/home/rmondo/repos/my-app'
    }
)
```

---

## Troubleshooting

### Issue: "No such file or directory"
**Cause:** `working_directory` path doesn't exist or is incorrect
**Solution:** Verify path exists: `ls /path/to/directory`

### Issue: "Permission denied"
**Cause:** User doesn't have access to `working_directory`
**Solution:** Check permissions: `ls -ld /path/to/directory`

### Issue: Empty response
**Cause:** Prompt might be unclear or Claude couldn't access files
**Solution:**
- Make prompt more specific
- Verify files exist in working directory
- Check wrapper has read permissions

### Issue: Task timeout
**Cause:** Complex prompt taking too long
**Solution:** Increase timeout in `config/air-executor.toml`:
```toml
[claude]
timeout_seconds = 120  # Increase to 2 minutes
```

---

## Best Practices

1. **Be Specific**: Clear prompts get better responses
2. **Set Working Directory**: Always specify when working with project files
3. **Check Logs**: Review full response in logs, not just XCom summary
4. **Use Absolute Paths**: Never use relative paths for `working_directory`
5. **Test Defaults First**: Run without parameters to verify setup
6. **Monitor Duration**: Complex prompts may need timeout adjustment

---

## Examples Collection

**Learning:**
```bash
airflow dags trigger claude_query_sdk --conf '{"prompt": "Explain Python generators with examples"}'
```

**Code Review:**
```bash
airflow dags trigger claude_query_sdk --conf '{"prompt": "Review security in auth module", "working_directory": "/home/user/app"}'
```

**Documentation:**
```bash
airflow dags trigger claude_query_sdk --conf '{"prompt": "Create API documentation from code comments"}'
```

**Debugging:**
```bash
airflow dags trigger claude_query_sdk --conf '{"prompt": "Why is memory usage increasing in worker.py?"}'
```

**Architecture:**
```bash
airflow dags trigger claude_query_sdk --conf '{"prompt": "Suggest improvements to the database schema"}'
```

---

## See Also

- **E2E Testing:** `E2E_TEST_READY.md`
- **Configuration:** `claudedocs/CONFIG_USAGE_GUIDE.md`
- **Troubleshooting:** `claudedocs/CLAUDE_SDK_TROUBLESHOOTING.md`
