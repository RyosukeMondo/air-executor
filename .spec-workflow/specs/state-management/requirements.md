# Requirements Document

## Introduction

Currently, autonomous fixing state is stored outside project directories (`/home/rmondo/repos/air-executor/config/*-cache/`), making it machine-specific, non-portable, and unable to detect external changes to configuration files. This feature moves state into project directories (`.ai-state/`) with smart invalidation logic that detects when hooks or tests are modified by other developers or tools.

**Value Proposition:** Enable cross-machine consistency, detect external configuration changes, improve debuggability through visible state files, and support team collaboration scenarios.

## Alignment with Product Vision

Aligns with:
- **Portability**: State travels with project (works across machines)
- **Reliability**: Detects external changes, prevents stale cache usage
- **Visibility**: State visible in project for debugging
- **Collaboration**: Team-aware (detects teammate changes to hooks/tests)

## Requirements

### Requirement 1: Project-Based State Storage

**User Story:** As a developer working across multiple machines, I want state stored in the project directory, so that setup decisions persist regardless of which machine I use.

#### Acceptance Criteria

1. WHEN setup phase completes THEN system SHALL write state to `{project}/.ai-state/{phase}_state.md`
2. WHEN writing state THEN system SHALL include: timestamp, config hash, validation markers
3. IF .ai-state directory missing THEN system SHALL create it with proper gitignore
4. WHEN checking gitignore THEN system SHALL add `.ai-state/` entry if not present
5. WHEN state file created THEN system SHALL use permissions 0644 (user writable, others read)

### Requirement 2: Smart Cache Invalidation

**User Story:** As a developer, I want the system to detect when configuration files change, so that outdated cached state doesn't cause incorrect behavior.

#### Acceptance Criteria

1. WHEN validating hook state THEN system SHALL check if `.pre-commit-config.yaml` modified after state creation
2. WHEN validating test state THEN system SHALL check if `package.json` modified after state creation
3. IF config file modified THEN system SHALL invalidate state AND re-run AI discovery
4. WHEN computing config hash THEN system SHALL use SHA256 of relevant config files
5. IF config hash changed from state THEN system SHALL invalidate cache

### Requirement 3: State File Format

**User Story:** As a developer debugging setup issues, I want state files to be human-readable with clear validation information, so I can understand why setup was skipped or re-run.

#### Acceptance Criteria

1. WHEN writing state THEN system SHALL use Markdown format with YAML frontmatter
2. WHEN including metadata THEN system SHALL provide: generated timestamp, status (CONFIGURED/DISCOVERED), config hash
3. WHEN documenting validation THEN system SHALL list computational checks performed
4. WHEN explaining invalidation THEN system SHALL document cache invalidation triggers
5. IF state file corrupted THEN system SHALL log error AND re-run setup (fail-safe)

### Requirement 4: Backward Compatibility

**User Story:** As a system maintainer, I want to support existing external cache location temporarily, so that migration doesn't break active workflows.

#### Acceptance Criteria

1. WHEN checking state THEN system SHALL check `.ai-state/` first, THEN fallback to `config/*-cache/`
2. IF external cache exists AND newer than project state THEN system SHALL use external cache (migration period)
3. WHEN writing new state THEN system SHALL write to `.ai-state/` only (no dual-write)
4. WHEN migrating THEN system SHALL log: "Migrating state from config/ to .ai-state/"
5. AFTER 30 days THEN system MAY remove external cache fallback (deprecation)

## Non-Functional Requirements

### Code Architecture and Modularity
- State manager is independent module: `core/state_manager.py`
- No circular dependencies (state → nothing, validators → state)
- Clear interfaces: `save_state(phase, data)`, `load_state(phase)`, `should_reconfigure(phase)`

### Performance
- State file operations MUST complete in <50ms (read + parse)
- Config hash calculation MUST use efficient file reading (stream, not load full file)
- Gitignore check/update MUST complete in <10ms

### Security
- State files MUST NOT contain secrets or credentials
- State directory MUST be gitignored by default
- File operations MUST validate paths (prevent directory traversal)

### Reliability
- Corrupted state MUST trigger re-run (fail-safe, no silent failures)
- Missing state directory MUST be created automatically
- Concurrent access MUST be safe (atomic file writes)

### Usability
- State files MUST be human-readable (developers can inspect)
- Error messages MUST indicate which file caused invalidation
- Logs MUST show migration status during transition period
