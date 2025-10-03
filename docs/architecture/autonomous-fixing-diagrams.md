# Autonomous Fixing - System Design Diagrams

Comprehensive system design diagrams for the autonomous code fixing system using Mermaid.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Priority-Based Execution Flow](#priority-based-execution-flow)
- [Multi-Language Orchestration](#multi-language-orchestration)
- [Health Monitoring System](#health-monitoring-system)
- [Issue Discovery & Batching](#issue-discovery--batching)
- [State Management](#state-management)
- [Execution Modes](#execution-modes)
- [Integration Points](#integration-points)

## High-Level Architecture

### System Overview

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI Scripts]
        PM2[PM2 Process Manager]
        Airflow[Airflow Web UI]
    end

    subgraph "Orchestration Layer"
        Orch[Multi-Language Orchestrator]
        Config[Configuration Manager]
        State[State Manager]
    end

    subgraph "Language Adapters"
        Python[Python Adapter]
        JS[JavaScript Adapter]
        Flutter[Flutter Adapter]
        Go[Go Adapter]
    end

    subgraph "Execution Layer"
        Health[Health Monitor]
        Discovery[Issue Discovery]
        Batch[Issue Batching]
        Executor[Air-Executor Runner]
    end

    subgraph "External Services"
        Claude[Claude AI CLI]
        Redis[(Redis)]
        Git[Git Repository]
    end

    CLI --> Orch
    PM2 --> Orch
    Airflow --> Orch

    Orch --> Config
    Orch --> State
    Orch --> Python
    Orch --> JS
    Orch --> Flutter
    Orch --> Go

    Python --> Health
    JS --> Health
    Flutter --> Health
    Go --> Health

    Health --> Discovery
    Discovery --> Batch
    Batch --> Executor

    Executor --> Claude
    State --> Redis
    Executor --> Git

    State -.->|Queue Management| Batch
    State -.->|Session Context| Executor

    style Orch fill:#f9f,stroke:#333,stroke-width:4px
    style Claude fill:#bbf,stroke:#333,stroke-width:2px
    style Redis fill:#fbb,stroke:#333,stroke-width:2px
```

### Component Relationships

```mermaid
graph LR
    subgraph "Core Components"
        O[Orchestrator]
        H[Health Monitor]
        D[Issue Discovery]
        B[Issue Batching]
        E[Executor]
        S[State Manager]
    end

    O -->|1. Check Health| H
    O -->|2. Route by Priority| D
    D -->|3. Group Issues| B
    B -->|4. Queue Tasks| S
    S -->|5. Get Next Tasks| E
    E -->|6. Execute Fixes| Claude[Claude AI]
    E -->|7. Commit Changes| Git[Git]
    E -->|8. Update State| S
    S -->|9. Check Completion| O

    style O fill:#f9f
    style Claude fill:#bbf
```

## Priority-Based Execution Flow

### Complete Execution Lifecycle

```mermaid
flowchart TD
    Start([Start Autonomous Fixing]) --> Init[Initialize Orchestrator]
    Init --> LoadConfig[Load Configuration]
    LoadConfig --> DetectLang[Detect Project Language]

    DetectLang --> P1Start{Priority 1: Static Analysis}

    subgraph "P1: Static Analysis (ALWAYS RUN)"
        P1Start --> P1Run[Run Linters & Type Checkers]
        P1Run --> P1Analyze[Analyze File Sizes & Complexity]
        P1Analyze --> P1Score[Calculate P1 Score]
        P1Score --> P1Gate{Score ≥ 90%?}
    end

    P1Gate -->|No| P1Fix[Fix P1 Issues]
    P1Fix --> P1Commit[Commit Fixes]
    P1Commit --> P1Recheck[Re-run P1]
    P1Recheck --> P1Gate

    P1Gate -->|Yes| P2Start{Priority 2: Tests}

    subgraph "P2: Strategic Tests (ADAPTIVE)"
        P2Start --> P2Strategy{Determine Strategy}
        P2Strategy -->|Health < 30%| P2Minimal[Minimal Tests - 5min]
        P2Strategy -->|Health 30-60%| P2Selective[Selective Tests - 15min]
        P2Strategy -->|Health > 60%| P2Comprehensive[Comprehensive Tests - 30min]

        P2Minimal --> P2Run[Run Tests]
        P2Selective --> P2Run
        P2Comprehensive --> P2Run

        P2Run --> P2Score[Calculate Pass Rate]
        P2Score --> P2Gate{Pass Rate ≥ 85%?}
    end

    P2Gate -->|No| P2Fix[Fix Test Failures]
    P2Fix --> P2Commit[Commit Fixes]
    P2Commit --> P2Recheck[Re-run Tests]
    P2Recheck --> P2Gate

    P2Gate -->|Yes| P3Gate{P3 Gate Check}

    subgraph "P3: Coverage (CONDITIONAL)"
        P3Gate -->|P1≥90% AND P2≥85%| P3Start[Analyze Coverage]
        P3Start --> P3Gaps[Identify Coverage Gaps]
        P3Gaps --> P3Gen[Generate Tests]
        P3Gen --> P3Commit[Commit New Tests]
        P3Commit --> P4Gate{P4 Gate Check}
    end

    P3Gate -->|Not Ready| Complete

    subgraph "P4: E2E (FINAL)"
        P4Gate -->|Health ≥ 90%| P4Start[Run E2E Tests]
        P4Start --> P4Errors[Capture Runtime Errors]
        P4Errors --> P4Fix[Add Regression Tests]
        P4Fix --> P4Commit[Commit Tests]
        P4Commit --> Complete
    end

    P4Gate -->|Not Ready| Complete

    Complete{Completion Check}
    Complete -->|Not Done| CheckCircuit{Circuit Breaker}
    CheckCircuit -->|OK| P1Start
    CheckCircuit -->|Triggered| Stop([Stop - Circuit Breaker])
    Complete -->|All Criteria Met| Success([Success - All Done])

    style P1Start fill:#ff9999
    style P2Start fill:#ffcc99
    style P3Gate fill:#99ccff
    style P4Gate fill:#99ff99
    style Success fill:#90EE90
    style Stop fill:#FFB6C1
```

### Adaptive Test Strategy Selection

```mermaid
flowchart LR
    Start[P1 Complete] --> CalcHealth[Calculate Health Score]

    CalcHealth --> Decision{Health Score}

    Decision -->|< 30%| Minimal[Minimal Strategy]
    Decision -->|30-60%| Selective[Selective Strategy]
    Decision -->|> 60%| Comprehensive[Comprehensive Strategy]

    Minimal --> M1[Run: Critical Tests Only]
    M1 --> M2[Duration: ~5 min]
    M2 --> M3[Coverage: Core paths]

    Selective --> S1[Run: Changed Files + Smoke]
    S1 --> S2[Duration: ~15 min]
    S2 --> S3[Coverage: Key scenarios]

    Comprehensive --> C1[Run: Full Test Suite]
    C1 --> C2[Duration: ~30 min]
    C2 --> C3[Coverage: All tests]

    M3 --> Execute[Execute Test Strategy]
    S3 --> Execute
    C3 --> Execute

    Execute --> Results[Analyze Results]

    style Decision fill:#f9f
    style Minimal fill:#fbb
    style Selective fill:#ffb
    style Comprehensive fill:#bfb
```

## Multi-Language Orchestration

### Language Detection & Routing

```mermaid
flowchart TD
    Start([Project Path]) --> Detect[Auto-Detect Language]

    Detect --> CheckPython{pubspec.yaml?}
    Detect --> CheckJS{package.json?}
    Detect --> CheckFlutter{pubspec.yaml?}
    Detect --> CheckGo{go.mod?}

    CheckPython -->|Yes| Python[Python Adapter]
    CheckJS -->|Yes| JavaScript[JavaScript Adapter]
    CheckFlutter -->|Yes| Flutter[Flutter Adapter]
    CheckGo -->|Yes| Go[Go Adapter]

    Python --> PyTools[Load Python Tools]
    JavaScript --> JSTools[Load JS Tools]
    Flutter --> FlutterTools[Load Flutter Tools]
    Go --> GoTools[Load Go Tools]

    PyTools --> PyConfig[pylint, mypy, pytest]
    JSTools --> JSConfig[eslint, tsc, jest]
    FlutterTools --> FlutterConfig[flutter analyze, test]
    GoTools --> GoConfig[go vet, staticcheck]

    PyConfig --> Execute[Execute P1-P4 Pipeline]
    JSConfig --> Execute
    FlutterConfig --> Execute
    GoConfig --> Execute

    style Detect fill:#f9f
    style Execute fill:#bfb
```

### Parallel Multi-Project Execution

```mermaid
gantt
    title Multi-Language Parallel Execution Timeline
    dateFormat YYYY-MM-DD
    axisFormat %H:%M:%S

    section Project Detection
    Detect all projects           :2025-01-01, 10s

    section P1: Static (Parallel)
    Python: pylint + mypy         :2025-01-01, 30s
    JavaScript: eslint + tsc      :2025-01-01, 30s
    Flutter: analyze              :2025-01-01, 30s
    Go: vet + staticcheck         :2025-01-01, 30s

    section P1: Analysis
    Aggregate results             :2025-01-01, 10s

    section P2: Tests (Parallel)
    Python: pytest                :2025-01-01, 300s
    JavaScript: jest              :2025-01-01, 300s
    Flutter: test                 :2025-01-01, 300s
    Go: test                      :2025-01-01, 300s

    section P2: Analysis
    Aggregate test results        :2025-01-01, 10s

    section Fixing (Sequential per project)
    Fix Python issues             :2025-01-01, 180s
    Fix JavaScript issues         :2025-01-01, 180s
    Fix Flutter issues            :2025-01-01, 180s
    Fix Go issues                 :2025-01-01, 180s
```

## Health Monitoring System

### Health Score Calculation

```mermaid
flowchart LR
    subgraph "Health Inputs"
        Build[Build Status]
        Tests[Test Results]
        Quality[Code Quality]
        Analysis[Static Analysis]
    end

    subgraph "Score Calculation"
        Build --> BuildScore[Build Score<br/>30% weight]
        Tests --> TestScore[Test Score<br/>30% weight]
        Quality --> QualityScore[Quality Score<br/>20% weight]
        Analysis --> AnalysisScore[Analysis Score<br/>20% weight]
    end

    subgraph "Aggregation"
        BuildScore --> Aggregate[Weighted Sum]
        TestScore --> Aggregate
        QualityScore --> Aggregate
        AnalysisScore --> Aggregate
    end

    Aggregate --> Final[Overall Health Score<br/>0-100%]

    Final --> Rating{Score Range}
    Rating -->|< 30%| Critical[Critical]
    Rating -->|30-60%| NeedsAttention[Needs Attention]
    Rating -->|60-85%| Good[Good]
    Rating -->|> 85%| Excellent[Excellent]

    style Final fill:#f9f
    style Critical fill:#fbb
    style NeedsAttention fill:#ffb
    style Good fill:#bfb
    style Excellent fill:#9f9
```

### Metrics Collection Pipeline

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant H as Health Monitor
    participant LA as Language Adapter
    participant Tools as External Tools
    participant Metrics as Metrics Store

    O->>H: Request Health Check
    H->>LA: Get Language Adapter
    LA->>Tools: Run Static Analysis
    Tools-->>LA: Analysis Results
    LA->>Tools: Run Tests
    Tools-->>LA: Test Results
    LA->>Tools: Run Coverage
    Tools-->>LA: Coverage Results
    LA->>Tools: Calculate Complexity
    Tools-->>LA: Complexity Metrics

    LA->>H: Aggregate Metrics
    H->>H: Calculate Health Score
    H->>Metrics: Store Metrics
    H-->>O: Health Report

    Note over O,Metrics: Metrics include:<br/>- Build status<br/>- Test pass rate<br/>- Coverage %<br/>- Code quality
```

## Issue Discovery & Batching

### Issue Discovery Flow

```mermaid
flowchart TD
    Start[Health Check Complete] --> Phase{Select Phase}

    Phase -->|P1 < 90%| Build[Build Phase]
    Phase -->|P2 < 85%| Test[Test Phase]
    Phase -->|Otherwise| Lint[Lint Phase]

    Build --> RunBuild[Run Build Command]
    Test --> RunTest[Run Test Command]
    Lint --> RunLint[Run Lint Command]

    RunBuild --> ParseBuild[Parse Build Output]
    RunTest --> ParseTest[Parse Test Output]
    RunLint --> ParseLint[Parse Lint Output]

    ParseBuild --> ExtractBuild[Extract Error Messages]
    ParseTest --> ExtractTest[Extract Failures]
    ParseLint --> ExtractLint[Extract Violations]

    ExtractBuild --> Issues[Raw Issues List]
    ExtractTest --> Issues
    ExtractLint --> Issues

    Issues --> Group[Issue Grouping]

    Group --> Batching{Batching Mode?}

    Batching -->|Mega| MegaBatch[Create ONE mega-batch]
    Batching -->|Smart| SmartBatch[Group by Type & Location]
    Batching -->|Individual| Individual[Keep as Individual Tasks]

    MegaBatch --> Queue[Queue Tasks]
    SmartBatch --> Queue
    Individual --> Queue

    Queue --> Redis[(Redis Task Queue)]

    style Issues fill:#f9f
    style Queue fill:#bfb
```

### Smart Batching Logic

```mermaid
flowchart TD
    Start[Raw Issues] --> Analyze[Analyze Issue Types]

    Analyze --> Cleanup{Cleanup Issues?}
    Analyze --> Location{Location-Based?}
    Analyze --> Other{Other Issues}

    Cleanup -->|unused_imports<br/>formatting<br/>etc.| CleanupBatch[Cleanup Batch]
    CleanupBatch --> CleanupSize{Count ≥ 3?}
    CleanupSize -->|Yes| CreateCleanup[Create Cleanup Batch]
    CleanupSize -->|No| Individual1[Keep Individual]

    Location -->|Same directory<br/>type_errors<br/>null_safety| LocationBatch[Location Batch]
    LocationBatch --> LocationSize{Count ≥ 3?}
    LocationSize -->|Yes| CreateLocation[Create Location Batch]
    LocationSize -->|No| Individual2[Keep Individual]

    Other --> Individual3[Keep Individual]

    CreateCleanup --> Batches[Batched Tasks]
    CreateLocation --> Batches
    Individual1 --> Tasks[Individual Tasks]
    Individual2 --> Tasks
    Individual3 --> Tasks

    Batches --> Queue[Priority Queue]
    Tasks --> Queue

    Queue --> Execute[Execute Tasks]

    style Analyze fill:#f9f
    style Batches fill:#bfb
    style Tasks fill:#ffb
```

### Batching Mode Comparison

```mermaid
graph TB
    subgraph "Mega Batch Mode"
        M1[100 Issues] --> M2[1 Mega-Batch]
        M2 --> M3[1 Claude Session]
        M3 --> M4[1 Commit]
        M4 --> M5[~15 min]
    end

    subgraph "Smart Batch Mode"
        S1[100 Issues] --> S2[5-7 Batches]
        S2 --> S3[5-7 Claude Sessions]
        S3 --> S4[5-7 Commits]
        S4 --> S5[~60 min]
    end

    subgraph "Individual Mode"
        I1[100 Issues] --> I2[100 Tasks]
        I2 --> I3[100 Claude Sessions]
        I3 --> I4[100 Commits]
        I4 --> I5[~150 min]
    end

    style M2 fill:#fbb
    style S2 fill:#ffb
    style I2 fill:#bfb
```

## State Management

### Redis State Schema

```mermaid
erDiagram
    TASK_QUEUE ||--o{ TASK : contains
    RUN_HISTORY ||--o{ RUN : contains
    SESSION_SUMMARY ||--o{ SUMMARY : contains
    CIRCUIT_BREAKER ||--|| STATE : tracks

    TASK {
        string task_id PK
        string type
        int priority
        string file
        string message
        json context
        int retry_count
        timestamp created_at
    }

    RUN {
        string run_id PK
        timestamp timestamp
        float health_score
        json metrics
        string phase
        int iteration
    }

    SUMMARY {
        string phase PK
        int fixed_count
        int total_count
        json patterns
        timestamp timestamp
    }

    STATE {
        int failure_count
        timestamp last_failure
        bool circuit_open
        int total_runs
    }
```

### State Flow

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant S as State Manager
    participant R as Redis
    participant E as Executor

    O->>S: Queue Tasks
    S->>R: ZADD task_queue
    Note over R: Tasks stored<br/>with priority scores

    O->>S: Get Next Tasks (batch_size=3)
    S->>R: ZRANGE task_queue 0 2
    R-->>S: Top 3 Tasks
    S-->>O: Task Batch

    O->>E: Execute Task Batch
    E-->>O: Results

    O->>S: Mark Tasks Complete
    S->>R: ZREM task_queue

    O->>S: Store Run History
    S->>R: LPUSH run_history
    S->>R: LTRIM run_history 0 9

    O->>S: Store Session Summary
    S->>R: SETEX summary:build

    O->>S: Check Circuit Breaker
    S->>R: GET failure_count
    R-->>S: Count
    S-->>O: Circuit State
```

## Execution Modes

### PM2 vs Airflow Execution

```mermaid
flowchart LR
    subgraph "PM2 Mode"
        PM2Start[pm2 start] --> PM2Process[Background Process]
        PM2Process --> PM2Logs[pm2 logs]
        PM2Logs --> PM2Terminal[Terminal Output]
        PM2Terminal --> PM2File[Log Files]
    end

    subgraph "Airflow Mode"
        AirflowTrigger[Trigger DAG] --> AirflowTask[PythonOperator]
        AirflowTask --> AirflowStream[Streaming Subprocess]
        AirflowStream --> AirflowUI[Web UI Logs]
        AirflowUI --> AirflowDB[(Airflow DB)]
    end

    subgraph "Common Core"
        PM2Process --> Orch[Orchestrator]
        AirflowStream --> Orch
        Orch --> Execute[Execute Fixes]
        Execute --> Results[Results]
    end

    Results --> PM2File
    Results --> AirflowDB

    style PM2Mode fill:#ffb
    style AirflowMode fill:#bbf
    style Orch fill:#f9f
```

### Simulation vs Live Mode

```mermaid
flowchart TD
    Start[Start Execution] --> Mode{Execution Mode?}

    Mode -->|simulation=true| SimPath[Simulation Path]
    Mode -->|simulation=false| LivePath[Live Path]

    SimPath --> SimHealth[Check Health]
    SimHealth --> SimDiscover[Discover Issues]
    SimDiscover --> SimBatch[Create Batches]
    SimBatch --> SimPrint[Print What Would Execute]
    SimPrint --> SimEnd[End - No Changes Made]

    LivePath --> LiveHealth[Check Health]
    LiveHealth --> LiveDiscover[Discover Issues]
    LiveDiscover --> LiveBatch[Create Batches]
    LiveBatch --> LiveExecute[Execute via Claude]
    LiveExecute --> LiveCommit[Git Commit]
    LiveCommit --> LiveCheck{More Iterations?}
    LiveCheck -->|Yes| LiveHealth
    LiveCheck -->|No| LiveEnd[End - Changes Committed]

    style SimPath fill:#ffb
    style LivePath fill:#bfb
    style SimEnd fill:#ddd
    style LiveEnd fill:#9f9
```

## Integration Points

### Claude AI Integration

```mermaid
sequenceDiagram
    participant E as Executor
    participant W as Claude Wrapper
    participant CLI as Claude CLI
    participant API as Claude API

    E->>W: Execute Task
    Note over E,W: Prepare narrow context<br/>- File context<br/>- Error message<br/>- Fix instructions

    W->>W: Build JSON Request
    W->>CLI: Send via stdin

    CLI->>API: HTTP Request
    API-->>CLI: Stream Response

    CLI-->>W: Stdout Events
    Note over W: Parse streaming events:<br/>- thinking<br/>- code_changes<br/>- complete

    W->>W: Aggregate Results
    W-->>E: Final Output

    E->>E: Parse Output
    E->>Git: Commit Changes
```

### Git Integration Flow

```mermaid
flowchart LR
    Start[Task Complete] --> Check[Check Git Status]
    Check --> Stage[Stage Changes]
    Stage --> Commit[Create Commit]

    Commit --> MsgType{Batch Type?}

    MsgType -->|Mega| MegaMsg[fix: comprehensive cleanup<br/>of N issues]
    MsgType -->|Cleanup| CleanupMsg[chore: remove all<br/>unused_imports]
    MsgType -->|Location| LocationMsg[fix: type_errors<br/>in home/]
    MsgType -->|Individual| IndividualMsg[fix: specific error<br/>in file.dart]

    MegaMsg --> GitCommit[git commit]
    CleanupMsg --> GitCommit
    LocationMsg --> GitCommit
    IndividualMsg --> GitCommit

    GitCommit --> Record[Record in State]
    Record --> Next[Next Task]

    style GitCommit fill:#bfb
```

### Complete Integration Architecture

```mermaid
graph TB
    subgraph "External Systems"
        User[User]
        Git[Git Repository]
        Claude[Claude AI]
        Redis[(Redis)]
    end

    subgraph "Air Executor"
        Scripts[Script Layer]
        Orchestrator[Orchestrator]
        Adapters[Language Adapters]
        Execution[Execution Layer]
    end

    subgraph "Monitoring"
        Logs[Log Files]
        PM2UI[PM2 UI]
        AirflowUI[Airflow UI]
    end

    User -->|CLI| Scripts
    User -->|PM2| Scripts
    User -->|Airflow| Scripts

    Scripts --> Orchestrator

    Orchestrator <--> Redis
    Orchestrator --> Adapters

    Adapters --> Execution

    Execution --> Claude
    Execution --> Git

    Execution --> Logs
    Scripts --> PM2UI
    Scripts --> AirflowUI

    Logs --> User
    PM2UI --> User
    AirflowUI --> User

    style Orchestrator fill:#f9f,stroke:#333,stroke-width:4px
    style Claude fill:#bbf
    style Redis fill:#fbb
```

## Data Flow Diagrams

### End-to-End Data Flow

```mermaid
flowchart TD
    User[User Trigger] --> Config[Load Config]
    Config --> Detect[Detect Language]

    Detect --> Health[Collect Health Metrics]
    Health -->|Build Status<br/>Test Results<br/>Code Quality| Score[Calculate Score]

    Score --> Phase{Select Phase}
    Phase -->|P1| Static[Static Analysis]
    Phase -->|P2| Tests[Test Execution]
    Phase -->|P3| Coverage[Coverage Analysis]

    Static --> Issues[Issue List]
    Tests --> Issues
    Coverage --> Issues

    Issues --> Batch[Batch Issues]
    Batch --> Queue[Task Queue]

    Queue --> Executor[Executor]
    Executor --> Claude[Claude AI]
    Claude --> Fixes[Code Fixes]

    Fixes --> Git[Git Commit]
    Git --> State[Update State]

    State --> Check{Complete?}
    Check -->|No| Health
    Check -->|Yes| Done[Done]

    style User fill:#f9f
    style Claude fill:#bbf
    style Done fill:#9f9
```

---

## Usage Examples

### Viewing Diagrams

These Mermaid diagrams render automatically on:
- **GitHub**: View this file on GitHub
- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **Online**: Copy to https://mermaid.live

### Diagram Categories

1. **Architecture Diagrams**: System overview, component relationships
2. **Flow Diagrams**: Execution flows, decision trees
3. **Sequence Diagrams**: Component interactions, message flow
4. **State Diagrams**: State management, data schemas
5. **Integration Diagrams**: External system integration

### Creating New Diagrams

Follow this template:

```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action]
    B -->|No| D[Alternative]
    C --> E[End]
    D --> E

    style A fill:#f9f
    style E fill:#9f9
```

## See Also

- **Main Docs**: `/docs/AUTONOMOUS_FIXING.md` - Complete guide
- **Implementation**: `/airflow_dags/autonomous_fixing/` - Source code
- **Configuration**: `/docs/CONFIGURATION.md` - Config reference

---

**Last Updated**: 2025-01-10
**Diagram Format**: Mermaid (GitHub compatible)
