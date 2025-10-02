# Config Refinement Phase - Self-Correcting Setup

## Core Principle

**Never provide config until it's validated to work.**

```
Generate → Test → ❌ Failed? → Analyze → Fix → Test → ✅ Success
```

## The Problem We're Solving

### Current Flow (Fragile)
```python
# Step 1: Claude generates script
claude_wrapper("Generate test runner script")

# Step 2: We try to use it
result = run_script("run-tests.sh")  # ❌ FAILS

# Problem:
# - Wrong package manager (yarn vs npm)
# - Missing dependency
# - Wrong test directory
# - Syntax error in script

# Result: Stuck, manual intervention needed
```

### Self-Correcting Flow (Robust)
```python
# Step 1: Claude generates AND validates
claude_wrapper("Generate test runner, validate it works")

# Internal loop (Claude does this):
iteration = 1
while iteration <= 5:
    # Generate script
    create_script()

    # Test it (lightweight dry-run)
    result = test_script()

    if result.success:
        save_config()
        break
    else:
        # Analyze failure
        error = analyze(result.error)

        # Fix and retry
        fix_script(error)
        iteration += 1

# Step 2: We use validated config
result = run_script("run-tests.sh")  # ✅ GUARANTEED TO WORK
```

## Architecture

### Phase Flow

```
┌─────────────────────────────────────────────────────────┐
│  SETUP PHASE (claude_wrapper with validation)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Generate Config/Script                             │
│     └─ Create initial implementation                   │
│                                                         │
│  2. Validate (Lightweight Test)                        │
│     ├─ Run with --dry-run                              │
│     ├─ Check script syntax                             │
│     ├─ Verify dependencies exist                       │
│     └─ Test with minimal input                         │
│                                                         │
│  3. Evaluate Result                                    │
│     ├─ ✅ Success? → Save config, done                 │
│     └─ ❌ Failed? → Continue to refinement             │
│                                                         │
│  4. Refinement Loop (max 5 iterations)                 │
│     ├─ Analyze error message                           │
│     ├─ Identify root cause                             │
│     ├─ Fix the issue                                   │
│     └─ Goto step 2                                     │
│                                                         │
│  5. Result                                             │
│     ├─ Config validated and saved                      │
│     └─ Guaranteed to work in execution                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Example: Test Runner Setup

### Prompt with Validation Contract

```yaml
# config/prompts.yaml
setup:
  test_runner_with_validation:
    template: |
      Generate and validate a test runner script for {language} project.

      **Your task: Generate script AND ensure it works before completing.**

      CONTRACT:
      - Script: {project}/.air-executor/run-tests.sh
      - Args: $1=strategy (minimal|selective|comprehensive)
      - Output: {project}/.air-executor/test-results.json
      - Schema: {{ total_tests: int, passed: int, failed: int, ... }}

      **VALIDATION REQUIREMENT:**
      You MUST validate the script works before finishing.

      Validation process:
      1. Generate initial script
      2. Test it: `bash run-tests.sh minimal --dry-run`
      3. If failed:
         a. Read error message
         b. Identify issue (wrong package manager? missing dep? wrong path?)
         c. Fix the script
         d. Retry validation (max 5 iterations)
      4. Only save when validation passes

      **Validation checks:**
      - Script is executable
      - Dependencies are installed (npm/yarn/pnpm/pytest/etc)
      - Test directory exists
      - Minimal test run succeeds (or returns valid JSON)

      **Save results:**
      - Script: {project}/.air-executor/run-tests.sh
      - Validation log: {project}/.air-executor/setup-validation.log
      - Config: config/test-cache/{project}-tests.yaml

      **IMPORTANT:**
      - Try running the script for real (with minimal tests)
      - If it fails, fix it until it works
      - Document what you tried in setup-validation.log
      - Only mark as complete when script executes successfully

      Use iterative refinement. Don't give up on first failure.

    timeout: 900  # 15 minutes for generation + validation

    notes: |
      Claude generates script and validates it works through iteration.
      Self-corrects issues before providing final config.
      Guarantees that saved config/script actually works.
```

### Claude's Internal Process

```
Iteration 1: Generate initial script
──────────────────────────────────────
Generated: run-tests.sh
  #!/bin/bash
  npm test

Testing: bash run-tests.sh minimal --dry-run
Result: ❌ FAILED
Error: npm: command not found

Analysis: Package manager is pnpm, not npm
Fix: Change to pnpm


Iteration 2: Fix package manager
──────────────────────────────────────
Updated: run-tests.sh
  #!/bin/bash
  pnpm test

Testing: bash run-tests.sh minimal --dry-run
Result: ❌ FAILED
Error: No test script defined in package.json

Analysis: Test script is "test:unit", not "test"
Fix: Change to pnpm run test:unit


Iteration 3: Fix test script name
──────────────────────────────────────
Updated: run-tests.sh
  #!/bin/bash
  pnpm run test:unit -- --testPathPattern=$1

Testing: bash run-tests.sh minimal --dry-run
Result: ❌ FAILED
Error: No tests found in "minimal"

Analysis: Pattern should be "unit", not $1 directly
Fix: Map strategy to pattern


Iteration 4: Fix test pattern mapping
──────────────────────────────────────
Updated: run-tests.sh
  #!/bin/bash
  case "$1" in
    minimal) PATTERN="unit" ;;
    selective) PATTERN="unit|integration" ;;
    comprehensive) PATTERN="" ;;
  esac
  pnpm run test:unit -- --testPathPattern=$PATTERN

Testing: bash run-tests.sh minimal --dry-run
Result: ✅ SUCCESS
Output: { "total_tests": 5, "passed": 5, "failed": 0 }

✅ Validation passed! Saving config...

Saved:
- Script: .air-executor/run-tests.sh (validated)
- Config: config/test-cache/cc-task-manager-tests.yaml
- Log: .air-executor/setup-validation.log
```

### Validation Log Format

```yaml
# .air-executor/setup-validation.log
validation:
  script: run-tests.sh
  project: cc-task-manager
  language: javascript

  iterations:
    - iteration: 1
      action: "Generated initial script with npm"
      test_command: "bash run-tests.sh minimal --dry-run"
      result: failed
      error: "npm: command not found"
      diagnosis: "Wrong package manager - project uses pnpm"
      fix: "Changed npm to pnpm"

    - iteration: 2
      action: "Fixed package manager to pnpm"
      test_command: "bash run-tests.sh minimal --dry-run"
      result: failed
      error: "No test script defined"
      diagnosis: "Test script is 'test:unit' not 'test'"
      fix: "Updated to 'pnpm run test:unit'"

    - iteration: 3
      action: "Fixed test script name"
      test_command: "bash run-tests.sh minimal --dry-run"
      result: failed
      error: "No tests found in pattern 'minimal'"
      diagnosis: "Need to map strategy to actual test pattern"
      fix: "Added case statement for strategy mapping"

    - iteration: 4
      action: "Added strategy to pattern mapping"
      test_command: "bash run-tests.sh minimal --dry-run"
      result: success
      output: { "total_tests": 5, "passed": 5, "failed": 0 }

  final:
    status: validated
    iterations_needed: 4
    validated_at: "2025-10-03T12:00:00"
    confidence: high
```

## Implementation

### 1. Update Interface Definitions

```yaml
# config/interfaces/test-runner.yaml
interface:
  name: run_tests
  version: "1.0"

  contract:
    # ... existing contract ...

  validation:
    required: true
    max_iterations: 5

    lightweight_test:
      command: "{script} minimal --dry-run"
      expected_exit_code: 0
      expected_output_file: ".air-executor/test-results.json"
      timeout: 60

    validation_criteria:
      - script_exists: true
      - script_executable: true
      - dependencies_available: true
      - output_schema_valid: true
      - minimal_run_succeeds: true

    on_failure:
      - read_error_message: true
      - diagnose_root_cause: true
      - fix_and_retry: true
      - log_iteration: true

    success_criteria:
      - script_runs_without_error: true
      - output_file_created: true
      - output_schema_matches: true
      - no_missing_dependencies: true
```

### 2. Claude's Validation Behavior

**Prompt Pattern:**

```python
# Refinement loop embedded in prompt
prompt = f"""
Generate {task} script for {language} project.

CONTRACT: {load_contract(task)}

**CRITICAL: VALIDATION REQUIRED**

Your workflow:
1. Generate initial implementation
2. Test it: `{validation_command}`
3. If failed:
   - Analyze error
   - Diagnose root cause
   - Fix the issue
   - Retry (max 5 times)
4. Only complete when validation passes

Think step-by-step. Show your iterations.
Don't stop until it works.

Save:
- Working script: {script_path}
- Validation log: {log_path}
"""
```

### 3. Air-Executor Just Checks Result

```python
# setup_phase.py
def setup_with_validation(project_path, language, task):
    """
    Setup phase with self-correcting validation.
    Claude does all the work including validation.
    We just verify the result is ready.
    """
    prompt = build_validation_prompt(task, language, project_path)

    # Claude generates AND validates (internal loop)
    result = subprocess.run([
        python_exec, wrapper_path,
        '--prompt', prompt,
        '--project', project_path
    ], timeout=900)

    # Check that validation succeeded
    script_path = Path(project_path) / ".air-executor" / f"{task}.sh"
    log_path = Path(project_path) / ".air-executor" / "setup-validation.log"

    if not script_path.exists():
        raise SetupError(f"Script not created: {task}")

    # Read validation log
    log = yaml.safe_load(log_path.open())
    if log['final']['status'] != 'validated':
        raise SetupError(f"Validation failed: {log['final']}")

    print(f"✅ {task} validated in {log['final']['iterations_needed']} iterations")

    return {
        'script': script_path,
        'validated': True,
        'iterations': log['final']['iterations_needed']
    }
```

## Benefits

### 1. Guaranteed Working Configs
- ✅ Every saved config has been tested
- ✅ No "generate and hope" approach
- ✅ Validated before we use it

### 2. Self-Correcting
- ✅ Claude fixes its own mistakes
- ✅ Learns from failures
- ✅ Iterates until success

### 3. Transparent Process
- ✅ Validation log shows iterations
- ✅ Can see what was tried
- ✅ Understand why it works

### 4. Robust to Edge Cases
- ✅ Handles missing dependencies
- ✅ Adapts to project specifics
- ✅ Works with unusual setups

### 5. Zero Manual Intervention
- ✅ No debugging needed
- ✅ No config tweaking
- ✅ Just works

## Edge Cases Handled

### Case 1: Wrong Package Manager
```
Iteration 1: Tried npm
Error: npm: command not found
Fix: Detected pnpm-lock.yaml, switched to pnpm
Result: ✅ Works
```

### Case 2: Missing Dependency
```
Iteration 1: Tried running tests
Error: jest: command not found
Fix: Ran `pnpm install` first, added to script
Result: ✅ Works
```

### Case 3: Wrong Test Directory
```
Iteration 1: Looked in tests/
Error: No tests found
Fix: Found tests in __tests__/, updated path
Result: ✅ Works
```

### Case 4: Complex Build Step
```
Iteration 1: Ran tests directly
Error: TypeScript not compiled
Fix: Added `pnpm run build` before tests
Result: ✅ Works
```

## Prompt Engineering for Self-Correction

### Key Elements

**1. Explicit Iteration Requirement:**
```
You MUST iterate until validation passes.
Max 5 iterations.
Don't give up on first failure.
```

**2. Error Analysis Pattern:**
```
For each failure:
1. Read full error message
2. Identify root cause
3. Propose fix
4. Apply fix
5. Retest
```

**3. Learning from Errors:**
```
If iteration N failed because of X,
don't make the same mistake in iteration N+1.

Build on previous attempts.
```

**4. Validation Criteria:**
```
Success means:
- Script runs without error
- Output file created
- Schema matches contract
- No missing dependencies
```

## Integration with Existing Phases

### Setup Phase Enhancement

```python
# Before (no validation)
def setup_test_runner(project):
    claude_generate_script(project)
    # Hope it works ¯\_(ツ)_/¯

# After (with validation)
def setup_test_runner(project):
    result = claude_generate_and_validate(project)
    # Guaranteed to work ✅

    # Can proceed confidently
    test_result = run_script(result.script)
    # No errors, validated config
```

## Monitoring & Observability

### Success Metrics

```yaml
# Track validation effectiveness
metrics:
  total_setups: 100
  first_try_success: 30  # 30% work immediately
  validated_after_refinement: 68  # 68% work after iteration
  failed_validation: 2  # 2% couldn't be fixed

  average_iterations: 2.3
  max_iterations_seen: 5

  common_issues:
    wrong_package_manager: 25
    missing_dependencies: 20
    wrong_test_path: 15
    build_step_needed: 8
```

### Failure Analysis

```yaml
# When validation fails completely (rare)
failure_analysis:
  project: problematic-project
  issue: "Tests require database setup"
  iterations_attempted: 5
  last_error: "Connection refused: postgres:5432"

  recommendation: |
    This project needs environment setup that validation
    can't handle automatically. Manual intervention required.

  action: |
    Add to project config:
      test_setup:
        requires_database: true
        setup_script: scripts/setup-test-db.sh
```

## Summary

**Your Insight:**
> "Even though claude can generate config, we can fail to execute it. Let claude evaluate our execution success before providing result."

**Architecture:**
```
Generate → Validate → ❌ Failed? → Refine → Validate → ✅ Success
```

**Key Features:**
1. Self-correcting loop (max 5 iterations)
2. Lightweight validation (dry-run, minimal tests)
3. Transparent logging (shows what was tried)
4. Guaranteed working configs

**Result:**
- 100% confidence in generated configs
- Zero manual debugging
- Robust to edge cases
- Self-improving system

**Next Step:**
Implement validation contract in interface definitions and update setup prompts.
