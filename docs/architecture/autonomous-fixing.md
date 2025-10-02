# Autonomous Code Fixing Architecture

## Overview

Multi-DAG orchestration system using air-executor for autonomous, context-efficient code fixing with concrete completion detection.

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│              Orchestrator DAG (Meta-Controller)            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Health Check │→ │ Phase Router │→ │ Completion Gate │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│                           │                                │
│                    State Store (Redis/PostgreSQL)          │
└───────────────────────────┼────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  ┌──────────┐        ┌──────────┐       ┌──────────┐
  │ Build    │        │ Test     │       │ Lint     │
  │ Fix DAG  │        │ Fix DAG  │       │ Fix DAG  │
  └──────────┘        └──────────┘       └──────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                   ┌─────────────────┐
                   │  air-executor   │
                   │  + Task Queue   │
                   └─────────────────┘
```

## Core Components

### 1. Health Metrics System

**Purpose**: Observable state that drives orchestration decisions

```python
# airflow_dags/health_monitor.py
from dataclasses import dataclass
from typing import Dict, List
import subprocess
import json

@dataclass
class HealthMetrics:
    build_status: str  # 'pass' | 'fail'
    test_pass_rate: float  # 0.0 - 1.0
    test_total: int
    test_failures: List[str]
    lint_errors: int
    lint_warnings: int
    coverage: float
    timestamp: str

def collect_health_metrics() -> HealthMetrics:
    """Collect current project health state"""
    return HealthMetrics(
        build_status=check_build(),
        test_pass_rate=run_tests(),
        test_total=count_tests(),
        test_failures=get_failing_tests(),
        lint_errors=run_linter(),
        lint_warnings=get_warnings(),
        coverage=get_coverage(),
        timestamp=datetime.now().isoformat()
    )

def check_build() -> str:
    """Run build and return status"""
    result = subprocess.run(['npm', 'run', 'build'], capture_output=True)
    return 'pass' if result.returncode == 0 else 'fail'

def run_tests() -> float:
    """Run tests and return pass rate"""
    result = subprocess.run(['pytest', '--json-report'], capture_output=True)
    report = json.loads(result.stdout)
    total = report['summary']['total']
    passed = report['summary']['passed']
    return passed / total if total > 0 else 0.0

def get_failing_tests() -> List[str]:
    """Get list of failing test names"""
    result = subprocess.run(['pytest', '--collect-only', '-q'], capture_output=True)
    # Parse output for failed tests
    return parse_test_failures(result.stdout)
```

### 2. State Store

**Purpose**: Track discovered issues, completed fixes, session context across DAG runs

```python
# airflow_dags/state_manager.py
from typing import Dict, List, Optional
import redis
import json

class StateManager:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
        self.prefix = 'code_fix:'

    def queue_task(self, task: Dict):
        """Add task to priority queue"""
        priority = task.get('priority', 5)
        task_json = json.dumps(task)
        self.redis.zadd(f'{self.prefix}task_queue', {task_json: priority})

    def get_next_tasks(self, count: int = 5) -> List[Dict]:
        """Get highest priority tasks"""
        tasks = self.redis.zrange(f'{self.prefix}task_queue', 0, count-1)
        return [json.loads(t) for t in tasks]

    def mark_task_complete(self, task_id: str):
        """Remove completed task from queue"""
        # Find and remove task by ID
        pass

    def store_session_summary(self, phase: str, summary: Dict):
        """Store summary of what was fixed in last session"""
        key = f'{self.prefix}summary:{phase}'
        self.redis.setex(key, 3600, json.dumps(summary))  # 1 hour TTL

    def get_session_summary(self, phase: str) -> Optional[Dict]:
        """Get last session summary for context"""
        key = f'{self.prefix}summary:{phase}'
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def record_run_result(self, run_id: str, metrics: HealthMetrics):
        """Record results of orchestrator run"""
        key = f'{self.prefix}run_history'
        self.redis.lpush(key, json.dumps({
            'run_id': run_id,
            'timestamp': metrics.timestamp,
            'metrics': metrics.__dict__
        }))
        self.redis.ltrim(key, 0, 9)  # Keep last 10 runs

    def get_run_history(self, count: int = 10) -> List[Dict]:
        """Get recent run history"""
        key = f'{self.prefix}run_history'
        history = self.redis.lrange(key, 0, count-1)
        return [json.loads(h) for h in history]
```

### 3. Orchestrator DAG

**Purpose**: Meta-controller that monitors health, routes to phase DAGs, detects completion

```python
# airflow_dags/fix_orchestrator.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

def check_health(**context):
    """Collect current health metrics"""
    metrics = collect_health_metrics()
    context['task_instance'].xcom_push(key='health_metrics', value=metrics.__dict__)
    return metrics.__dict__

def route_to_phase(**context):
    """Decide which phase DAG to trigger based on health"""
    metrics = context['task_instance'].xcom_pull(key='health_metrics')

    # Priority order: build > tests > lint
    if metrics['build_status'] == 'fail':
        return 'trigger_build_fix'
    elif metrics['test_pass_rate'] < 1.0:
        return 'trigger_test_fix'
    elif metrics['lint_errors'] > 0:
        return 'trigger_lint_fix'
    else:
        return 'check_completion'

def check_completion(**context):
    """Determine if all fixes are complete"""
    state_mgr = StateManager()
    history = state_mgr.get_run_history(count=3)

    # Completion criteria
    current_metrics = context['task_instance'].xcom_pull(key='health_metrics')
    criteria = {
        'build_passing': current_metrics['build_status'] == 'pass',
        'tests_passing': current_metrics['test_pass_rate'] >= 0.95,
        'no_lint_errors': current_metrics['lint_errors'] == 0,
        'stable_3_runs': all(
            h['metrics']['build_status'] == 'pass'
            for h in history
        ) if len(history) >= 3 else False
    }

    if all(criteria.values()):
        print("✅ All completion criteria met!")
        return 'complete'
    else:
        print(f"⏳ Continuing... Criteria: {criteria}")
        return 'continue'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'fix_orchestrator',
    default_args=default_args,
    description='Meta-controller for autonomous code fixing',
    schedule_interval=None,  # Manual or triggered by external events
    catchup=False,
) as dag:

    health_check = PythonOperator(
        task_id='health_check',
        python_callable=check_health,
        provide_context=True,
    )

    phase_router = BranchPythonOperator(
        task_id='phase_router',
        python_callable=route_to_phase,
        provide_context=True,
    )

    trigger_build_fix = TriggerDagRunOperator(
        task_id='trigger_build_fix',
        trigger_dag_id='build_fix_dag',
        conf={'session_mode': 'separate'},
    )

    trigger_test_fix = TriggerDagRunOperator(
        task_id='trigger_test_fix',
        trigger_dag_id='test_fix_dag',
        conf={'session_mode': 'separate'},
    )

    trigger_lint_fix = TriggerDagRunOperator(
        task_id='trigger_lint_fix',
        trigger_dag_id='lint_fix_dag',
        conf={'session_mode': 'separate'},
    )

    completion_gate = PythonOperator(
        task_id='check_completion',
        python_callable=check_completion,
        provide_context=True,
    )

    # Flow
    health_check >> phase_router
    phase_router >> [trigger_build_fix, trigger_test_fix, trigger_lint_fix, completion_gate]
```

### 4. Phase DAG Template

**Purpose**: Focused DAG for specific fix category (build, test, lint)

```python
# airflow_dags/build_fix_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def discover_build_issues(**context):
    """Analyze build failures and queue specific fix tasks"""
    state_mgr = StateManager()

    # Run build to capture errors
    result = subprocess.run(['npm', 'run', 'build'],
                          capture_output=True, text=True)

    if result.returncode != 0:
        # Parse build errors
        errors = parse_build_errors(result.stderr)

        # Queue tasks for each error
        for error in errors:
            state_mgr.queue_task({
                'type': 'fix_build_error',
                'error_type': error['type'],
                'file': error['file'],
                'message': error['message'],
                'priority': calculate_priority(error),
                'context': extract_file_context(error['file'])
            })

    return len(errors)

def run_fixes_via_executor(**context):
    """Execute queued build fix tasks using air-executor"""
    state_mgr = StateManager()
    tasks = state_mgr.get_next_tasks(count=5)  # Batch of 5

    results = []
    for task in tasks:
        # Prepare narrow context prompt
        prompt = f"""Fix this build error:

File: {task['file']}
Error: {task['message']}

Context:
{task['context']}

Previous session summary:
{state_mgr.get_session_summary('build')}

Fix ONLY this specific error. Commit when done.
"""

        # Call air-executor
        result = subprocess.run([
            'python', 'claude_wrapper.py',
            '--prompt', prompt,
            '--task-mode', 'fix'
        ], capture_output=True, text=True)

        results.append({
            'task_id': task.get('id'),
            'success': result.returncode == 0,
            'output': result.stdout
        })

        if result.returncode == 0:
            state_mgr.mark_task_complete(task['id'])

    # Store session summary
    state_mgr.store_session_summary('build', {
        'fixed_count': sum(1 for r in results if r['success']),
        'total_count': len(results),
        'timestamp': datetime.now().isoformat()
    })

    return results

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
}

with DAG(
    'build_fix_dag',
    default_args=default_args,
    description='Fix build errors autonomously',
    schedule_interval=None,
    catchup=False,
) as dag:

    discover = PythonOperator(
        task_id='discover_build_issues',
        python_callable=discover_build_issues,
    )

    fix = PythonOperator(
        task_id='run_fixes',
        python_callable=run_fixes_via_executor,
    )

    discover >> fix
```

## Context Management Strategy

### Hybrid Approach: Separate Sessions + Shared State

**Per-task context** (separate session benefits):
- Narrow, focused prompt
- Only relevant files
- Specific error/test case
- Fresh analysis per task

**Shared state** (session continuity benefits):
- Session summaries stored in Redis
- Previous fixes inform next tasks
- Pattern learning across sessions
- Avoid re-analyzing same issues

### Context Compression

```python
def extract_file_context(filepath: str, error_line: int = None) -> str:
    """Extract minimal relevant context for a file"""
    with open(filepath) as f:
        lines = f.readlines()

    if error_line:
        # Get ±10 lines around error
        start = max(0, error_line - 10)
        end = min(len(lines), error_line + 10)
        context = ''.join(lines[start:end])
    else:
        # Get file structure only (imports, class/function signatures)
        context = extract_structure(lines)

    return f"```{filepath}\n{context}\n```"

def extract_structure(lines: List[str]) -> str:
    """Extract imports and signatures only"""
    structure = []
    for line in lines:
        if (line.startswith('import ') or
            line.startswith('from ') or
            line.strip().startswith('def ') or
            line.strip().startswith('class ')):
            structure.append(line)
    return ''.join(structure)
```

## Completion Detection Logic

```python
class CompletionDetector:
    def __init__(self, state_mgr: StateManager):
        self.state_mgr = state_mgr

    def is_complete(self) -> bool:
        """Check all completion criteria"""
        metrics = collect_health_metrics()
        history = self.state_mgr.get_run_history(count=3)

        criteria = {
            'build_passing': metrics.build_status == 'pass',
            'tests_passing': metrics.test_pass_rate >= 0.95,
            'lint_clean': metrics.lint_errors == 0,
            'stable_runs': self._check_stability(history),
            'no_queued_tasks': self._check_queue_empty(),
            'no_regression': self._check_no_regression(history)
        }

        print(f"Completion criteria: {criteria}")
        return all(criteria.values())

    def _check_stability(self, history: List[Dict]) -> bool:
        """Verify last 3 runs had no new issues"""
        if len(history) < 3:
            return False
        return all(h['metrics']['build_status'] == 'pass' for h in history)

    def _check_queue_empty(self) -> bool:
        """Verify no tasks left in queue"""
        tasks = self.state_mgr.get_next_tasks(count=1)
        return len(tasks) == 0

    def _check_no_regression(self, history: List[Dict]) -> bool:
        """Verify metrics aren't degrading"""
        if len(history) < 2:
            return True

        current = history[0]['metrics']
        previous = history[1]['metrics']

        return (
            current['test_pass_rate'] >= previous['test_pass_rate'] and
            current['lint_errors'] <= previous['lint_errors']
        )

    def should_continue(self) -> bool:
        """Apply circuit breaker logic"""
        history = self.state_mgr.get_run_history(count=10)

        # Stop if too many consecutive failures
        recent_failures = sum(
            1 for h in history[:5]
            if h['metrics']['build_status'] == 'fail'
        )
        if recent_failures >= 5:
            print("❌ Circuit breaker: Too many consecutive failures")
            return False

        # Stop if no progress in last 5 runs
        if len(history) >= 5:
            test_rates = [h['metrics']['test_pass_rate'] for h in history[:5]]
            if len(set(test_rates)) == 1:  # No change
                print("⚠️ No progress detected in last 5 runs")
                return False

        return not self.is_complete()
```

## Dynamic Task Generation

```python
class TaskGenerator:
    """Generate tasks dynamically based on discovered issues"""

    def generate_from_build(self, build_output: str) -> List[Dict]:
        """Parse build errors into tasks"""
        errors = parse_build_errors(build_output)
        tasks = []

        for error in errors:
            tasks.append({
                'id': generate_task_id(),
                'type': 'fix_build_error',
                'priority': self._calculate_priority(error),
                'file': error['file'],
                'line': error.get('line'),
                'message': error['message'],
                'context': extract_file_context(error['file'], error.get('line'))
            })

        return tasks

    def generate_from_tests(self, test_output: str) -> List[Dict]:
        """Parse test failures into tasks"""
        failures = parse_test_failures(test_output)
        tasks = []

        for failure in failures:
            tasks.append({
                'id': generate_task_id(),
                'type': 'fix_test_failure',
                'priority': self._calculate_priority(failure),
                'test_file': failure['test_file'],
                'test_name': failure['test_name'],
                'failure_message': failure['message'],
                'context': extract_test_context(failure)
            })

        return tasks

    def _calculate_priority(self, issue: Dict) -> int:
        """Calculate priority (1-10, 1 = highest)"""
        # Build blockers = highest priority
        if issue.get('type') == 'syntax_error':
            return 1
        elif issue.get('type') == 'import_error':
            return 2
        elif issue.get('type') == 'type_error':
            return 3
        else:
            return 5  # Default
```

## Air-Executor Integration

```python
class AirExecutorRunner:
    """Interface to run tasks via air-executor"""

    def run_task(self, task: Dict, session_mode: str = 'separate') -> Dict:
        """Execute a single fix task"""

        # Build prompt based on task type
        if task['type'] == 'fix_build_error':
            prompt = self._build_fix_prompt(task)
        elif task['type'] == 'fix_test_failure':
            prompt = self._test_fix_prompt(task)
        else:
            prompt = self._generic_fix_prompt(task)

        # Add session context if available
        if session_mode == 'hybrid':
            state_mgr = StateManager()
            prev_summary = state_mgr.get_session_summary(task['type'])
            if prev_summary:
                prompt += f"\n\nPrevious session: {prev_summary}"

        # Call air-executor
        result = subprocess.run([
            'python', 'claude_wrapper.py',
            '--prompt', prompt,
            '--working-dir', os.getcwd(),
            '--auto-commit'
        ], capture_output=True, text=True, timeout=300)

        return {
            'task_id': task['id'],
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': time.time() - start_time
        }

    def _build_fix_prompt(self, task: Dict) -> str:
        return f"""Fix this build error:

**File**: {task['file']}:{task.get('line', '?')}
**Error**: {task['message']}

**Code Context**:
{task['context']}

**Instructions**:
1. Analyze the error
2. Fix ONLY this specific error
3. Verify build passes
4. Commit with message: "fix: {task['message'][:50]}"

Be surgical - change only what's needed.
"""

    def _test_fix_prompt(self, task: Dict) -> str:
        return f"""Fix this failing test:

**Test**: {task['test_name']}
**File**: {task['test_file']}
**Failure**: {task['failure_message']}

**Test Context**:
{task['context']}

**Instructions**:
1. Understand why test is failing
2. Fix the implementation (not the test)
3. Verify test passes
4. Commit with message: "fix: {task['test_name']}"
"""
```

## Libraries & Tools

### Recommended Stack

1. **Orchestration**
   - **Apache Airflow** (already using) - DAG orchestration
   - **Celery** (comes with Airflow) - Distributed task execution

2. **State Management**
   - **Redis** - Fast state store, task queue, session summaries
   - **PostgreSQL** - Airflow metadata + persistent state

3. **Observability**
   - **Prometheus** - Metrics collection (test pass rate, build status)
   - **Grafana** - Dashboards for health visualization
   - **Airflow UI** - DAG execution monitoring

4. **AI Orchestration** (optional enhancements)
   - **LangGraph** - State machines for AI agents
   - **LangChain Memory** - Context summarization

5. **Code Quality**
   - **pytest** + **pytest-json-report** - Test execution with structured output
   - **ruff** - Fast Python linter
   - **mypy** - Type checking

### Installation

```bash
# Core dependencies
pip install apache-airflow redis celery

# Monitoring
pip install prometheus-client

# Code quality
pip install pytest pytest-json-report ruff mypy

# Optional AI orchestration
pip install langgraph langchain
```

## Usage Flow

### 1. Setup

```bash
# Initialize state store
redis-server

# Initialize Airflow
airflow db init
airflow users create --role Admin --username admin --email admin@example.com

# Start Airflow
airflow webserver &
airflow scheduler &
```

### 2. Trigger Orchestrator

```bash
# Manual trigger
airflow dags trigger fix_orchestrator

# Or set up event-based trigger (on git push, CI failure, etc.)
```

### 3. Monitor Progress

```bash
# Watch Airflow UI
open http://localhost:8080

# Check health metrics
redis-cli GET code_fix:run_history

# View task queue
redis-cli ZRANGE code_fix:task_queue 0 -1 WITHSCORES
```

### 4. Completion

When orchestrator detects completion criteria met, it stops scheduling new runs.

## Configuration

```yaml
# airflow_config.yaml
code_fix:
  completion_criteria:
    min_test_pass_rate: 0.95
    max_lint_errors: 0
    stability_runs: 3

  circuit_breaker:
    max_consecutive_failures: 5
    max_total_runs: 20
    max_duration_hours: 4

  session_mode: separate  # 'separate' | 'keep' | 'hybrid'

  batch_sizes:
    build_fixes: 5
    test_fixes: 3
    lint_fixes: 10

  air_executor:
    timeout: 300  # seconds
    auto_commit: true
    max_retries: 2
```

## Advantages of This Approach

✅ **Concrete completion detection** - Clear criteria, no infinite loops
✅ **Efficient context usage** - Narrow prompts per task, shared state via Redis
✅ **Autonomous task generation** - Discovers new issues dynamically
✅ **Fault tolerance** - Circuit breakers prevent runaway execution
✅ **Observable** - Health metrics, run history, task queues all visible
✅ **Scalable** - Can run multiple phase DAGs in parallel
✅ **Flexible session management** - Choose mode per phase (separate vs hybrid)
✅ **Incremental progress** - Each run makes measurable progress toward goals
