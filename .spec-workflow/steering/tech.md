# Technology Stack

## Project Type

Air-Executor is a workflow orchestration system with two implementation paths:
1. **Airflow-based**: DAG-driven orchestration using Apache Airflow with KubernetesExecutor
2. **Prefect-based**: Python-native workflow orchestration using Prefect with Work Pools

Both implementations share common patterns but differ in deployment infrastructure and execution models.

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.11+
- **Runtime**: CPython 3.11 or higher
- **Package Manager**: pip with requirements.txt
- **Build Tools**: make for common operations (install, test, run)

### Key Dependencies/Libraries

**Airflow Implementation:**
- **Apache Airflow 2.8+**: Workflow orchestration and scheduling
- **Kubernetes Python Client**: Pod management and status monitoring
- **PostgreSQL Driver (psycopg2)**: Metadata database connectivity

**Prefect Implementation:**
- **Prefect 2.14+**: Dynamic workflow orchestration
- **Docker SDK**: Container-based task execution
- **httpx**: Async HTTP client for Prefect API communication

**Shared Dependencies:**
- **Claude Code CLI**: AI-assisted task execution (wrapper integration)
- **pydantic**: Data validation and settings management
- **structlog**: Structured logging for observability
- **pytest**: Testing framework with pytest-asyncio
- **click**: CLI interface for job management commands

### Application Architecture

**Control Plane Architecture:**
- **Job Manager**: Polling loop that monitors job status and spawns task runners
- **Task Runner**: Single-task execution wrapper around Claude Code CLI
- **Job Store**: File-based or database-backed job state persistence

**Airflow Architecture:**
- Scheduler acts as MCP (Master Control Program)
- KubernetesExecutor creates ephemeral Pods per task
- Dynamic Task Mapping for runtime sub-task generation
- DAGs define job structure with expand() for dynamic tasks

**Prefect Architecture:**
- Prefect API Server acts as control plane
- Work Pools with Process/Docker workers
- Flow-as-orchestrator pattern with subflow submissions
- --run-once workers for ephemeral execution model

### Data Storage

- **Primary Storage**:
  - Airflow: PostgreSQL for metadata, Redis for broker (optional)
  - Prefect: SQLite (dev) / PostgreSQL (prod) for Prefect API
  - Job State: JSON files in `.air-executor/jobs/` directory
- **Caching**: In-memory job status cache with file-based persistence
- **Data Formats**: JSON for job definitions, YAML for configuration, structured logs in JSON

### External Integrations

- **Kubernetes API**: Pod lifecycle management (Airflow implementation)
- **Docker Engine API**: Container execution (Prefect implementation)
- **Claude Code CLI**: Task execution subprocess integration
- **Protocols**: HTTP/REST for Prefect API, Kubernetes API via Python client
- **Authentication**: Kubernetes RBAC, Prefect API keys, file-based job access control

### Monitoring & Dashboard Technologies

**MVP (CLI-based):**
- **Dashboard Framework**: Rich terminal UI using `rich` library
- **Real-time Communication**: Polling-based status checks (5-second interval)
- **Visualization**: ASCII progress bars, colored status indicators
- **State Management**: File system as source of truth for job state

**Future (Web Dashboard):**
- Dashboard framework TBD (React, Vue, or Streamlit candidates)
- WebSocket for real-time updates
- Chart.js or D3 for visualization
- Prefect/Airflow native UIs as starting point

## Development Environment

### Build & Development Tools
- **Build System**: Makefile for common tasks (make install, make test, make dev)
- **Package Management**: pip with virtual environment (venv)
- **Development Workflow**: Hot reload for job manager (watchdog), manual restart for task runners
- **Dependency Management**: pip-tools for requirements.txt generation

### Code Quality Tools
- **Static Analysis**:
  - ruff for fast Python linting
  - mypy for type checking
  - bandit for security scanning
- **Formatting**:
  - black (line length 100)
  - isort for import sorting
- **Testing Framework**:
  - pytest for unit/integration tests
  - pytest-cov for coverage reporting (>80% target)
  - pytest-asyncio for async test support
- **Documentation**:
  - Sphinx for API documentation
  - mkdocs for user guides

### Version Control & Collaboration
- **VCS**: Git
- **Branching Strategy**: GitHub Flow (feature branches → main)
- **Code Review Process**:
  - PR required for all changes
  - Automated CI checks (linting, tests, type checking)
  - One approval required before merge

### Dashboard Development (Future)
- **Live Reload**: TBD based on framework choice
- **Port Management**: Dynamic port allocation (8080-8100 range)
- **Multi-Instance Support**: Port-based isolation for concurrent job managers

## Deployment & Distribution

- **Target Platforms**:
  - Linux (Ubuntu 22.04+, RHEL 8+)
  - macOS (Monterey+)
  - Windows (WSL2 required)
- **Distribution Method**:
  - PyPI package (pip install air-executor)
  - Docker images for orchestration platforms
  - GitHub releases with binaries
- **Installation Requirements**:
  - Python 3.11+
  - Kubernetes cluster (Airflow) or Docker Engine (Prefect)
  - 2GB RAM minimum, 4GB recommended
  - Claude Code CLI installed and authenticated
- **Update Mechanism**: pip upgrade, Docker image tags

## Technical Requirements & Constraints

### Performance Requirements
- Job manager polling interval: 5 seconds (configurable 1-60s)
- Task runner spawn time: <10 seconds
- Job status query: <100ms
- Task queue throughput: 50+ tasks/hour
- Memory footprint: <100MB for job manager, <500MB per task runner

### Compatibility Requirements
- **Platform Support**: Linux (primary), macOS (development), Windows WSL2 (limited)
- **Python Versions**: 3.11, 3.12
- **Kubernetes**: 1.24+ (for Airflow implementation)
- **Docker**: 20.10+ (for Prefect implementation)
- **Standards Compliance**: POSIX compliance for file operations, Kubernetes API v1

### Security & Compliance
- **Security Requirements**:
  - No secrets in job definitions
  - File-based access control for job directories
  - Kubernetes RBAC for Pod operations
  - Claude Code CLI authentication inheritance
- **Compliance Standards**: None (internal tooling)
- **Threat Model**:
  - Untrusted code execution in isolated runners
  - Job definition tampering prevention
  - Resource exhaustion limits

### Scalability & Reliability
- **Expected Load**: 10-100 concurrent jobs, 100-1000 tasks per day
- **Availability Requirements**: 99% uptime for job manager, best-effort for task runners
- **Growth Projections**: Linear scaling with job count, horizontal scaling via multiple job managers

## Technical Decisions & Rationale

### Decision Log

1. **Dual Implementation (Airflow + Prefect)**:
   - **Why**: Different infrastructure preferences (Kubernetes vs Docker/native Python)
   - **Alternatives**: Single implementation would limit adoption
   - **Trade-offs**: Increased maintenance burden, but broader applicability

2. **File-Based Job State**:
   - **Why**: Simple, no external dependencies, easy debugging
   - **Alternatives**: Database (added complexity), Redis (requires server)
   - **Trade-offs**: Not suitable for distributed scenarios, but adequate for MVP

3. **Polling vs Event-Driven**:
   - **Why**: Simpler to implement, works with any orchestrator
   - **Alternatives**: Webhooks, message queues (added complexity)
   - **Trade-offs**: Higher latency (5s), but predictable and reliable

4. **KubernetesExecutor for Airflow**:
   - **Why**: Native support for ephemeral, single-task Pods
   - **Alternatives**: CeleryExecutor (persistent workers, not aligned)
   - **Trade-offs**: Requires Kubernetes, but perfect architectural fit

5. **Claude Code CLI Wrapper**:
   - **Why**: Leverage existing AI capabilities without reimplementation
   - **Alternatives**: Direct API integration (more complex, less flexible)
   - **Trade-offs**: Dependency on CLI stability, but rapid integration

## Known Limitations

- **Single-Machine Job Manager**: Current implementation doesn't support distributed job management (file-based state)
  - **Impact**: Limited to single-region, single-instance deployment
  - **Future**: Database-backed state for multi-instance support

- **No Task Retry Logic**: Failed tasks require manual re-queuing
  - **Impact**: Reduced resilience for transient failures
  - **Future**: Configurable retry policies with exponential backoff

- **Limited Observability**: CLI-only monitoring in MVP
  - **Impact**: Difficult to diagnose issues in production
  - **Future**: Web dashboard with metrics and trace visualization

- **No Resource Limits**: Task runners can consume unbounded resources
  - **Impact**: Risk of resource exhaustion
  - **Future**: Kubernetes resource quotas, cgroup limits for Prefect
