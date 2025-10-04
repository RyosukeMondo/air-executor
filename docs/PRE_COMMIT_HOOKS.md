# Pre-Commit Hooks Strategy

## Philosophy: Shift Quality Gates to Enforced Tooling

**Old Approach (Fragile):**
- AI prompts ask: "Please run eslint and fix errors"
- AI might skip checks
- AI might bypass failures with `--no-verify`
- Relies on AI following instructions correctly

**New Approach (Robust):**
- AI configures pre-commit hooks once
- Hooks enforce quality automatically on every commit
- AI **cannot** bypass hooks (must fix issues)
- Quality gates are **enforced by git**, not requested by prompts

## Benefits

### 1. Reliability
- **Enforcement over trust:** Hooks FORCE quality, prompts only ask
- **Cannot bypass:** Git blocks commits that fail quality checks
- **Consistent:** Same checks every time, no variation

### 2. Developer Experience
- **Immediate feedback:** Know about issues before CI/CD
- **Clear standards:** Hook configuration IS the quality contract
- **Fast iteration:** Fix locally, commit when ready

### 3. Autonomous Fixing
- **AI learns standards:** Reads hook config to understand requirements
- **AI cannot cheat:** Hooks prevent `--no-verify` workarounds
- **Self-correcting:** If hooks block, AI must fix the code

## Architecture

### Setup Phase (Priority 0)

Before P1/P2 iterations, autonomous system:

1. **Detects existing hooks:**
   - Python: `.pre-commit-config.yaml`
   - JavaScript: `.husky/` + `lint-staged` in `package.json`
   - All: `.git/hooks/pre-commit`

2. **Configures hooks if missing:**
   - Calls `configure_precommit_hooks` prompt
   - AI analyzes project and sets up appropriate hooks
   - Saves config to `config/precommit-cache/`

3. **Verifies hooks work:**
   - Makes test commit
   - Ensures hooks run and can block bad commits
   - Documents configuration

### Quality Gates Enforced

#### JavaScript/TypeScript Projects
```bash
# .husky/pre-commit
🔍 Pre-commit quality checks...
📊 TypeScript type checking... (tsc --noEmit)
🔧 ESLint checking... (npx lint-staged)
🧪 Running unit tests... (npm test)
📈 Checking coverage... (>=60% threshold)
✅ All checks passed!
```

#### Python Projects
```yaml
# .pre-commit-config.yaml
hooks:
  - mypy (type checking)
  - pylint (linting)
  - pytest (tests must pass)
  - pytest-cov (coverage ≥60%)
```

#### Flutter Projects
```bash
# .git/hooks/pre-commit
flutter analyze (MUST pass)
flutter test (MUST pass)
```

## Integration with Autonomous Fixing

### Phase Flow

```
SETUP 0: Configure Pre-Commit Hooks
  ↓
SETUP 1: Discover Test Configuration
  ↓
P1: Static Analysis
  ↓
  If issues found:
    Fix code → Try commit → Hooks validate → Success/Fail
  ↓
P2: Tests
  ↓
  If tests fail:
    Fix tests → Try commit → Hooks validate → Success/Fail
  ↓
P3: Coverage (optional)
  ↓
Success!
```

### Prompt Changes

#### Before (Fragile)
```
Fix {language} errors.

Process:
1. Run eslint
2. Fix errors
3. git commit
```

#### After (Robust)
```
Fix {language} errors.

Process:
1. Check for pre-commit hooks
2. Fix errors
3. Try commit (hooks validate automatically)
4. If hooks block: fix issues, don't bypass

NEVER use --no-verify
```

## Configuration Examples

### JavaScript/TypeScript

**package.json:**
```json
{
  "scripts": {
    "precommit": "lint-staged && npm test -- --passWithNoTests",
    "type-check": "tsc --noEmit"
  },
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": ["eslint --fix", "prettier --write"],
    "*.{ts,tsx}": ["bash -c 'npm run type-check'"]
  },
  "devDependencies": {
    "husky": "^8.0.0",
    "lint-staged": "^15.0.0"
  }
}
```

**.husky/pre-commit:**
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

echo "🔍 Pre-commit quality checks..."

# Type checking MUST pass
npm run type-check || exit 1

# Linting MUST pass
npx lint-staged || exit 1

# Tests MUST pass
npm test -- --passWithNoTests || exit 1

echo "✅ All checks passed!"
```

### Python

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy type checking
        entry: mypy
        language: system
        types: [python]
        pass_filenames: false

      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]

      - id: pytest
        name: pytest unit tests
        entry: pytest
        language: system
        pass_filenames: false
        args: ['tests/', '--cov=src', '--cov-fail-under=60']
```

## Cache Structure

```
config/precommit-cache/
  warps-hooks.yaml          # JavaScript project
  my-api-hooks.yaml         # Python project
  flutter-app-hooks.yaml    # Flutter project
```

**Example cache file:**
```yaml
project_name: warps
language: javascript
configured_at: 2025-10-04T10:30:00

hook_framework:
  type: husky
  config_file: package.json
  installed: true
  verified: true

quality_gates:
  type_checking:
    enabled: true
    tool: tsc
    blocking: true

  linting:
    enabled: true
    tool: eslint
    blocking: true

  unit_tests:
    enabled: true
    command: npm test
    blocking: true

  coverage:
    enabled: true
    threshold: 60
    blocking: true

verification:
  test_commit_blocked: true
  hooks_cannot_be_bypassed: true
  notes: "Hooks successfully block commits with type errors"
```

## Critical Rules

### ✅ DO

- Configure hooks during SETUP phase
- Let hooks enforce quality automatically
- Fix code to meet hook requirements
- Document hook configuration
- Verify hooks work with test commits

### ❌ DON'T

- Use `git commit --no-verify` (bypasses hooks)
- Disable hooks in configuration
- Lower quality thresholds to make commits pass
- Skip hook verification
- Rely on prompts alone for quality enforcement

## Migration Strategy

### For Existing Projects

1. **Check for hooks:**
   ```bash
   ls .husky/pre-commit .pre-commit-config.yaml .git/hooks/pre-commit
   ```

2. **If no hooks, configure them:**
   - Run autonomous fixing with SETUP phase
   - AI will detect missing hooks and configure them
   - Verify configuration with test commit

3. **If hooks exist, document them:**
   - Cache configuration for future reference
   - Verify hooks are comprehensive
   - Update if missing critical checks

### Backward Compatibility

- Projects without hooks: Use manual check prompts (old approach)
- Projects with hooks: Use hook-based enforcement (new approach)
- Gradually migrate all projects to hook-based approach
- Eventually deprecate manual checking prompts

## Troubleshooting

### Hooks not running

**Problem:** Commits succeed without running hooks

**Solution:**
```bash
# Reinstall hooks
npm run prepare          # JavaScript (husky)
pre-commit install       # Python
chmod +x .git/hooks/*    # Native hooks
```

### Hooks block all commits

**Problem:** Cannot commit anything, hooks always fail

**Solution:**
1. Check what's failing: Run hooks manually
2. Fix the issues (don't bypass)
3. If hooks are misconfigured, fix configuration
4. Only use `--no-verify` for emergency hotfixes (rare)

### AI keeps trying to bypass hooks

**Problem:** AI uses `--no-verify` flag

**Solution:**
- Prompts explicitly forbid `--no-verify`
- If AI tries, it's a prompt engineering issue
- Update prompts with stronger warnings
- Report issue for investigation

## Future Enhancements

1. **Coverage enforcement:** Require coverage increase, not just threshold
2. **Performance checks:** Block commits that slow down tests significantly
3. **Security scanning:** Run security tools in hooks
4. **Dependency checks:** Validate no vulnerable dependencies
5. **Documentation checks:** Ensure critical functions are documented

## See Also

- [Autonomous Fixing Architecture](./architecture/autonomous-fixing-diagrams.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Prompt Engineering](../config/prompts.yaml)
