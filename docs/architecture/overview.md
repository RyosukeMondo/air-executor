# System Architecture

High-level overview of Air Executor architecture.

## System Components

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                    │
│  (CLI, Airflow UI, Direct Python API)              │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              Air Executor Core                      │
│  ┌────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Job Manager│  │ Storage  │  │ Task Executor  │  │
│  └────────────┘  └──────────┘  └────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴──────────┬──────────────┐
        │                    │              │
┌───────▼────────┐ ┌────────▼────────┐ ┌──▼──────────┐
│ Claude Wrapper │ │ Airflow DAGs    │ │ Autonomous  │
│ (SDK/CLI)      │ │                 │ │ Fixing      │
└────────────────┘ └─────────────────┘ └─────────────┘
```

## Core Components

### Job Manager
- Creates and manages job lifecycle
- Tracks job state and metadata
- Handles job dependencies

### Task Executor
- Executes tasks as isolated subprocesses
- Manages task timeout and cancellation
- Captures task output and errors

### Storage Backend
- Persists job state and history
- File-based storage with JSON serialization
- Extensible for other backends

## Integration Components

### Claude Wrapper
- Interfaces with Claude AI via SDK or CLI
- JSON-based stdin/stdout protocol
- Streaming event handling
- Session management

### Airflow Integration
- DAG definitions for common workflows
- Python operators for task execution
- Web UI for monitoring and triggering
- XCom for inter-task communication

### Autonomous Fixing
- Health monitoring (static + dynamic)
- Issue discovery and categorization
- Task queue with priority
- Circuit breaker for safety

## Data Flow

### Job Execution Flow
```
1. User creates job via API/CLI
2. Job Manager validates and stores job
3. Task Executor runs tasks sequentially/parallel
4. Results stored and returned to user
```

### Claude Query Flow
```
1. User submits prompt via DAG/API
2. Wrapper starts Claude subprocess
3. Prompt sent via JSON stdin
4. Stream events captured from stdout
5. Results aggregated and returned
```

### Autonomous Fixing Flow
```
1. Health monitor runs static checks
2. Issues discovered and queued
3. Task executor runs fixes via Claude
4. Changes committed automatically
5. Health re-checked (dynamic if improved)
6. Loop until healthy or circuit breaker
```

## Technology Stack

- **Language**: Python 3.10+
- **AI Integration**: Claude Code SDK/CLI
- **Workflow Orchestration**: Apache Airflow
- **State Management**: Redis (for autonomous fixing)
- **Configuration**: TOML
- **CLI**: Click framework

## Design Principles

1. **Modularity**: Components are loosely coupled and independently testable
2. **Extensibility**: Easy to add new task types and integrations
3. **Reliability**: Comprehensive error handling and recovery
4. **Observability**: Detailed logging and monitoring
5. **Safety**: Circuit breakers and validation gates

## See Also

- [Autonomous Fixing Architecture](./autonomous-fixing.md)
- [Session Management Patterns](./session-management-keep.md)
- [Technical Research](./technical-research.md)
