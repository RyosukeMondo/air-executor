# Product Overview

## Product Purpose

Air-Executor is an autonomous job management system that orchestrates task execution through ephemeral, single-task runners. It solves the problem of managing complex, multi-step workflows where tasks can dynamically spawn sub-tasks based on runtime conditions, while maintaining clean resource lifecycle management and preventing concurrent execution conflicts.

## Target Users

**Primary Users: Development Teams and DevOps Engineers**

**Needs:**
- Automated execution of complex, multi-step workflows
- Dynamic task generation based on runtime results
- Resource-efficient execution with automatic cleanup
- Prevention of duplicate task runners for the same job
- Integration with Claude Code CLI for AI-assisted task execution

**Pain Points:**
- Manual orchestration of dependent tasks is error-prone
- Long-running workers waste resources during idle periods
- Difficult to manage dynamic workflows where task count isn't known upfront
- Risk of concurrent execution causing race conditions
- Lack of visibility into job status and task progress

## Key Features

1. **Ephemeral Task Runners**: Single-task execution pods/processes that start on-demand and terminate after completion, maximizing resource efficiency

2. **Job State Management**: Polling-based job manager that monitors job status every 5 seconds (configurable) and spawns runners only when needed

3. **Dynamic Task Queuing**: Task runners can queue additional sub-tasks during execution, enabling adaptive workflows that respond to runtime conditions

4. **Concurrency Control**: Ensures only one task runner is active per job at any time, preventing race conditions and resource conflicts

5. **Dual Implementation**: Support for both Apache Airflow (KubernetesExecutor) and Prefect for flexibility in infrastructure requirements

6. **Claude Code Integration**: Task runners wrap Claude Code CLI for AI-assisted task execution capabilities

## Business Objectives

- **Reduce Resource Waste**: Ephemeral runners minimize idle compute time by 80-90% compared to persistent workers
- **Enable Complex Workflows**: Support dynamic task generation for workflows where requirements emerge during execution
- **Improve Reliability**: Single-runner-per-job constraint eliminates race conditions and duplicate work
- **Lower Operational Overhead**: Automated lifecycle management reduces manual intervention by 95%
- **Accelerate Development**: AI-assisted task execution through Claude Code integration speeds up implementation

## Success Metrics

- **Resource Efficiency**: Average runner lifetime < 10 minutes, resource utilization > 70% during active execution
- **Execution Reliability**: 99%+ success rate for task completion without conflicts
- **Task Throughput**: Process 50+ tasks per hour per job with dynamic scaling
- **System Availability**: Job manager uptime > 99.5%
- **User Adoption**: 80% of new workflows use Air-Executor within 6 months

## Product Principles

1. **Ephemeral Over Persistent**: Favor short-lived, single-purpose execution units over long-running workers to minimize resource waste and maximize isolation

2. **Self-Contained Tasks**: Each task should be independently executable with clear inputs/outputs, enabling parallelization and retry without dependencies on runner state

3. **Progressive Disclosure**: Workflows can discover and queue sub-tasks dynamically rather than requiring complete task graphs upfront, supporting adaptive execution patterns

4. **Single Responsibility**: One runner per job at any time enforces clear ownership and prevents coordination complexity

5. **Infrastructure Agnostic**: Support multiple orchestration backends (Airflow, Prefect) to adapt to existing infrastructure rather than forcing specific technology choices

## Monitoring & Visibility

- **Dashboard Type**: CLI-based status reporting with optional web dashboard (future enhancement)
- **Real-time Updates**: Polling-based status checks every 5 seconds (configurable interval)
- **Key Metrics Displayed**:
  - Job status (working, waiting, completed)
  - Active task runner status
  - Task queue depth and completion rate
  - Runner spawn/termination events
  - Error states and retry attempts
- **Sharing Capabilities**: Job logs and status exports for team visibility and debugging

## Future Vision

### Potential Enhancements

- **Web Dashboard**: Real-time visualization of job status, task graphs, and resource utilization with tunnel support for remote access
- **Analytics & Insights**: Historical trends, performance metrics, bottleneck identification
- **Advanced Scheduling**: Cron-like scheduling, dependency-based triggers, external event integration
- **Multi-User Collaboration**: Shared job management, role-based access control, commenting and annotations
- **Smart Task Routing**: ML-based task complexity estimation for optimal resource allocation
- **Distributed Job Management**: Multi-region job execution with global coordination
- **Plugin Ecosystem**: Extensible task runner implementations for different execution environments (Docker, Kubernetes, serverless)
