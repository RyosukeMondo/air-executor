# Requirements Document

## Introduction

The autonomous fixing system currently suffers from redundant setup phases that waste AI call time and API costs. Every execution runs hook configuration (37-261s) and test discovery (85-97s) even when these operations completed successfully in previous runs. This feature implements pre-flight validation and persistent state tracking to eliminate 99% of redundant setup calls, reducing execution time by 2-4 minutes per run and API costs by approximately $0.80 per redundant execution.

**Value Proposition:** Enable sophisticated, cost-efficient autonomous fixing by computationally validating prerequisites before invoking AI, eliminating wasteful re-execution of already-completed setup tasks.

## Alignment with Product Vision

This feature aligns with Air-Executor's core product principles:

- **Resource Efficiency**: Reduces idle AI time by 99% for setup phases, minimizing waste
- **Operational Overhead Reduction**: Automated cache validation eliminates manual "already configured" checks
- **Reliability Improvement**: Computational validation ensures consistent setup state detection
- **Cost Optimization**: Saves ~$0.80 per run + 120-240s execution time through intelligent skip logic

Supports Business Objective: **Reduce Resource Waste** by applying ephemeral execution principles to AI invocations themselves.

## Requirements

### Requirement 1: Pre-Flight Validation Layer

**User Story:** As a DevOps engineer running autonomous fixing, I want the system to computationally verify setup completion before calling AI, so that I don't waste time and money re-configuring already-configured projects.

#### Acceptance Criteria

1. WHEN hook configuration validation is requested THEN system SHALL check `.pre-commit-config.yaml`, `.git/hooks/pre-commit` existence AND cache file validity (<7 days) within 100ms
2. WHEN test discovery validation is requested THEN system SHALL check `config/test-cache/{project}-tests.yaml` existence AND freshness (<7 days) within 50ms
3. IF validation finds valid cached state THEN system SHALL skip AI invocation AND log skip reason
4. WHEN validation detects missing or stale state THEN system SHALL proceed with AI invocation AND update cache afterward
5. WHEN validation runs THEN system SHALL return tuple `(can_skip: bool, reason: str)` for logging transparency

### Requirement 2: State Persistence System

**User Story:** As a DevOps engineer, I want setup completion tracked persistently across sessions, so that re-running autonomous fixing doesn't repeat completed work.

#### Acceptance Criteria

1. WHEN setup phase completes successfully THEN system SHALL write state marker to `.ai-state/{phase}_complete.marker` with ISO timestamp
2. IF Redis is configured THEN system SHALL store state in Redis with key `setup:{project}:{phase}` AND TTL of 30 days
3. WHEN checking setup completion THEN system SHALL query Redis first, THEN fallback to filesystem markers
4. IF state marker exists AND age < 30 days THEN system SHALL report setup as complete
5. WHEN state marker is older than 30 days THEN system SHALL treat as stale AND re-run setup with AI
6. WHEN AI setup fails THEN system SHALL NOT create completion marker

### Requirement 3: Cache Validation Enhancement

**User Story:** As a developer, I want cache files validated for correctness before being trusted, so that corrupted or incomplete cache doesn't cause silent failures.

#### Acceptance Criteria

1. WHEN validating hook configuration cache THEN system SHALL verify YAML parsability AND presence of `hook_framework.installed: true` field
2. WHEN validating test discovery cache THEN system SHALL verify YAML parsability AND presence of required fields: `test_framework`, `test_command`, `test_patterns`
3. IF cache file is corrupted or missing required fields THEN system SHALL invalidate cache AND re-run AI discovery
4. WHEN cache validation fails THEN system SHALL log warning with corruption details AND proceed with AI invocation
5. WHEN AI writes new cache THEN system SHALL include validation marker: `config_hash: <sha256>` for integrity checking

### Requirement 4: Integration with Iteration Engine

**User Story:** As a system integrator, I want pre-flight validation integrated seamlessly into existing orchestrator loop, so that setup optimization works without breaking current workflows.

#### Acceptance Criteria

1. WHEN iteration engine starts setup phase 0 (hooks) THEN system SHALL invoke `PreflightValidator.can_skip_hook_config()` before AI call
2. WHEN iteration engine starts setup phase 1 (tests) THEN system SHALL invoke `PreflightValidator.can_skip_test_discovery()` before AI call
3. IF validator returns `can_skip=True` THEN system SHALL log skip reason AND continue to next project without AI invocation
4. WHEN all projects skip setup THEN system SHALL log summary: "⏭️ Skipped setup for N projects (savings: Xs + $Y)"
5. WHEN validator indicates re-run needed THEN system SHALL call existing `fixer.configure_precommit_hooks()` or `fixer.discover_test_config()` as before

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: `PreflightValidator` handles only validation logic, not AI invocation
- **Modular Design**: Validator is independent, reusable component in `airflow_dags/autonomous_fixing/core/validators/`
- **Dependency Management**: Validator depends only on `pathlib`, `time`, `yaml` (no circular dependencies)
- **Clear Interfaces**: Validator returns consistent `tuple[bool, str]` for all validation methods

### Performance
- Pre-flight validation MUST complete in <200ms for all checks (hook + test + state) per project
- Filesystem access MUST be minimized (max 3 file reads per validation)
- Redis queries MUST have 100ms timeout to prevent blocking
- Validation overhead MUST be <1% of AI invocation time it replaces

### Security
- Cache files MUST NOT contain secrets or sensitive project data
- State markers MUST use restrictive permissions (0600) to prevent tampering
- Redis keys MUST include project path hash to prevent cross-project leakage
- File operations MUST validate paths to prevent directory traversal

### Reliability
- Validation MUST fail-safe: if uncertain, proceed with AI invocation (no false skips)
- Cache corruption MUST NOT prevent system operation (graceful degradation)
- Stale marker cleanup MUST handle concurrent access without race conditions
- System MUST work identically with or without Redis (Redis is optional enhancement)

### Usability
- Skip decisions MUST be logged clearly with savings estimate: "⏭️ Skipped hooks (saved 60s + $0.50)"
- Validation failures MUST log actionable error messages
- First-run behavior MUST be intuitive (no skips, all setup runs as expected)
- Summary statistics MUST show total savings per orchestrator run
