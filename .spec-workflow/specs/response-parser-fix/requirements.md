# Requirements Document

## Introduction

The autonomous fixing system currently reports false failures when AI operations complete successfully but produce non-critical stderr output (deprecation warnings, experimental feature notices). This causes unnecessary re-runs, wasted debugging time, and confusion. For example, hook configuration completes with `run_status: completed` and `exit_code: 0`, but gets marked as "❌ Hook configuration failed: Unknown error" due to punycode deprecation warnings in stderr.

**Value Proposition:** Eliminate false negatives by implementing intelligent error detection that distinguishes real errors from benign warnings, improving system reliability and reducing wasted debugging effort.

## Alignment with Product Vision

This feature aligns with Air-Executor's core principles:

- **Reliability Improvement**: Accurate success/failure detection prevents incorrect orchestrator decisions
- **Operational Overhead Reduction**: Eliminates manual investigation of false failures
- **Improve User Experience**: Clear, actionable error messages when real failures occur
- **Resource Efficiency**: Prevents unnecessary re-runs triggered by false failures

Supports Business Objective: **Improve Reliability** by ensuring 99%+ success rate for task completion detection.

## Requirements

### Requirement 1: Intelligent Error Detection

**User Story:** As a DevOps engineer, I want the system to distinguish real errors from benign warnings in stderr, so that successful operations aren't incorrectly marked as failed.

#### Acceptance Criteria

1. WHEN wrapper returns `run_status: completed` AND `exit_code: 0` THEN system SHALL analyze stderr for real errors before marking as failure
2. IF stderr contains only noise patterns (deprecation warnings, experimental features, skipped files) THEN system SHALL mark operation as SUCCESS
3. IF stderr contains error indicators (Error:, FAILED:, Exception, Traceback) THEN system SHALL mark operation as FAILURE with extracted error message
4. WHEN filtering stderr THEN system SHALL use configurable noise pattern list: `["punycode", "ExperimentalWarning", "Skipping files", "DeprecationWarning"]`
5. WHEN extracting errors THEN system SHALL return first 3 real error lines for actionable debugging

### Requirement 2: Configurable Noise Filtering

**User Story:** As a system administrator, I want to configure which stderr patterns are considered noise, so that the system adapts to different tooling ecosystems without code changes.

#### Acceptance Criteria

1. WHEN parsing responses THEN system SHALL load noise patterns from `config/error_patterns.yaml` if exists
2. IF config file missing THEN system SHALL use default noise patterns from code
3. WHEN config updated THEN system SHALL apply new patterns on next orchestrator run (no restart required)
4. WHEN adding noise pattern THEN admin SHALL specify pattern type: `substring` or `regex`
5. WHEN config invalid THEN system SHALL log warning AND use default patterns

### Requirement 3: Error Message Enhancement

**User Story:** As a developer debugging failures, I want clear, actionable error messages with context, so that I can quickly identify and fix issues.

#### Acceptance Criteria

1. WHEN real error detected THEN system SHALL return dict with: `{"success": False, "errors": [list], "error_message": "first 3 lines joined"}`
2. WHEN operation succeeds THEN system SHALL return dict with: `{"success": True, "status": "completed"}`
3. IF wrapper times out THEN system SHALL return: `{"success": False, "error_message": "Operation timed out after {timeout}s"}`
4. IF wrapper crashes THEN system SHALL return: `{"success": False, "error_message": "Wrapper crashed: {exception}"}`
5. WHEN logging errors THEN system SHALL include operation type (configure_hooks, discover_tests, fix_error) for context

### Requirement 4: Backward Compatibility

**User Story:** As a system maintainer, I want response parsing changes to be backward compatible, so that existing integrations continue working without modifications.

#### Acceptance Criteria

1. WHEN IssueFixer receives response THEN it SHALL handle both old format (success: bool) AND new format (dict with status)
2. IF response format unknown THEN system SHALL log warning AND treat as failure (fail-safe)
3. WHEN upgrading THEN existing DebugLogger calls SHALL continue working without modifications
4. IF ClaudeClient returns old format THEN parser SHALL convert to new format automatically
5. WHEN testing THEN both formats SHALL be tested for compatibility

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: `ResponseParser` handles only response parsing, not AI invocation
- **Modular Design**: Parser is independent, reusable component in `airflow_dags/autonomous_fixing/adapters/ai/`
- **Dependency Management**: Parser depends only on `yaml`, `re` (no AI/wrapper dependencies)
- **Clear Interfaces**: Parser returns consistent `dict` format for all operations

### Performance
- Response parsing MUST complete in <10ms per response
- Noise pattern matching MUST use efficient substring search (not regex) for common patterns
- Config file loading MUST be cached (load once per orchestrator run, not per parse)
- Parser overhead MUST be <0.1% of wrapper execution time

### Security
- Error messages MUST NOT include secrets or sensitive file contents
- Config file MUST validate patterns to prevent ReDoS (regex denial of service)
- Parser MUST sanitize user-provided patterns before regex compilation
- Extracted errors MUST truncate at 500 chars to prevent log flooding

### Reliability
- Parser MUST fail-safe: uncertain → mark as failure (no false successes)
- Malformed response MUST NOT crash parser (graceful error handling)
- Invalid config MUST NOT prevent system startup (fallback to defaults)
- Parser MUST handle unicode in stderr/stdout correctly

### Usability
- Error messages MUST be actionable (include operation type, first error line, context)
- Config file MUST include examples and comments for each pattern type
- Logs MUST clearly indicate when using default vs custom patterns
- False negatives MUST be detectable (log raw stderr when marking as success)
