# Pre-Commit Hook Bypass Policy

## Overview

This document explains when and why the autonomous fixing system uses `git commit --no-verify` to bypass pre-commit hooks.

## Policy Summary

```
┌────────────────────────────────────────────────────────┐
│  Pre-Commit Hook Bypass Policy                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ ALLOWED (--no-verify):                             │
│     • P2: Test fixing iterations                       │
│     • Reason: Prevents circular dependency             │
│     • Scope: Individual test fix commits               │
│                                                         │
│  ❌ FORBIDDEN (no bypass):                             │
│     • P1: Static analysis/linting fixes                │
│     • P3: Coverage improvements                        │
│     • P4: E2E test additions                           │
│     • All other phases and manual development          │
│                                                         │
│  🔒 FINAL VALIDATION:                                  │
│     • After all P2 tests pass                          │
│     • Full pre-commit validation runs                  │
│     • Ensures no quality regression                    │
│                                                         │
└────────────────────────────────────────────────────────┘
```

## Rationale

### The Problem: Circular Dependency

When fixing tests iteratively, pre-commit hooks create a catch-22:

```
1. AI fixes Test A (passes)
2. AI commits fix
3. Pre-commit hook runs ALL tests
4. Test B still fails (not fixed yet)
5. Hook blocks commit
6. AI cannot make progress
```

### The Solution: Selective Bypass

During **P2 test fixing only**, use `--no-verify`:

```
1. AI fixes Test A (passes)
2. AI commits with --no-verify
   ✅ Commit succeeds
3. AI fixes Test B (passes)
4. AI commits with --no-verify
   ✅ Commit succeeds
5. All tests pass → P2 complete
6. Final validation with full hooks
   ✅ Quality gate passed
```

## Implementation

### Updated Prompts

**File**: `airflow_dags/autonomous_fixing/executor_prompts.py`

```python
def test_fix_prompt(task, summary: Optional[Dict]) -> str:
    """Uses --no-verify during test fixing"""

    prompt = f"""
    ...
    git add -A
    git commit --no-verify -m "fix(test): {commit_msg}"

    **Why --no-verify?**
    During iterative test fixing, pre-commit hooks that run tests
    create a circular dependency. Using --no-verify allows incremental
    progress. Final validation will occur after all tests pass.
    """
    return prompt
```

**File**: `config/prompts.yaml`

```yaml
tests:
  fix_failures:
    template: |
      ...
      git add . && git commit --no-verify -m "fix: Fix test failures"

      **Why --no-verify during test fixing?**
      Pre-commit hooks that run tests create a circular dependency.
      --no-verify allows incremental progress.
      Final validation occurs after ALL tests pass (P2 gate).
```

### Phase-Specific Behavior

| Phase | Pre-Commit Hooks | --no-verify Allowed? | Reason |
|-------|------------------|----------------------|--------|
| **P1: Static Analysis** | ✅ Run normally | ❌ No | Linters should pass immediately |
| **P2: Test Fixing** | ⏭️ Bypassed | ✅ Yes | Prevents circular dependency |
| **P3: Coverage** | ✅ Run normally | ❌ No | Tests already passing |
| **P4: E2E** | ✅ Run normally | ❌ No | Final quality gate |
| **Manual Dev** | ✅ Run normally | ❌ No | Standard development |

## Safety Mechanisms

### 1. Explicit Documentation

Every prompt that uses `--no-verify` includes:
- Clear explanation of WHY
- When it's appropriate
- What final validation will occur

### 2. Limited Scope

Only applies to:
- Test fixing (P2 phase)
- Autonomous fixing mode
- Iterative commits

Does NOT apply to:
- Linting/formatting fixes
- Coverage improvements
- Manual development
- Final commits

### 3. Final Validation

After P2 completes:
```python
# core/iteration_engine.py
def complete_p2_phase(self):
    """After all tests pass, run final validation"""
    if self.phase_complete('P2'):
        # Run test suite with full hooks
        result = self.analyzer.run_tests_with_hooks()
        if not result.success:
            logger.error("P2 final validation failed")
            raise ValidationError("Tests pass individually but fail with hooks")
```

### 4. Audit Logging

All hook bypasses are logged:

```python
# core/state_manager.py
def log_hook_bypass(self, phase: str, iteration: int, reason: str):
    """Track when and why hooks are bypassed"""
    self.redis.rpush(
        f"hook_bypass_log:{self.project_name}",
        json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'phase': phase,
            'iteration': iteration,
            'reason': reason
        })
    )
```

## Examples

### Test Fixing (P2) - ✅ Allowed

```bash
# Claude's commands during P2 test fixing:
flutter test test/widget_test.dart  # Run specific test
# ... test passes ...
git add -A
git commit --no-verify -m "fix(test): Fix widget initialization"
```

**Rationale**: Test is fixed, but other tests may still fail. Hook would block progress.

### Linting (P1) - ❌ Forbidden

```bash
# Claude's commands during P1 linting:
flutter analyze --no-pub
# ... no issues ...
git add -A
git commit -m "style: Fix linting issues"  # NO --no-verify!
```

**Rationale**: Linters should pass. If hook blocks, code needs more fixing.

### Coverage (P3) - ❌ Forbidden

```bash
# Claude's commands during P3 coverage:
flutter test --coverage
# ... coverage improves ...
git add -A
git commit -m "test: Improve coverage for auth module"  # NO --no-verify!
```

**Rationale**: All tests already pass (P2 complete). Hooks should succeed.

## Migration Guide

### For Users

If you maintain the target projects being fixed:

**Option 1: Accept the bypass** (recommended)
- Trust the P2 final validation
- Review P2 completion logs
- Verify final commit passes all hooks

**Option 2: Use environment-aware hooks** (advanced)
```bash
# .husky/pre-commit or .git/hooks/pre-commit
if [ "$AUTONOMOUS_FIXING" = "true" ] && [ "$FIXING_PHASE" = "P2_tests" ]; then
  echo "⏭️  Skipping test validation during autonomous test fixing"
  npm run lint || exit 1  # Still run linters
  exit 0
fi

# Normal validation
npm run precommit || exit 1
```

### For Developers

No changes needed. The system now:
- ✅ Bypasses hooks during P2 automatically
- ✅ Explains why in every prompt
- ✅ Runs final validation after P2
- ✅ Logs all bypasses for audit

## Monitoring

### Check Bypass Logs

```bash
# View bypass audit trail
redis-cli
> LRANGE hook_bypass_log:myproject 0 -1

# Example output:
{"timestamp": "2025-10-04T10:30:00Z", "phase": "P2", "iteration": 3, "reason": "test_iteration"}
{"timestamp": "2025-10-04T10:31:00Z", "phase": "P2", "iteration": 4, "reason": "test_iteration"}
```

### Verify Final Validation

```bash
# Check P2 completion in logs
grep "P2 final validation" logs/autonomous_fixing.log

# Expected:
✅ P2 final validation passed - all tests pass with full hooks
```

## FAQ

**Q: Isn't this dangerous? Won't code quality suffer?**

A: No. We only bypass during **incremental test fixing**. Final P2 validation ensures all tests pass with full hooks before moving to P3.

**Q: What if Claude abuses --no-verify in other phases?**

A: Prompts are explicit about when it's allowed. Only the test fixing prompt includes `--no-verify`. All other prompts forbid it.

**Q: Can I disable this behavior?**

A: Yes. Edit `executor_prompts.py` and remove `--no-verify` from `test_fix_prompt()`. But this will cause the circular dependency problem.

**Q: What about linting/formatting hooks?**

A: Those still run during P1 and all other phases. Only test-running hooks are bypassed during P2.

**Q: How do I verify P2 final validation occurred?**

A: Check logs for "P2 final validation passed" message, or verify the final P2 commit passes `npm test` / `pytest` locally.

## Related Documentation

- [Adaptive Pre-Commit Strategy](./adaptive-precommit-strategy.md) - Full strategy details
- [Pre-Commit Integration Architecture](../docs/architecture/pre-commit-integration.md) - System design
- [Priority-Based Execution Flow](../docs/architecture/autonomous-fixing-diagrams.md#priority-based-execution-flow) - Phase descriptions

## Changelog

- **2025-10-04**: Initial policy - Allow --no-verify during P2 test fixing only
- **Future**: Consider environment-aware hooks for even more granular control
