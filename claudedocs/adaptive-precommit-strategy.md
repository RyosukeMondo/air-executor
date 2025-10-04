# Adaptive Pre-Commit Hook Strategy

## Problem Statement

When autonomous AI fixes tests, pre-commit hooks that run tests create a catch-22:
1. AI fixes failing tests
2. AI tries to commit fixes
3. Pre-commit hook runs ALL tests (including unfixed ones)
4. Hook fails → commit blocked
5. AI cannot make progress → gives up

## Root Cause

Pre-commit hooks are **too strict during iterative fixing**:
- They're designed for final validation
- But autonomous fixing needs **incremental commits**
- Tests need multiple iterations to fix completely

## Solution: Context-Aware Hook Bypass

### Strategy Overview

**Principle**: Pre-commit hooks are valuable but must be **adaptive** during autonomous fixing.

```
┌─────────────────────────────────────────────────────────┐
│  Context-Aware Commit Strategy                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Normal Development:                                     │
│    → Full pre-commit validation                         │
│    → All tests must pass                                │
│    → --no-verify is FORBIDDEN                           │
│                                                          │
│  Autonomous Test Fixing (Iteration Mode):               │
│    → Bypass test-running hooks ONLY                     │
│    → Keep linting/formatting hooks active               │
│    → Use: git commit --no-verify OR selective bypass    │
│    → Re-enable full validation after P2 completes       │
│                                                          │
│  Autonomous Lint/Type Fixing:                           │
│    → Full pre-commit validation                         │
│    → No bypass (linters should pass)                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Implementation Approaches

### Approach 1: Conditional --no-verify (Simple)

**When**: During P2 test fixing iterations only

**How**:
```yaml
# In executor_prompts.py - test_fix_prompt

if phase == "P2_test_fixing":
    commit_instruction = """
    git add -A
    git commit --no-verify -m "fix(test): {message}"
    """
else:
    commit_instruction = """
    git add -A
    git commit -m "fix: {message}"
    """
```

**Pros**:
- Simple implementation
- Immediate solution
- AI doesn't need to understand hooks

**Cons**:
- Bypasses ALL hooks (including formatters)
- Less granular control

### Approach 2: Temporary Hook Disable (Recommended)

**When**: During P2 test fixing iterations

**How**:
```bash
# Before P2 test fixing
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
mv .husky/pre-commit .husky/pre-commit.disabled

# After P2 completes
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
mv .husky/pre-commit.disabled .husky/pre-commit
```

**Pros**:
- Clean separation of concerns
- Hooks fully restored after P2
- No partial bypass confusion

**Cons**:
- Requires file operations
- More complex orchestration

### Approach 3: Environment Variable Control (Best)

**When**: During any autonomous fixing iteration

**How**:
```bash
# Set environment flag
export AUTONOMOUS_FIXING=true
export FIXING_PHASE=P2_tests

# Commit normally
git commit -m "fix(test): message"

# Hook script checks environment
if [ "$AUTONOMOUS_FIXING" = "true" ] && [ "$FIXING_PHASE" = "P2_tests" ]; then
  echo "⏭️  Skipping test validation during autonomous test fixing"
  exit 0
fi

# Normal hook validation...
```

**Modified pre-commit hooks**:
```bash
#!/bin/bash
# .git/hooks/pre-commit or .husky/pre-commit

# Check if in autonomous fixing mode
if [ "$AUTONOMOUS_FIXING" = "true" ]; then
  case "$FIXING_PHASE" in
    P2_tests)
      echo "⏭️  [Autonomous Fixing] Skipping test hooks during P2"
      # Still run linters/formatters
      npm run lint || exit 1
      # Skip tests
      exit 0
      ;;
    P1_static)
      echo "✅ [Autonomous Fixing] Running full validation for P1"
      # Run everything normally
      ;;
  esac
fi

# Normal pre-commit validation
npm run precommit || exit 1
```

**Pros**:
- Granular control per phase
- Hooks remain active
- Self-documenting
- Easy to debug

**Cons**:
- Requires hook modification
- Projects need to adopt pattern

## Recommended Solution: Hybrid Approach

Combine Approach 1 (simple) with Approach 3 (robust):

### Phase 1: Immediate Fix (Use Approach 1)

Update `executor_prompts.py` to use `--no-verify` during test fixing:

```python
def test_fix_prompt(task, summary: Optional[Dict], iteration_context: Dict) -> str:
    """Generate prompt for test failure fix"""

    # Determine if we should bypass hooks
    phase = iteration_context.get('phase')
    iteration = iteration_context.get('iteration', 0)

    if phase == 'P2' and iteration > 0:
        # During iterative test fixing, bypass hooks
        commit_cmd = '''git add -A
git commit --no-verify -m "fix(test): {msg}"'''
        bypass_explanation = """
**Note**: Using --no-verify because:
- We're in iterative test fixing mode (P2)
- Pre-commit hooks that run tests would create a circular dependency
- Hooks will be respected after all tests pass
"""
    else:
        # Normal commit with full validation
        commit_cmd = '''git add -A
git commit -m "fix(test): {msg}"'''
        bypass_explanation = ""

    prompt = f"""Fix this failing test:
...
{commit_cmd}
{bypass_explanation}
"""
    return prompt
```

### Phase 2: Robust Solution (Implement Approach 3)

**Documentation for users**: Create hook templates that respect autonomous fixing context.

**File**: `docs/PRECOMMIT_AUTONOMOUS_PATTERN.md`

```markdown
# Autonomous-Friendly Pre-Commit Hooks

## Pattern: Environment-Aware Hooks

Your pre-commit hooks should detect autonomous fixing mode:

### JavaScript (husky)

\`\`\`bash
# .husky/pre-commit
#!/bin/bash

# Detect autonomous fixing mode
if [ "$AUTONOMOUS_FIXING" = "true" ]; then
  case "$FIXING_PHASE" in
    P2_tests)
      echo "⏭️  Skipping tests during autonomous test fixing (P2)"
      npm run lint || exit 1  # Keep linting
      exit 0
      ;;
  esac
fi

# Normal validation
npm run precommit || exit 1
\`\`\`

### Python (pre-commit framework)

\`\`\`yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: bash -c 'if [ "$AUTONOMOUS_FIXING" = "true" ] && [ "$FIXING_PHASE" = "P2_tests" ]; then echo "⏭️  Skipping tests (P2)"; exit 0; fi; pytest tests/'
        language: system
\`\`\`
```

## Decision Matrix

| Scenario | Hook Behavior | Bypass Allowed? | Method |
|----------|---------------|-----------------|---------|
| **P1: Static Analysis** | Full validation | ❌ No | Normal commit |
| **P2: Test Fixing (Iteration 1)** | Lint only | ✅ Yes | `--no-verify` |
| **P2: Test Fixing (Iteration N)** | Lint only | ✅ Yes | `--no-verify` |
| **P2: All Tests Pass** | Full validation | ❌ No | Normal commit |
| **P3: Coverage** | Full validation | ❌ No | Normal commit |
| **Manual Development** | Full validation | ❌ No | Normal commit |

## Configuration Changes

### Update `config/prompts.yaml`

```yaml
tests:
  fix_failures:
    template: |
      Fix failing {language} tests.

      **IMPORTANT - Commit Strategy**:

      During iterative test fixing, pre-commit hooks that run tests
      create a circular dependency. Therefore:

      1. Fix the test failures
      2. Commit with: `git add -A && git commit --no-verify -m "fix(test): {message}"`
      3. The --no-verify flag is REQUIRED during test fixing iterations
      4. After ALL tests pass, a final commit with full validation will occur

      **Rationale**:
      - Pre-commit hooks run ALL tests
      - You're fixing tests incrementally (not all at once)
      - Hook would fail on unfixed tests → blocks progress
      - Final P2 validation ensures all tests pass
```

### Update `core/iteration_engine.py`

Add iteration context to prompts:

```python
class IterationEngine:
    def fix_issues(self, phase: str, iteration: int):
        context = {
            'phase': phase,
            'iteration': iteration,
            'bypass_hooks': phase == 'P2' and iteration > 0
        }

        prompt = self.prompt_generator.generate(task, context)
        # Pass context to Claude
```

## Safety Guardrails

### 1. Re-validation After P2

After P2 completes (all tests pass), run one final validation commit:

```python
def finalize_p2_phase(self):
    """After all tests pass, create a validation commit"""
    if self.all_tests_passing():
        # Final commit with full hooks
        subprocess.run(['git', 'commit', '--amend', '--no-edit'], check=True)
        logger.info("✅ Final P2 commit with full pre-commit validation")
```

### 2. Audit Trail

Log all hook bypasses:

```python
if bypass_hooks:
    logger.warning(
        f"⚠️  Bypassing pre-commit hooks: phase={phase}, iteration={iteration}"
    )
    # Log to state manager
    self.state.log_hook_bypass(phase, iteration, reason="test_iteration")
```

### 3. User Notification

Show clear messaging:

```
🔧 Fixing tests (iteration 3/10)
⏭️  Pre-commit hooks bypassed during test fixing
✅ Final validation will run after all tests pass
```

## Migration Path

### Week 1: Immediate Fix
- ✅ Update test fixing prompts to use `--no-verify`
- ✅ Add clear documentation about when/why
- ✅ Deploy to production

### Week 2: Enhanced Control
- ✅ Add iteration context to prompts
- ✅ Implement bypass logging
- ✅ Add final validation step

### Week 3: Hook Template
- ✅ Create environment-aware hook templates
- ✅ Update documentation
- ✅ Encourage users to adopt pattern

## Success Metrics

- ✅ Test fixing iterations no longer blocked by pre-commit
- ✅ All final commits still pass full validation
- ✅ No increase in merged code quality issues
- ✅ Faster autonomous fixing iterations

## FAQ

**Q: Isn't bypassing hooks dangerous?**
A: Only during **autonomous test fixing iterations**. Final commit has full validation.

**Q: What if AI abuses --no-verify?**
A: Prompts are explicit about when it's allowed. Audit logs track usage.

**Q: Won't this reduce code quality?**
A: No - final validation still runs. This only enables **incremental progress**.

**Q: What about linting/formatting?**
A: Those hooks should STILL run (use selective bypass, not --no-verify).

## References

- [Pre-Commit Integration Architecture](../docs/architecture/pre-commit-integration.md)
- [Priority-Based Execution Flow](../docs/architecture/autonomous-fixing-diagrams.md#priority-based-execution-flow)
- [Hook Level Configuration](../config/hook-levels.yaml)
