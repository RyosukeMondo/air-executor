# Tasks Document

- [x] 1. Create SetupTracker core module
  - File: airflow_dags/autonomous_fixing/core/setup_tracker.py
  - Implement state tracking with Redis primary, filesystem fallback
  - Add methods: `mark_setup_complete()`, `is_setup_complete()`, `_redis_store()`, `_filesystem_store()`
  - Purpose: Provide persistent state tracking across autonomous fixing sessions
  - _Leverage: config/projects/warps.yaml state_manager configuration (lines 41-44), pathlib patterns from existing core modules_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer specializing in state management and distributed systems | Task: Create SetupTracker class implementing persistent setup phase tracking following requirements 2.1-2.6, with Redis as primary storage (TTL 30 days) and filesystem markers as fallback, leveraging existing state_manager configuration from config/projects/warps.yaml | Restrictions: Must work with or without Redis (graceful degradation), do not create circular dependencies with iteration_engine, use pathlib for all file operations, follow structlog logging patterns | _Leverage: existing Redis configuration in config/projects/warps.yaml lines 41-44, pathlib patterns from airflow_dags/autonomous_fixing/core/*.py modules | Success: Class implements both Redis and filesystem storage, state persists across sessions, TTL logic works correctly, graceful Redis fallback, >90% test coverage | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 2. Create PreflightValidator validation module
  - File: airflow_dags/autonomous_fixing/core/validators/preflight.py
  - Implement cache validation methods: `can_skip_hook_config()`, `can_skip_test_discovery()`
  - Add cache integrity validation: `_validate_hook_cache()`, `_validate_test_cache()`
  - Purpose: Provide fast computational checks before AI invocation
  - _Leverage: airflow_dags/autonomous_fixing/core/fixer.py cache path patterns (lines 346, 403), yaml parsing from existing codebase_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 3.5_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer with expertise in validation logic and caching strategies | Task: Create PreflightValidator class implementing pre-flight validation checks following requirements 1.1-1.5 and 3.1-3.5, checking cache file existence, validity (<7 days), and integrity (required YAML fields), returning tuple[bool, str] for skip decisions | Restrictions: Must complete all checks in <200ms total, fail-safe (if uncertain, don't skip), no AI/wrapper dependencies, use SetupTracker for state queries | _Leverage: cache path construction from airflow_dags/autonomous_fixing/core/fixer.py lines 346 and 403, yaml.safe_load patterns from existing modules | Success: Validation completes <100ms per project, all error conditions handled gracefully, cache corruption detected and logged, returns actionable skip reasons, >90% test coverage | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 3. Integrate validation into IterationEngine setup loops
  - File: airflow_dags/autonomous_fixing/core/iteration_engine.py (modify existing)
  - Add validator instantiation after line 50 (after hook_manager initialization)
  - Modify setup phase 0 loop (lines 80-83) to call `validator.can_skip_hook_config()`
  - Modify setup phase 1 loop (lines 89-92) to call `validator.can_skip_test_discovery()`
  - Add setup tracker calls after successful AI invocations
  - Purpose: Enable setup skipping in production autonomous fixing workflow
  - _Leverage: existing IterationEngine loop structure (lines 74-92), IssueFixer methods (configure_precommit_hooks, discover_test_config)_
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Engineer with expertise in Python workflow orchestration | Task: Integrate PreflightValidator and SetupTracker into IterationEngine.run_improvement_loop() following requirements 4.1-4.5, adding validation checks before AI calls in setup phases 0 and 1, logging skip decisions with savings estimates, marking successful completions | Restrictions: Must not change existing IssueFixer method signatures, maintain backward compatibility, preserve all existing logging, handle validation failures gracefully | _Leverage: existing loop structure from airflow_dags/autonomous_fixing/core/iteration_engine.py lines 74-92, IssueFixer.configure_precommit_hooks and IssueFixer.discover_test_config methods (no modifications to fixer needed) | Success: Setup phases skip correctly when cache valid, AI calls proceed when cache invalid/missing, skip decisions logged with format "⏭️ {project}: {reason}", state marked on successful AI completion, no regressions in existing flow | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 4. Add comprehensive unit tests for SetupTracker
  - File: tests/unit/test_setup_tracker.py
  - Test Redis operations: store state, query state, TTL expiration
  - Test filesystem fallback: marker creation, timestamp validation, stale detection
  - Test graceful degradation: Redis unavailable scenarios
  - Purpose: Ensure state tracking reliability across all storage backends
  - _Leverage: pytest fixtures, fakeredis for mocking, tmp_path fixture for filesystem tests_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in Python unit testing and pytest | Task: Create comprehensive unit tests for SetupTracker covering requirements 2.1-2.6, testing Redis operations (store, query, TTL), filesystem fallback (markers, timestamps, staleness), and graceful degradation (Redis unavailable) | Restrictions: Must mock Redis client (use fakeredis), use tmp_path for filesystem tests, test both success and failure paths, maintain test isolation (no shared state) | _Leverage: pytest tmp_path fixture for temporary filesystem testing, fakeredis library for Redis mocking, existing test patterns from tests/unit/*.py | Success: >90% code coverage for SetupTracker, all storage backends tested, TTL logic validated, Redis fallback tested, concurrent access safe, all tests pass independently | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 5. Add comprehensive unit tests for PreflightValidator
  - File: tests/unit/test_preflight_validator.py
  - Test cache validation: valid cache, corrupted YAML, missing fields, stale cache
  - Test skip decisions: hook config validation, test discovery validation
  - Test performance: verify <200ms validation time
  - Purpose: Ensure validation logic correctness and performance
  - _Leverage: pytest fixtures, tmp_path for cache files, freezegun for timestamp mocking_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 3.5_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer specializing in validation testing and performance verification | Task: Create comprehensive unit tests for PreflightValidator covering requirements 1.1-1.5 and 3.1-3.5, testing cache validation (valid/corrupted/incomplete), skip decision logic, and performance (<200ms), using tmp_path for cache files and freezegun for timestamp control | Restrictions: Must test all error conditions (YAML errors, missing files, permission errors), verify fail-safe behavior (uncertain → don't skip), ensure deterministic tests (mock time.time()), no actual AI calls | _Leverage: pytest tmp_path for temporary cache files, freezegun for time mocking, pyyaml for cache generation in tests | Success: >90% code coverage, all validation paths tested, performance verified (<200ms), error handling validated, fail-safe behavior confirmed, all cache corruption scenarios covered | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 6. Add integration tests for full setup optimization flow
  - File: tests/integration/test_setup_optimization_flow.py
  - Test complete flow: clean project → cache miss → AI invocation → cache creation → cache hit → skip
  - Test Redis integration with real Redis container
  - Test filesystem fallback scenario
  - Purpose: Verify end-to-end setup optimization in realistic scenarios
  - _Leverage: docker-compose for Redis container, existing integration test patterns, test fixtures for project setup_
  - _Requirements: All (integration testing requirement)_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Test Engineer with expertise in Python integration testing and Docker | Task: Create integration tests covering full setup optimization flow for all requirements, testing clean project → cache miss → AI call → cache creation → cache hit → skip cycle, using real Redis (docker-compose) and filesystem fallback scenarios | Restrictions: Must use real Redis container (not mocked), clean up test state between runs, verify skip decisions logged correctly, measure actual time savings | _Leverage: docker-compose for test Redis, existing integration test patterns from tests/integration/*.py, test fixtures for project setup | Success: Full flow validated from cache miss to cache hit, Redis integration tested with real container, filesystem fallback tested, time savings verified (>100s on second run), skip logging verified, concurrent access tested | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 7. Add end-to-end test with real autonomous fixing run
  - File: tests/e2e/test_autonomous_fixing_cache.py
  - Test full autonomous_fix.sh execution twice on same project
  - Verify first run executes setup phases, second run skips them
  - Measure and verify time savings (>100s faster on second run)
  - Purpose: Validate setup optimization in production-like scenario
  - _Leverage: scripts/autonomous_fix.sh, config/projects/warps.yaml, pytest subprocess integration_
  - _Requirements: All (E2E validation)_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: E2E Test Automation Engineer with expertise in system testing and performance validation | Task: Create end-to-end test running full autonomous_fix.sh twice covering all requirements, verifying first run executes setup (hooks + tests), second run skips setup (cache hit), and measuring time savings (target >100s faster), using real project from config/projects/warps.yaml | Restrictions: Must use actual autonomous_fix.sh script (no mocking), clean cache between test suite runs, verify final results identical (quality not affected), measure wall-clock time accurately | _Leverage: scripts/autonomous_fix.sh for execution, config/projects/warps.yaml for test project, pytest subprocess.run for script invocation, time.time() for duration measurement | Success: E2E test passes with real autonomous fixing script, first run completes setup phases (logged), second run skips setup (logged with savings), time savings measured and verified (>100s), final fix results consistent across runs, no quality regression from caching | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 8. Add skip statistics logging and reporting
  - File: airflow_dags/autonomous_fixing/core/iteration_engine.py (modify existing)
  - Track skip statistics during setup phases (count, time saved, cost saved)
  - Log summary after setup phases: "⏭️ Skipped setup for N/M projects (saved: {time}s + ${cost})"
  - Add metrics to debug logger for observability
  - Purpose: Provide visibility into setup optimization effectiveness
  - _Leverage: existing DebugLogger from iteration_engine, existing skip decision logging_
  - _Requirements: 4.4 (skip statistics requirement)_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Observability Engineer with expertise in metrics collection and structured logging | Task: Add skip statistics tracking to IterationEngine setup phases following requirement 4.4, counting skipped projects, calculating time/cost savings (60s + $0.50 per hook skip, 90s + $0.60 per test skip), logging summary after setup phases, integrating with existing DebugLogger | Restrictions: Must not change existing log format for individual skips, calculate savings based on average AI call time (hooks: 60s, tests: 90s) and API cost ($0.02/1K tokens, estimate 25K tokens per setup call), use existing DebugLogger instance | _Leverage: existing DebugLogger instance from airflow_dags/autonomous_fixing/core/iteration_engine.py, existing skip decision logging (task 3) | Success: Statistics tracked accurately (skip count, saved time, saved cost), summary logged after setup phases with clear format, metrics available in debug logs for analysis, savings calculation accurate (+/- 10%), no performance impact from metric collection | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_

- [x] 9. Update documentation and configuration examples
  - Files: docs/setup-optimization.md (new), config/projects/warps.yaml (example comments)
  - Document pre-flight validation behavior and configuration options
  - Add Redis configuration examples and fallback behavior
  - Document cache invalidation triggers and manual cache clearing
  - Purpose: Enable users to understand and configure setup optimization
  - _Leverage: existing docs/architecture/*.md patterns, config examples from warps.yaml_
  - _Requirements: Usability requirements (clear skip logging, actionable errors)_
  - _Prompt: Implement the task for spec setup-optimization, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical Writer with expertise in developer documentation and system architecture | Task: Create comprehensive documentation for setup optimization covering usability requirements, including pre-flight validation behavior, Redis configuration (optional vs required), filesystem fallback, cache invalidation triggers, manual cache clearing, and troubleshooting common issues | Restrictions: Must follow existing documentation patterns from docs/architecture/*.md, provide concrete configuration examples, explain Redis optional nature clearly, include troubleshooting section | _Leverage: existing architecture docs from docs/architecture/*.md for formatting, config/projects/warps.yaml for configuration examples | Success: Documentation is clear and comprehensive, Redis configuration explained with examples, cache invalidation triggers documented, manual cache clearing procedure provided, troubleshooting section includes common issues and solutions, examples use real project paths | Instructions: First mark task as in-progress in tasks.md, implement the code, then mark as complete when done_
