# Prompt Configuration Architecture

## Overview

**Problem Solved**: Prompts were scattered throughout code as magic strings, making prompt engineering difficult and violating separation of concerns.

**Solution**: Config-driven architecture with centralized prompt management in YAML.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    config/prompts.yaml                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Single Source of Truth for ALL LLM prompts        │    │
│  │                                                     │    │
│  │ • static_issues.error                             │    │
│  │ • static_issues.complexity                        │    │
│  │ • tests.fix_failures                              │    │
│  │ • tests.create_tests                              │    │
│  │ • language_overrides (python/js/flutter/go)       │    │
│  │ • timeouts                                        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    fixer._load_prompts()
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 core/fixer.py (IssueFixer)                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Code = Logic, Config = Domain Knowledge           │    │
│  │                                                     │    │
│  │ _fix_single_issue()                               │    │
│  │   → Load template from prompts['static_issues']   │    │
│  │   → Format with {language}, {file}, {message}     │    │
│  │   → Get timeout from prompts['timeouts']          │    │
│  │                                                     │    │
│  │ _fix_failing_tests()                              │    │
│  │   → Load template from prompts['tests']           │    │
│  │   → Format with {language}, {failed}, {total}     │    │
│  │                                                     │    │
│  │ _create_tests_for_project()                       │    │
│  │   → Load template from prompts['tests']           │    │
│  │   → Add language-specific hints                   │    │
│  │   → Format with {language}                        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### Why YAML?

| Requirement | YAML | JSON | TOML | .env |
|-------------|------|------|------|------|
| Multi-line strings | ✅ Natural | ❌ Ugly | ✅ OK | ❌ No |
| Comments | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Human-readable | ✅ Yes | ⚠️ OK | ✅ Yes | ⚠️ OK |
| Already in project | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Structure support | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |

**Winner: YAML** - Perfect for multi-line prompts, already used in project configs.

## File Structure

```
config/
├── prompts.yaml              # ← NEW: Centralized prompts
├── projects/
│   ├── air-executor.yaml
│   ├── cc-task-manager.yaml
│   ├── mind-training.yaml
│   ├── money-making-app.yaml
│   └── warps.yaml

airflow_dags/autonomous_fixing/
└── core/
    ├── fixer.py              # ← MODIFIED: Loads from prompts.yaml
    ├── analyzer.py
    ├── scorer.py
    └── iteration_engine.py
```

## prompts.yaml Structure

```yaml
# P1: Static Issues
static_issues:
  error:
    template: |
      Fix this {language} error in {file}:
      {message}
    notes: "Keep simple - Claude knows errors"

  complexity:
    template: |
      Refactor {file} to reduce complexity...
    notes: "Emphasize maintaining functionality"

# P2: Tests
tests:
  fix_failures:
    template: |
      Fix failing {language} tests...

  create_tests:
    template: |
      This {language} project has NO TESTS...
      1. Find/install test framework
      2. Analyze codebase
      3. Create 3-5 tests
      ...

# Language-specific overrides
language_overrides:
  python:
    create_tests:
      framework_hint: "Use pytest with fixtures..."
  javascript:
    create_tests:
      framework_hint: "Use jest with describe/it..."

# Timeouts
timeouts:
  fix_static_issue: 300    # 5 min
  fix_test_failure: 600    # 10 min
  create_tests: 900        # 15 min
```

## Code Changes

### Before (Magic Strings)

```python
def _create_tests_for_project(self, project_info: Dict) -> bool:
    prompt = (
        f"This {project_info['language']} project has NO TESTS. "
        f"Your task:\n"
        f"1. Find or install appropriate test framework...\n"
        # ... 10 more lines of hardcoded prompt
    )

    subprocess.run([...], timeout=900)  # Hardcoded timeout
```

### After (Config-Driven)

```python
def _create_tests_for_project(self, project_info: Dict) -> bool:
    # Load template from config
    template = self.prompts['tests']['create_tests']['template']
    prompt = template.format(language=project_info['language'])

    # Add language-specific hints
    lang_overrides = self.prompts.get('language_overrides', {})
    if project_info['language'] in lang_overrides:
        prompt += f"\n\n{lang_overrides[project_info['language']]['framework_hint']}"

    # Get timeout from config
    timeout = self.prompts.get('timeouts', {}).get('create_tests', 900)

    subprocess.run([...], timeout=timeout)
```

## Benefits

### 1. Clean Separation of Concerns
- **Code**: Logic and control flow
- **Config**: Domain knowledge and prompts
- **No mixing**: Prompts never in Python files

### 2. Easy Iteration
- Change prompts without touching code
- Test different prompt strategies quickly
- A/B test prompt effectiveness

### 3. Maintainability
- Single source of truth
- Easy to find and update prompts
- Comments document prompt engineering decisions

### 4. Version Control
- Prompts tracked in git like code
- Can revert prompt changes
- Diff shows exact prompt modifications

### 5. Language-Specific Customization
- Override prompts per language
- Add framework-specific hints
- Keep base prompts language-agnostic

## Usage Examples

### Iterate on Prompt Engineering

```bash
# 1. Edit prompt in config
vim config/prompts.yaml

# 2. Test changes (no code rebuild needed)
pm2 reload all

# 3. Monitor results
tail -f logs/fix-*.log

# 4. Iterate
vim config/prompts.yaml
```

### Add New Prompt Type

```yaml
# In config/prompts.yaml
p3_coverage:
  improve_coverage:
    template: |
      Improve test coverage for {file}
      Current coverage: {current}%
      Target: {target}%
```

```python
# In fixer.py
def improve_coverage(self, coverage_info):
    template = self.prompts['p3_coverage']['improve_coverage']['template']
    prompt = template.format(
        file=coverage_info['file'],
        current=coverage_info['current'],
        target=coverage_info['target']
    )
    # ... call claude_wrapper
```

### Language-Specific Customization

```yaml
language_overrides:
  go:
    create_tests:
      framework_hint: "Use Table Driven Tests pattern with subtests"
    complexity:
      template: |
        Refactor {file} using Go idioms:
        - Use early returns
        - Extract methods with clear names
        - Keep functions < 50 lines
```

## Fallback Behavior

If `config/prompts.yaml` not found:

```python
def _load_prompts(self) -> Dict:
    # Try multiple paths
    possible_paths = [
        Path(__file__).parent.parent.parent / 'config' / 'prompts.yaml',
        Path('config/prompts.yaml'),
    ]

    for path in possible_paths:
        if path.exists():
            return yaml.safe_load(path.open())

    # Fallback: minimal default prompts
    print("⚠️  Warning: prompts.yaml not found, using fallback prompts")
    return {
        'static_issues': {
            'error': {'template': 'Fix this {language} error...'},
            # ... minimal defaults
        }
    }
```

**Graceful degradation**: System works even without config file.

## Best Practices

### 1. Prompt Design
- **Specific but flexible**: Provide structure, trust Claude's expertise
- **Step-by-step for complex tasks**: Break down into clear process
- **LLM-as-a-judge pattern**: Let Claude analyze and decide
- **Language-agnostic**: Use {language} parameter, customize only when needed

### 2. Template Variables
- Keep variable names clear: `{language}`, `{file}`, `{message}`
- Use Python `.format()` syntax: `{variable}`
- Document expected variables in comments

### 3. Comments
- Explain WHY a prompt is structured that way
- Note prompt engineering decisions
- Document what worked/didn't work

### 4. Version Control
- Commit prompt changes with clear messages
- Reference related code changes
- Document prompt effectiveness in commit messages

### 5. Testing
- Test prompt changes on sample projects first
- Monitor logs for prompt effectiveness
- Iterate based on real results

## Future Enhancements

### Prompt Versioning
```yaml
tests:
  create_tests:
    v1:  # Legacy
      template: "Simple prompt..."
    v2:  # Current
      template: "Improved prompt with more structure..."
    active: "v2"
```

### Metrics Collection
```yaml
tests:
  create_tests:
    template: "..."
    metrics:
      success_rate: 0.85
      avg_time_seconds: 420
      last_updated: "2025-10-03"
```

### A/B Testing
```yaml
tests:
  create_tests:
    strategy_a:
      template: "Approach 1..."
      weight: 0.5
    strategy_b:
      template: "Approach 2..."
      weight: 0.5
```

## Summary

**What Changed**:
- ✅ Prompts extracted from code to `config/prompts.yaml`
- ✅ Fixer loads prompts at initialization
- ✅ All prompts use template substitution
- ✅ Timeouts configurable per prompt type
- ✅ Language-specific overrides supported

**Benefits**:
- ✅ Clear separation of concerns (code vs domain knowledge)
- ✅ Easy iteration on prompt engineering
- ✅ Better maintainability and clarity
- ✅ Version control for prompts
- ✅ KISS: Simple YAML, no complex framework

**Result**: Clean, maintainable, config-driven architecture following SOLID principles.
