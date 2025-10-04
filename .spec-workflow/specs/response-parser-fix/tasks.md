# Tasks Document

- [x] 1. Create ResponseParser class with noise filtering
  - File: airflow_dags/autonomous_fixing/adapters/ai/response_parser.py
  - Implement parse(), _extract_real_errors(), _is_noise() methods
  - Add default NOISE_PATTERNS and ERROR_INDICATORS constants
  - _Leverage: yaml parsing patterns from existing codebase_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - _Prompt: Implement the task for spec response-parser-fix, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer specializing in parsing and pattern matching | Task: Create ResponseParser class implementing intelligent error detection following requirements 1.1-1.5, filtering noise patterns (punycode, ExperimentalWarning) from stderr, detecting real errors (Error:, Traceback), returning dict with success/errors/error_message | Restrictions: Must complete parsing in <10ms, use substring matching (not regex) for common patterns, fail-safe (uncertain → failure), handle unicode correctly | Success: Parser distinguishes warnings from errors, returns consistent dict format, performance <10ms, >90% test coverage | Instructions: First mark task as in-progress, implement code, mark complete when done_

- [x] 2. Add configurable pattern loading from YAML
  - File: airflow_dags/autonomous_fixing/adapters/ai/response_parser.py (extend)
  - Implement __init__() config loading, validate patterns, handle missing config
  - Create config file: config/error_patterns.yaml with examples
  - _Leverage: yaml.safe_load patterns, pydantic for validation_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - _Prompt: Implement the task for spec response-parser-fix, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Configuration Management Engineer with Python expertise | Task: Add configurable pattern loading to ResponseParser following requirements 2.1-2.5, loading from config/error_patterns.yaml, validating patterns (prevent ReDoS), falling back to defaults if missing/invalid | Restrictions: Must not crash on invalid config, validate regex complexity, cache config (load once), support both substring and regex patterns | Success: Config loads correctly, invalid config handled gracefully, examples in YAML, pattern updates applied on restart | Instructions: First mark in-progress, implement, mark complete_

- [x] 3. Integrate ResponseParser into ClaudeClient
  - File: airflow_dags/autonomous_fixing/adapters/ai/claude_client.py (modify)
  - Instantiate ResponseParser in __init__(), use in query() method
  - Replace simple returncode check with parser.parse() call
  - _Leverage: existing ClaudeClient query() structure_
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3_
  - _Prompt: Implement the task for spec response-parser-fix, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Engineer with Python and API design expertise | Task: Integrate ResponseParser into ClaudeClient.query() following requirements 3.1-3.5 and 4.1-4.3, replacing simple success check with intelligent parsing, maintaining backward compatibility, including operation type in error context | Restrictions: Must maintain existing method signature, preserve DebugLogger integration, ensure backward compatibility with old response format | Success: Parser integrated seamlessly, errors include operation context, backward compatible, no regression in existing flows | Instructions: First mark in-progress, implement, mark complete_

- [x] 4. Add unit tests for ResponseParser
  - File: tests/unit/test_response_parser.py
  - Test noise filtering, error detection, config loading, edge cases
  - _Leverage: pytest fixtures, tmp_path for config files_
  - _Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5_
  - _Prompt: Implement the task for spec response-parser-fix, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer specializing in parser testing | Task: Create comprehensive tests for ResponseParser covering all requirements, testing noise filtering (warnings→success), error detection (errors→failure), config loading, unicode handling, edge cases (empty stderr, huge output) | Restrictions: Must use tmp_path for config files, test performance (<10ms), cover all error indicators and noise patterns | Success: >90% coverage, all patterns tested, performance validated, unicode handled, config scenarios covered | Instructions: First mark in-progress, implement, mark complete_

- [x] 5. Add integration tests for ClaudeClient with parser
  - File: tests/integration/test_claude_client_parser.py
  - Test real wrapper responses, backward compatibility
  - _Leverage: mock wrapper responses, existing test patterns_
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - _Prompt: Implement the task for spec response-parser-fix, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Test Engineer | Task: Create integration tests for ClaudeClient with ResponseParser following requirements 4.1-4.5, testing real wrapper responses (success with warnings, failures with errors), backward compatibility with old format | Restrictions: Must test both old and new response formats, use real-world stderr samples, verify operation type logging | Success: Integration validated, backward compatibility confirmed, real wrapper responses handled correctly | Instructions: First mark in-progress, implement, mark complete_

- [x] 6. Add E2E test validating false negative fix
  - File: tests/e2e/test_false_negatives_fixed.py
  - Run autonomous fixing on project with deprecation warnings
  - Verify no false failures, successful operations marked correctly
  - _Leverage: test project with known warnings, autonomous_fix.sh_
  - _Requirements: All (E2E validation)_
  - _Prompt: Implement the task for spec response-parser-fix, first run spec-workflow-guide to get the workflow guide then implement the task: Role: E2E Test Engineer | Task: Create E2E test running autonomous fixing on project with deprecation warnings, verifying false negatives eliminated, successful operations correctly marked as success, no regression in error detection | Restrictions: Must use real project with known warnings (Node.js with punycode), verify logs show success (not failure), ensure real errors still detected | Success: False negatives eliminated, warnings filtered correctly, real errors still caught, logs accurate | Instructions: First mark in-progress, implement, mark complete_
