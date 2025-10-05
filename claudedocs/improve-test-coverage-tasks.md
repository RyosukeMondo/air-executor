# Test Coverage Improvement Tasks

**Goal**: Increase overall test coverage from **40%** to **>80%**

**Current Status**: 338 tests passing, 30 files need coverage improvement

**Generated**: October 5, 2025

---

## 📊 Progress Summary

- [ ] **Phase 1**: Critical Core Modules (0/12 completed) - Target: >70%
- [ ] **Phase 2**: Adapter Modules (0/13 completed) - Target: >70%
- [ ] **Phase 3**: Legacy/Deprecated Modules (0/6 completed) - Target: >50% or deprecate

**Overall Progress**: 0/31 files improved

---

## 🔴 Phase 1: Critical Core Modules (Priority: HIGH)

These are core business logic files that need immediate coverage improvement.

### 1.1 Core Orchestration & Iteration

#### [ ] `core/fixer.py` (25% → 70%)
**Current**: 146 statements, 110 missing (25% coverage)
**Priority**: 🔴 CRITICAL - Core fixing logic

**Tasks**:
- [ ] Add tests for `fix_static_issues()` method with various error types
- [ ] Test `fix_test_issues()` with different test failure scenarios
- [ ] Test `configure_precommit_hooks()` with different project structures
- [ ] Test `discover_test_config()` with Python/JavaScript projects
- [ ] Test AI client retry logic and error handling
- [ ] Test dependency injection of language adapters
- [ ] Add edge case tests for empty/null results
- [ ] Test circuit breaker behavior for repeated failures

**Files to update**: `tests/unit/test_fixer.py`, `tests/integration/test_fixer_adapter_integration.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `core/fixer.py`

---

#### [ ] `core/iteration_engine.py` (40% → 75%)
**Current**: 227 statements, 136 missing (40% coverage)
**Priority**: 🔴 CRITICAL - Main orchestration loop

**Tasks**:
- [ ] Test `run_improvement_loop()` with multiple iterations
- [ ] Test `_run_static_analysis_phase()` success and failure paths
- [ ] Test `_run_test_analysis_phase()` with different strategies
- [ ] Test `_upgrade_hooks_after_p1()` and `_upgrade_hooks_after_p2()`
- [ ] Test circuit breaker for test creation loops
- [ ] Test time gate abort conditions
- [ ] Test P1/P2 gate pass/fail scenarios
- [ ] Add integration test for full iteration cycle

**Files to update**: `tests/unit/test_iteration_engine.py`, `tests/e2e/test_full_iteration_loop.py` (expand)

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `core/iteration_engine.py`

---

#### [ ] `core/analyzer.py` (45% → 75%)
**Current**: 78 statements, 43 missing (45% coverage)
**Priority**: 🔴 CRITICAL - Analysis orchestration

**Tasks**:
- [ ] Test `analyze_static()` with multi-language projects
- [ ] Test `analyze_tests()` with different test strategies
- [ ] Test `analyze_coverage()` with various coverage tools
- [ ] Test `analyze_e2e()` for end-to-end test scenarios
- [ ] Test adapter selection logic for each language
- [ ] Test error aggregation across multiple projects
- [ ] Test parallel vs sequential analysis modes

**Files to update**: `tests/unit/test_analyzer.py`, `tests/integration/test_analyzer_multi_language.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `core/analyzer.py`

---

#### [ ] `core/scorer.py` (45% → 75%)
**Current**: 33 statements, 18 missing (45% coverage)
**Priority**: 🟡 HIGH - Health scoring logic

**Tasks**:
- [ ] Test `score_static_analysis()` with various error counts
- [ ] Test `score_tests()` with different pass/fail ratios
- [ ] Test `score_coverage()` with different coverage percentages
- [ ] Test `determine_test_strategy()` logic (SKIP/SMART/COMPREHENSIVE)
- [ ] Test edge cases (0 tests, 100% failures, empty results)
- [ ] Test threshold boundary conditions

**Files to update**: `tests/unit/test_scorer.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `core/scorer.py`

---

### 1.2 Core Supporting Components

#### [ ] `core/hook_level_manager.py` (28% → 70%)
**Current**: 208 statements, 150 missing (28% coverage)
**Priority**: 🔴 CRITICAL - Progressive hook enforcement

**Tasks**:
- [ ] Test `upgrade_after_gate_passed()` for each level (0→1→2→3)
- [ ] Test hook verification with adapter type checks
- [ ] Test hook verification with adapter builds
- [ ] Test `.pre-commit-level` file creation and updates
- [ ] Test rollback scenarios when verification fails
- [ ] Test hook config generation for each level
- [ ] Test edge cases (missing adapters, invalid levels)

**Files to update**: `tests/unit/test_hook_level_manager.py`, `tests/integration/test_progressive_hooks.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `core/hook_level_manager.py`

---

#### [ ] `core/analysis_delegate.py` (35% → 70%)
**Current**: 82 statements, 53 missing (35% coverage)
**Priority**: 🟡 HIGH - AI-powered analysis

**Tasks**:
- [ ] Test `analyze_with_ai()` with mock AI responses
- [ ] Test `parse_ai_analysis()` for various response formats
- [ ] Test error handling for AI client failures
- [ ] Test retry logic for transient failures
- [ ] Test analysis result transformation
- [ ] Add dependency injection tests for AI client

**Files to update**: `tests/unit/test_analysis_delegate.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `core/analysis_delegate.py`

---

#### [ ] `core/time_gatekeeper.py` (43% → 70%)
**Current**: 61 statements, 35 missing (43% coverage)
**Priority**: 🟡 HIGH - Time budget enforcement

**Tasks**:
- [ ] Test `start_iteration()` and `end_iteration()` tracking
- [ ] Test `should_abort()` rapid iteration detection
- [ ] Test `wait_if_needed()` throttling logic
- [ ] Test `get_timing_summary()` report generation
- [ ] Test boundary conditions (max time, max iterations)
- [ ] Test timing metrics accuracy

**Files to update**: `tests/unit/test_time_gatekeeper.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `core/time_gatekeeper.py`

---

#### [ ] `core/analysis_verifier.py` (58% → 75%)
**Current**: 113 statements, 48 missing (58% coverage)
**Priority**: 🟡 HIGH - Result validation

**Tasks**:
- [ ] Test `verify_batch_results()` with valid/invalid results
- [ ] Test `verify_analysis_result()` schema validation
- [ ] Test `print_verification_report()` output formatting
- [ ] Test error detection for malformed results
- [ ] Test verification with missing required fields
- [ ] Test verification across multiple languages

**Files to update**: `tests/unit/test_analysis_verifier.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `core/analysis_verifier.py`

---

#### [ ] `core/validators/preflight.py` (62% → 75%)
**Current**: 141 statements, 54 missing (62% coverage)
**Priority**: 🟡 HIGH - Setup validation

**Tasks**:
- [ ] Test `can_skip_hook_config()` with various cache states
- [ ] Test `can_skip_test_discovery()` with different scenarios
- [ ] Test cache invalidation triggers (config changes, staleness)
- [ ] Test state file validation
- [ ] Test integration with SetupTracker
- [ ] Test time-based staleness detection (>7 days)

**Files to update**: `tests/unit/test_preflight_validator.py`, `tests/integration/test_preflight_integration.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `core/validators/preflight.py`

---

#### [ ] `core/debug_logger.py` (55% → 75%)
**Current**: 98 statements, 44 missing (55% coverage)
**Priority**: 🟢 MEDIUM - Logging utility

**Tasks**:
- [ ] Test `log_iteration_start()` and `log_iteration_end()`
- [ ] Test `log_fix_result()` with success/failure
- [ ] Test `log_session_start()` and `log_session_end()`
- [ ] Test JSON formatting correctness
- [ ] Test file output when enabled
- [ ] Test console output formatting

**Files to update**: `tests/unit/test_debug_logger.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `core/debug_logger.py`

---

#### [ ] `core/prompt_manager.py` (49% → 70%)
**Current**: 47 statements, 24 missing (49% coverage)
**Priority**: 🟢 MEDIUM - Prompt generation

**Tasks**:
- [ ] Test `get_fix_prompt()` for different issue types
- [ ] Test `get_analysis_prompt()` for various contexts
- [ ] Test template loading and variable substitution
- [ ] Test prompt customization options
- [ ] Test prompt validation

**Files to update**: `tests/unit/test_prompt_manager.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `core/prompt_manager.py`

---

#### [ ] `core/commit_verifier.py` (44% → 70%)
**Current**: 16 statements, 9 missing (44% coverage)
**Priority**: 🟢 MEDIUM - Git commit validation

**Tasks**:
- [ ] Test `has_new_commits()` with various git states
- [ ] Test `get_recent_commits()` output parsing
- [ ] Test error handling for non-git directories
- [ ] Test commit detection after fixes

**Files to update**: `tests/unit/test_commit_verifier.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `core/commit_verifier.py`

---

## 🟡 Phase 2: Adapter Modules (Priority: MEDIUM)

### 2.1 Language Adapters

#### [ ] `adapters/languages/python_adapter.py` (48% → 75%)
**Current**: 274 statements, 142 missing (48% coverage)
**Priority**: 🔴 CRITICAL - Python language support

**Tasks**:
- [ ] Test `static_analysis()` with flake8/pylint/ruff
- [ ] Test `run_tests()` with pytest
- [ ] Test `analyze_coverage()` with coverage.py
- [ ] Test `run_type_check()` with mypy
- [ ] Test `run_build()` for Python projects
- [ ] Test `parse_errors()` for different linter formats
- [ ] Test `calculate_complexity()` with radon
- [ ] Test error handling for missing tools

**Files to update**: `tests/unit/test_python_adapter.py`, `tests/integration/test_python_adapter_integration.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `adapters/languages/python_adapter.py`

---

#### [ ] `adapters/languages/javascript_adapter.py` (30% → 75%)
**Current**: 311 statements, 218 missing (30% coverage)
**Priority**: 🔴 CRITICAL - JavaScript language support

**Tasks**:
- [ ] Test `static_analysis()` with eslint
- [ ] Test `run_tests()` with jest/mocha
- [ ] Test `analyze_coverage()` with nyc/jest
- [ ] Test `run_type_check()` with typescript
- [ ] Test `run_build()` with webpack/vite
- [ ] Test `parse_errors()` for eslint format
- [ ] Test package.json detection and parsing
- [ ] Test node_modules handling

**Files to update**: `tests/unit/test_javascript_adapter.py`, `tests/integration/test_javascript_adapter_integration.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `adapters/languages/javascript_adapter.py`

---

#### [ ] `adapters/languages/base.py` (50% → 75%)
**Current**: 137 statements, 68 missing (50% coverage)
**Priority**: 🟡 HIGH - Base adapter interface

**Tasks**:
- [ ] Test abstract method enforcement
- [ ] Test common utility methods
- [ ] Test default implementations
- [ ] Test adapter initialization
- [ ] Test config handling
- [ ] Test error message formatting

**Files to update**: `tests/unit/test_base_adapter.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `adapters/languages/base.py`

---

#### [ ] `adapters/languages/python_linters.py` (64% → 75%)
**Current**: 47 statements, 17 missing (64% coverage)
**Priority**: 🟢 MEDIUM - Python linter wrappers

**Tasks**:
- [ ] Test flake8 wrapper with various outputs
- [ ] Test pylint wrapper with different error formats
- [ ] Test ruff wrapper output parsing
- [ ] Test error count aggregation
- [ ] Test missing linter handling

**Files to update**: `tests/unit/test_python_linters.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `adapters/languages/python_linters.py`

---

#### [ ] `adapters/languages/javascript_linters.py` (52% → 75%)
**Current**: 23 statements, 11 missing (52% coverage)
**Priority**: 🟢 MEDIUM - JavaScript linter wrappers

**Tasks**:
- [ ] Test eslint wrapper with various configs
- [ ] Test error parsing for different formats
- [ ] Test warning vs error categorization
- [ ] Test missing eslint handling

**Files to update**: `tests/unit/test_javascript_linters.py`

**Completion marker**: <!-- Coverage: 75% ✅ --> at bottom of `adapters/languages/javascript_linters.py`

---

#### [ ] `adapters/languages/go_adapter.py` (15% → 50%)
**Current**: 274 statements, 234 missing (15% coverage)
**Priority**: 🟢 LOW - Go language support (if used)

**Tasks**:
- [ ] Test basic static analysis with go fmt/vet
- [ ] Test `run_tests()` with go test
- [ ] Test `run_build()` with go build
- [ ] Test error parsing for go toolchain
- [ ] **OR** Mark as deprecated if not actively used

**Files to update**: `tests/unit/test_go_adapter.py` OR add deprecation notice

**Completion marker**: <!-- Coverage: 50% ✅ --> or <!-- DEPRECATED --> at bottom of `adapters/languages/go_adapter.py`

---

#### [ ] `adapters/languages/flutter_adapter.py` (15% → 50%)
**Current**: 245 statements, 209 missing (15% coverage)
**Priority**: 🟢 LOW - Flutter language support (if used)

**Tasks**:
- [ ] Test basic static analysis with flutter analyze
- [ ] Test `run_tests()` with flutter test
- [ ] Test `run_build()` with flutter build
- [ ] Test error parsing for flutter toolchain
- [ ] **OR** Mark as deprecated if not actively used

**Files to update**: `tests/unit/test_flutter_adapter.py` OR add deprecation notice

**Completion marker**: <!-- Coverage: 50% ✅ --> or <!-- DEPRECATED --> at bottom of `adapters/languages/flutter_adapter.py`

---

#### [ ] `adapters/languages/flutter_test_utils.py` (30% → 50%)
**Current**: 33 statements, 23 missing (30% coverage)
**Priority**: 🟢 LOW - Flutter utilities

**Tasks**:
- [ ] Test utility functions if Flutter is used
- [ ] **OR** Mark as deprecated

**Files to update**: `tests/unit/test_flutter_test_utils.py` OR deprecate

**Completion marker**: <!-- Coverage: 50% ✅ --> or <!-- DEPRECATED -->

---

### 2.2 AI & External Service Adapters

#### [ ] `adapters/ai/claude_client.py` (67% → 80%)
**Current**: 163 statements, 54 missing (67% coverage)
**Priority**: 🟡 HIGH - AI client integration

**Tasks**:
- [ ] Test `query()` method with various prompts
- [ ] Test error handling for API failures
- [ ] Test retry logic for transient errors
- [ ] Test rate limiting handling
- [ ] Test response parsing and validation
- [ ] Test timeout handling
- [ ] Test streaming vs non-streaming responses

**Files to update**: `tests/unit/test_claude_client.py`, `tests/integration/test_claude_client_integration.py`

**Completion marker**: <!-- Coverage: 80% ✅ --> at bottom of `adapters/ai/claude_client.py`

---

#### [ ] `adapters/ai/wrapper_history.py` (48% → 70%)
**Current**: 194 statements, 101 missing (48% coverage)
**Priority**: 🟢 MEDIUM - AI call history tracking

**Tasks**:
- [ ] Test `record_call()` for different call types
- [ ] Test `get_history()` retrieval and filtering
- [ ] Test `clear_history()` cleanup
- [ ] Test persistence to file/storage
- [ ] Test history size limits
- [ ] Test concurrent access handling

**Files to update**: `tests/unit/test_wrapper_history.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `adapters/ai/wrapper_history.py`

---

### 2.3 Parsing & Validation Adapters

#### [ ] `adapters/error_parser.py` (43% → 70%)
**Current**: 159 statements, 90 missing (43% coverage)
**Priority**: 🟡 HIGH - Error parsing logic

**Tasks**:
- [ ] Test parsing of different error formats (Python, JS, Go)
- [ ] Test error extraction from stdout/stderr
- [ ] Test warning vs error categorization
- [ ] Test line number extraction
- [ ] Test file path extraction
- [ ] Test edge cases (malformed errors, unicode)

**Files to update**: `tests/unit/test_error_parser.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `adapters/error_parser.py`

---

#### [ ] `adapters/test_result_parser.py` (24% → 70%)
**Current**: 169 statements, 128 missing (24% coverage)
**Priority**: 🟡 HIGH - Test result parsing

**Tasks**:
- [ ] Test parsing pytest output (verbose/summary)
- [ ] Test parsing jest output
- [ ] Test parsing go test output
- [ ] Test pass/fail/skip counting
- [ ] Test error extraction from test failures
- [ ] Test edge cases (0 tests, all pass, all fail)

**Files to update**: `tests/unit/test_test_result_parser.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `adapters/test_result_parser.py`

---

#### [ ] `adapters/git/git_verifier.py` (36% → 70%)
**Current**: 25 statements, 16 missing (36% coverage)
**Priority**: 🟢 MEDIUM - Git operations

**Tasks**:
- [ ] Test `has_uncommitted_changes()` detection
- [ ] Test `get_current_branch()` output
- [ ] Test `is_clean_working_tree()` validation
- [ ] Test error handling for non-git directories

**Files to update**: `tests/unit/test_git_verifier.py`

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom of `adapters/git/git_verifier.py`

---

### 2.4 State Management Adapters

#### [ ] `adapters/state/state_manager.py` (14% → 50%)
**Current**: 146 statements, 125 missing (14% coverage)
**Priority**: 🟢 MEDIUM - State persistence

**Tasks**:
- [ ] Test state save/load operations
- [ ] Test state file format (JSON/YAML)
- [ ] Test state directory creation
- [ ] Test state corruption handling
- [ ] Test concurrent access scenarios
- [ ] **OR** Check if this duplicates `core/state_manager.py` and consolidate

**Files to update**: `tests/unit/test_state_manager_adapter.py`

**Completion marker**: <!-- Coverage: 50% ✅ --> or <!-- DEPRECATED --> at bottom

---

## 🟢 Phase 3: Legacy/Utility Modules (Priority: LOW)

### 3.1 Deprecated or Low-Priority Modules

#### [ ] `core/tool_validator.py` (14% → 50% or DEPRECATE)
**Current**: 177 statements, 153 missing (14% coverage)
**Priority**: 🟢 LOW - Tool validation

**Decision Required**:
- [ ] If actively used: Write tests to reach 50%
- [ ] If deprecated: Mark as deprecated and remove from coverage targets

**Tasks (if keeping)**:
- [ ] Test `validate_tool()` for each language toolchain
- [ ] Test missing tool detection
- [ ] Test version checking logic
- [ ] Test tool path resolution

**Files to update**: `tests/unit/test_tool_validator.py` OR add deprecation

**Completion marker**: <!-- Coverage: 50% ✅ --> or <!-- DEPRECATED -->

---

#### [ ] `core/issue_extractor.py` (19% → 50% or DEPRECATE)
**Current**: 37 statements, 30 missing (19% coverage)
**Priority**: 🟢 LOW - Issue extraction

**Decision Required**:
- [ ] Check if this duplicates functionality in error_parser.py
- [ ] If redundant: Deprecate and migrate functionality
- [ ] If unique: Write tests to reach 50%

**Completion marker**: <!-- Coverage: 50% ✅ --> or <!-- DEPRECATED -->

---

#### [ ] `domain/exceptions.py` (58% → 70%)
**Current**: 36 statements, 15 missing (58% coverage)
**Priority**: 🟢 MEDIUM - Custom exceptions

**Tasks**:
- [ ] Test each custom exception class
- [ ] Test exception message formatting
- [ ] Test exception inheritance chain
- [ ] Test exception context data

**Files to update**: `tests/unit/test_exceptions.py`

**Completion marker**: <!-- Coverage: 70% ✅ -->

---

### 3.2 Legacy Orchestrator Files (0% coverage - DEPRECATE)

#### [ ] `executor_prompts.py` (0% → DEPRECATE)
**Current**: 115 statements, 115 missing (0% coverage)
**Status**: Legacy file, check if still used

**Decision**:
- [ ] Verify if used in current codebase
- [ ] If unused: Mark as deprecated and exclude from coverage
- [ ] If used: Migrate to `core/prompt_manager.py`

**Completion marker**: <!-- DEPRECATED --> or migrate

---

#### [ ] `executor_runner.py` (0% → DEPRECATE)
**Current**: 128 statements, 128 missing (0% coverage)
**Status**: Legacy file

**Decision**:
- [ ] Verify if used in current codebase
- [ ] If unused: Mark as deprecated
- [ ] If used: Write tests or migrate functionality

**Completion marker**: <!-- DEPRECATED --> or migrate

---

#### [ ] `executor_utils.py` (0% → DEPRECATE)
**Current**: 25 statements, 25 missing (0% coverage)
**Status**: Utility file with 0% coverage

**Decision**:
- [ ] Check if utilities are used elsewhere
- [ ] Migrate useful functions to appropriate modules
- [ ] Deprecate this file

**Completion marker**: <!-- DEPRECATED -->

---

#### [ ] `fix_orchestrator.py` (0% → DEPRECATE)
**Current**: 203 statements, 203 missing (0% coverage)
**Status**: Old orchestrator, replaced by `multi_language_orchestrator.py`

**Decision**:
- [ ] Confirm replacement by new orchestrator
- [ ] Mark as deprecated
- [ ] Plan removal in future version

**Completion marker**: <!-- DEPRECATED - See multi_language_orchestrator.py -->

---

#### [ ] `issue_discovery.py` (0% → DEPRECATE)
**Current**: 138 statements, 138 missing (0% coverage)

**Completion marker**: <!-- DEPRECATED -->

---

#### [ ] `issue_grouping.py` (0% → DEPRECATE)
**Current**: 156 statements, 156 missing (0% coverage)

**Completion marker**: <!-- DEPRECATED -->

---

#### [ ] `smart_health_monitor.py` (0% → DEPRECATE)
**Current**: 187 statements, 187 missing (0% coverage)

**Completion marker**: <!-- DEPRECATED --> or implement if needed

---

#### [ ] `multi_language_orchestrator.py` (36% → 70%)
**Current**: 104 statements, 67 missing (36% coverage)
**Priority**: 🔴 CRITICAL - Main entry point

**Tasks**:
- [ ] Test `run()` method end-to-end
- [ ] Test language detection logic
- [ ] Test project grouping by language
- [ ] Test orchestrator configuration
- [ ] Test error handling and reporting
- [ ] Add integration tests with real projects

**Files to update**: `tests/unit/test_multi_language_orchestrator.py`, `tests/e2e/test_multi_language_orchestration.py` (expand)

**Completion marker**: <!-- Coverage: 70% ✅ --> at bottom

---

## 📋 Completion Checklist Format

Add this marker at the **bottom of each source file** after improving coverage:

```python
# =============================================================================
# TEST COVERAGE STATUS
# =============================================================================
# Coverage: 75% ✅ (Target: 70%)
# Last Updated: 2025-10-05
# Tests: tests/unit/test_<module>.py, tests/integration/test_<module>_integration.py
# =============================================================================
```

---

## 🎯 Success Metrics

### Phase 1 Success (Critical Core)
- [ ] All 12 core modules ≥ 70% coverage
- [ ] Overall core/ directory coverage ≥ 75%
- [ ] All critical business logic paths tested

### Phase 2 Success (Adapters)
- [ ] Python & JavaScript adapters ≥ 75% coverage
- [ ] AI client adapter ≥ 80% coverage
- [ ] Parser adapters ≥ 70% coverage
- [ ] Overall adapters/ directory coverage ≥ 70%

### Phase 3 Success (Cleanup)
- [ ] All legacy files deprecated or tested
- [ ] 0% coverage files marked as deprecated
- [ ] Migration plan for deprecated functionality

### Overall Success
- [ ] **Overall project coverage: >80%** (from current 40%)
- [ ] All critical paths have tests
- [ ] No core business logic files < 60% coverage
- [ ] Clear coverage improvement documentation

---

## 📊 Progress Tracking

Use this command to check progress:

```bash
# Generate coverage report
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=term-missing \
  --cov-report=html

# Check specific file coverage
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing/core/fixer.py \
  --cov-report=term-missing
```

**Update this file** after completing each task by checking the box: `- [x]`

---

## 🚀 Quick Start Workflow

1. **Choose a file** from Phase 1 (highest priority)
2. **Check current tests**: `tests/unit/test_<module>.py`
3. **Run coverage**: `.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing/<path> --cov-report=term-missing`
4. **Write tests** for red (uncovered) lines
5. **Re-run coverage** to verify improvement
6. **Check box** in this file when target reached
7. **Add completion marker** at bottom of source file
8. **Move to next file**

---

**Generated by**: Claude Code
**Date**: October 5, 2025
**Total Tasks**: 31 files to improve or deprecate
**Estimated Effort**: 40-60 hours for complete coverage improvement
