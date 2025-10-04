# Tasks Document

- [x] 1. Create ProjectStateManager class with state persistence
  - File: airflow_dags/autonomous_fixing/core/state_manager.py
  - Implement save_state(), should_reconfigure(), _get_config_hash(), _ensure_gitignore()
  - Add Markdown state file format with YAML frontmatter
  - _Leverage: pathlib patterns, hashlib for SHA256, yaml for frontmatter_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 3.5_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer specializing in state management and file I/O | Task: Create ProjectStateManager implementing project-based state storage following requirements 1.1-1.5 and 3.1-3.5, saving state to .ai-state/, computing config hashes (SHA256), ensuring gitignore, using Markdown format with metadata | Restrictions: Must use atomic file operations, handle corrupted state gracefully, ensure .ai-state/ gitignored, permissions 0644 for state files | Success: State saved to project directory, gitignore updated, Markdown format with validation markers, config hash computed correctly, >90% coverage | Instructions: First mark in-progress, implement, mark complete_

- [x] 2. Implement smart cache invalidation logic
  - File: airflow_dags/autonomous_fixing/core/state_manager.py (extend)
  - Add invalidation triggers: config modified, hash changed, files deleted, state stale (>30d)
  - Implement mtime comparison, hash comparison, file existence checks
  - _Leverage: pathlib.stat() for mtimes, existing hash computation_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Systems Engineer with expertise in cache invalidation strategies | Task: Implement smart invalidation logic following requirements 2.1-2.5, checking config file mtimes (package.json, .pre-commit-config.yaml), comparing config hashes, detecting deleted files, checking state staleness (>30 days) | Restrictions: Must handle missing files gracefully, use efficient mtime checks, validate hash before comparison, fail-safe on uncertainty | Success: Invalidation triggers work correctly, config changes detected, stale state detected, deleted files trigger re-run, >90% test coverage | Instructions: First mark in-progress, implement, mark complete_

- [x] 3. Add backward compatibility with external cache
  - File: airflow_dags/autonomous_fixing/core/state_manager.py (extend)
  - Implement fallback: check .ai-state/ first, then config/*-cache/
  - Add migration logging when using external cache
  - _Leverage: existing cache path patterns from IssueFixer_
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Migration Engineer with Python expertise | Task: Add backward compatibility with external cache following requirements 4.1-4.5, checking .ai-state/ first then config/*-cache/, using newer state if available, logging migration notices, writing only to new location | Restrictions: Must prefer new location, compare timestamps when both exist, log migration clearly, no dual-write to both locations | Success: Fallback works correctly, migration logged, newer state preferred, writes only to .ai-state/, backward compatible | Instructions: First mark in-progress, implement, mark complete_

- [x] 4. Integrate ProjectStateManager into PreflightValidator
  - File: airflow_dags/autonomous_fixing/core/validators/preflight.py (modify)
  - Replace cache validation with state_manager.should_reconfigure() calls
  - Update validation methods to use project-based state
  - _Leverage: existing PreflightValidator structure (from setup-optimization spec)_
  - _Requirements: Integration with validation layer_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Engineer | Task: Integrate ProjectStateManager into PreflightValidator, replacing external cache checks with state_manager.should_reconfigure(), delegating state validation to state manager, maintaining existing return format tuple[bool, str] | Restrictions: Must maintain PreflightValidator interface, preserve existing validation logic, no breaking changes to iteration engine integration | Success: Validator uses project state, state manager integrated seamlessly, return format unchanged, validation logic enhanced, no regressions | Instructions: First mark in-progress, implement, mark complete_

- [x] 5. Update IterationEngine to save state after successful setup
  - File: airflow_dags/autonomous_fixing/core/iteration_engine.py (modify)
  - Add state_manager.save_state() calls after successful hook config and test discovery
  - Instantiate ProjectStateManager for each project in loop
  - _Leverage: existing setup phase integration from setup-optimization spec_
  - _Requirements: State persistence after successful operations_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Workflow Integration Engineer | Task: Update IterationEngine to save project state after successful setup operations, instantiating ProjectStateManager per project, calling save_state() after hook configuration and test discovery succeed, passing operation metadata | Restrictions: Must only save on success (not on failure), instantiate manager per project, preserve existing flow, handle state save errors gracefully | Success: State saved after successful setup, project-specific state managed, errors handled, integration seamless, no flow disruption | Instructions: First mark in-progress, implement, mark complete_

- [x] 6. Add comprehensive unit tests for ProjectStateManager
  - File: tests/unit/test_project_state_manager.py
  - Test save/load, hash computation, invalidation triggers, gitignore creation
  - _Leverage: pytest tmp_path, freezegun for time mocking_
  - _Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5, 4.1-4.5_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer specializing in state management testing | Task: Create comprehensive unit tests for ProjectStateManager covering all requirements, testing state save/load cycle, config hash computation, invalidation triggers (modified files, deleted files, stale state), gitignore creation, backward compatibility | Restrictions: Use tmp_path for projects, mock time for staleness tests, test all invalidation triggers, verify atomic operations | Success: >90% coverage, all triggers tested, hash computation validated, gitignore tested, migration tested, all edge cases covered | Instructions: First mark in-progress, implement, mark complete_

- [x] 7. Add integration tests for state migration and portability
  - File: tests/integration/test_state_migration_portability.py
  - Test migration from external to project state, cross-machine consistency
  - _Leverage: tmp_path, shutil for directory copying_
  - _Requirements: All (integration validation)_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Test Engineer | Task: Create integration tests for state migration and portability, testing migration from config/*-cache/ to .ai-state/, copying project to different path and verifying state works, modifying config and verifying invalidation | Restrictions: Must test real file operations, verify migration logged, test cross-directory portability, clean up test state | Success: Migration tested end-to-end, portability validated, invalidation triggered correctly, state works across different project paths | Instructions: First mark in-progress, implement, mark complete_

- [ ] 8. Add E2E test for project-based state in autonomous fixing
  - File: tests/e2e/test_project_state_e2e.py
  - Run autonomous fixing, verify .ai-state/ created, modify config, verify re-run
  - _Leverage: autonomous_fix.sh, test projects_
  - _Requirements: All (E2E validation)_
  - _Prompt: Implement the task for spec state-management, first run spec-workflow-guide to get the workflow guide then implement the task: Role: E2E Test Engineer | Task: Create E2E test running full autonomous fixing with project state, verifying .ai-state/ directory created, state files written, gitignore updated, config modification triggers invalidation, state persists across runs | Restrictions: Must use real autonomous_fix.sh, test with real project, verify state file format, test invalidation by actually modifying config files | Success: E2E flow validated, .ai-state/ created correctly, state persists, invalidation triggers work, gitignore updated, format correct | Instructions: First mark in-progress, implement, mark complete_
