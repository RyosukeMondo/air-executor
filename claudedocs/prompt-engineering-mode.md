# Prompt Engineering Mode - Documentation

## Overview

Systematic prompt testing and refinement tool for autonomous fixing system.

**Purpose**: Test multiple prompt variations on the same project, compare results, and identify the best approach.

## Features

✅ **Systematic Testing**
- Run multiple prompt variants on same codebase
- Reset to clean state between experiments
- Capture full results for each variant

✅ **Comprehensive Logging**
- Structured JSON logs per experiment
- Claude response captured
- Git changes tracked (commit SHA, diff stats)
- Timing and metrics recorded

✅ **Comparison Analysis**
- Side-by-side comparison of variants
- Winner determination based on criteria
- Metrics comparison (duration, changes, success rate)

✅ **Reproducibility**
- Git baseline reset before each experiment
- Same starting state guaranteed
- Full experiment config saved

## Usage

### Basic Command

```bash
python airflow_dags/autonomous_fixing/prompt_engineer.py config/experiments/test-creation-flutter.yaml
```

### Experiment Config Structure

```yaml
name: "Experiment Name"
description: "What you're testing"

# Base config for wrapper settings
base_config: "config/projects/money-making-app.yaml"

# Project to test on
project:
  path: "/home/rmondo/repos/money-making-app"
  language: "flutter"

# Git baseline (reset to this before each experiment)
baseline:
  git_ref: "HEAD"  # or specific commit SHA

# How to compare results
comparison:
  criteria: "success_and_speed"  # Options: success_and_speed, most_comprehensive, least_changes

# Prompt variants to test
prompts:
  - name: "variant_1"
    description: "First approach"
    timeout: 600
    text: |
      Your prompt text here...
      Can be multi-line

  - name: "variant_2"
    description: "Second approach"
    timeout: 600
    file: "config/prompts/variant-2.txt"  # Or load from file

  - name: "variant_3_with_vars"
    description: "With template variables"
    timeout: 600
    text: |
      Fix {language} errors in {project_name}
    variables:
      language: "Flutter"
      project_name: "money-making-app"
```

## Workflow

### 1. Create Experiment Config

```bash
# Create new experiment
cat > config/experiments/my-test.yaml << 'EOF'
name: "Testing Fix Approaches"
project:
  path: "/home/rmondo/repos/my-project"
baseline:
  git_ref: "HEAD"
prompts:
  - name: "approach_a"
    text: "Fix all linter errors"
  - name: "approach_b"
    text: "Fix errors one by one, starting with highest priority"
EOF
```

### 2. Run Experiment

```bash
python airflow_dags/autonomous_fixing/prompt_engineer.py config/experiments/my-test.yaml
```

### 3. Review Results

**Console Output:**
```
🧪 PROMPT ENGINEERING MODE
================================================================================
Session: 20251003_151530
Suite: Testing Fix Approaches
================================================================================

📂 Project: /home/rmondo/repos/my-project
🔖 Baseline: HEAD
🎯 Prompts to test: 2

💾 Baseline commit: abc12345

================================================================================
🧪 Experiment 1/2: approach_a
================================================================================

📝 Prompt: Fix all linter errors
🔤 Prompt length: 25 chars
🔄 Resetting to baseline...
   ✓ Reset complete

... Claude execution ...

✅ Experiment complete
   Duration: 45.3s
   Commit: def67890

💾 Saved: logs/prompt-experiments/20251003_151530_approach_a.json

================================================================================
📊 COMPARING RESULTS
================================================================================

📊 Baseline: approach_a
🔬 Variants: approach_b

📈 RESULTS SUMMARY

Prompt                         Success    Duration      Files    Lines
------------------------------ ---------- ------------ -------- --------
approach_a                     ✅              45.3s       12      234
approach_b                     ✅              38.7s        8      156

🏆 Winner: approach_b
   Reason: Fastest successful experiment (38.7s)

📊 Detailed comparison:

   approach_b vs baseline:
      Duration: -6.6s (85.4%)
      Files: -4
      Lines: -78
```

**Saved Files:**

```
logs/prompt-experiments/
├── 20251003_151530_approach_a.json      # Individual experiment
├── 20251003_151530_approach_b.json      # Individual experiment
└── suite_20251003_151530.json           # Suite summary
```

### 4. Analyze Logs

**Individual Experiment Log:**

```json
{
  "experiment_id": "20251003_151530_approach_a",
  "prompt_name": "approach_a",
  "prompt_text": "Fix all linter errors",
  "project_path": "/home/rmondo/repos/my-project",
  "timestamp": "2025-10-03T15:15:30.123456",
  "duration": 45.3,
  "success": true,

  "claude_response": {
    "success": true,
    "output": "...",
    "error": null
  },

  "git_commit_sha": "def67890abcdef1234567890",
  "git_diff_stats": {
    "files_changed": 12,
    "insertions": 180,
    "deletions": 54,
    "diff_output": "..."
  },

  "metrics": {
    "claude_success": true,
    "has_git_changes": true,
    "files_changed": 12,
    "lines_changed": 234
  }
}
```

**Suite Summary:**

```json
{
  "session_id": "20251003_151530",
  "suite_name": "Testing Fix Approaches",
  "project": "/home/rmondo/repos/my-project",
  "baseline_commit": "abc12345",
  "experiments_run": 2,
  "experiments": [...],
  "comparison": {
    "baseline_id": "20251003_151530_approach_a",
    "variants": ["20251003_151530_approach_b"],
    "winner": "approach_b",
    "winner_reason": "Fastest successful experiment (38.7s)",
    "metrics_comparison": {...}
  }
}
```

## Use Cases

### 1. Solving the "0/0 Tests" Bug

**Problem**: Tests are created but not detected in next iteration

**Experiment**: Test different test creation prompts

```yaml
name: "Flutter Test Creation Debug"
project:
  path: "/home/rmondo/repos/money-making-app"

prompts:
  - name: "current_prompt"
    file: "config/prompts/test-creation-baseline.txt"

  - name: "explicit_location"
    text: |
      Create tests in test/ directory.
      CRITICAL: Tests MUST be in test/ to be discovered.
      After creating, run: flutter test
      Show the output to prove tests are found.

  - name: "discovery_first"
    text: |
      Step 1: Check if tests exist (ls test/)
      Step 2: Run flutter test --dry-run
      Step 3: If 0 tests found, diagnose why
      Step 4: Create tests that WILL be discovered
      Step 5: Verify with flutter test
```

**Analysis**: Compare which prompt results in tests that are actually discovered

### 2. Optimizing Fix Prompts

**Problem**: Want faster, more focused fixes

**Experiment**: Test different fix strategies

```yaml
name: "Error Fix Optimization"

prompts:
  - name: "fix_all"
    text: "Fix all errors found by flutter analyze"

  - name: "fix_one"
    text: "Fix ONLY the first error from flutter analyze"

  - name: "fix_by_priority"
    text: "Analyze errors, pick highest priority, fix that one"
```

### 3. Prompt Clarity Testing

**Problem**: Unclear if prompt is giving right instructions

**Experiment**: Test more explicit vs concise prompts

```yaml
name: "Prompt Clarity"

prompts:
  - name: "concise"
    text: "Create Flutter tests"

  - name: "detailed"
    text: |
      Create Flutter tests with these requirements:
      1. Use flutter_test package
      2. Place in test/ directory
      3. Name files *_test.dart
      4. Create at least 5 test files
      5. Run flutter test to verify
      6. Commit changes
```

## Advanced Features

### Template Variables

Use `{variable_name}` in prompts:

```yaml
prompts:
  - name: "templated"
    text: "Fix {language} errors in {project_name} using {tool}"
    variables:
      language: "Flutter"
      project_name: "my-app"
      tool: "flutter analyze"
```

### Custom Comparison Criteria

```yaml
comparison:
  criteria: "custom"
  custom_logic:
    prefer: "fewer_changes"  # Prefer solutions that change less
    require: "all_tests_pass"
```

### Iterative Refinement

```bash
# Round 1: Test 5 variants
python prompt_engineer.py config/experiments/round1.yaml

# Analyze results, pick top 2
# Round 2: Test refined versions of top 2
python prompt_engineer.py config/experiments/round2.yaml

# Round 3: Test winner with edge cases
python prompt_engineer.py config/experiments/round3.yaml
```

## Best Practices

### 1. Start Simple

```yaml
# First experiment: Just 2 variants
prompts:
  - name: "current"
    file: "config/prompts/current.txt"
  - name: "improved"
    text: "My improved version..."
```

### 2. One Variable at a Time

Don't change multiple things in one experiment:

❌ **Bad**: Test "more explicit + different order + different tool"
✅ **Good**: Test "more explicit" vs "current", then test different order separately

### 3. Use Descriptive Names

```yaml
prompts:
  - name: "baseline_v1"  # ❌ Unclear
  - name: "explicit_test_location"  # ✅ Clear what's different
```

### 4. Document Hypotheses

```yaml
prompts:
  - name: "hypothesis_tests_not_found_due_to_location"
    description: "Testing if explicit test/ directory fixes discovery"
    text: |
      Create tests in test/ directory (NOT integration_test/ or test_driver/).
      ...
```

### 5. Save Successful Prompts

When you find a winner:

```bash
# Save to prompts.yaml
cp logs/prompt-experiments/20251003_151530_winner.json \
   config/prompts/test-creation-improved.txt

# Update prompts.yaml to use it
```

## Integration with Main System

### Update prompts.yaml After Finding Winner

```yaml
# config/prompts.yaml

tests:
  create_tests:
    # Updated 2025-10-03: Experiment 20251003_151530 winner
    # Improved test discovery by explicit location specification
    template: |
      This {language} project has NO TESTS. Create initial test suite.

      CRITICAL: Tests MUST be in test/ directory to be discovered.
      After creating tests, run: flutter test
      Verify output shows test count > 0
      ...
```

### A/B Testing in Production

```python
# In fixer.py, optionally use experiment mode
if self.config.get('experiment_mode'):
    prompt_variant = self.config.get('prompt_variant', 'baseline')
    prompt_text = self._get_experiment_prompt(prompt_variant)
else:
    prompt_text = self.prompts['tests']['create_tests']['template']
```

## Troubleshooting

### Experiment Hangs

```yaml
# Add shorter timeout for testing
prompts:
  - name: "test"
    timeout: 60  # Start with 1 minute for quick tests
```

### Git Reset Fails

```bash
# Manually reset project
cd /path/to/project
git reset --hard HEAD
git clean -fd
```

### Can't Compare Results

```python
# Use jq to analyze logs
jq '.metrics' logs/prompt-experiments/suite_*.json

# Compare durations
jq -r '.experiments[] | "\(.prompt_name): \(.duration)s"' logs/prompt-experiments/suite_*.json
```

## Example Experiments Included

1. **test-creation-flutter.yaml**: 5 variants for Flutter test creation
2. **quick-test.yaml**: Simple 2-variant test for rapid iteration

Run them:

```bash
# Full test suite (5 variants)
python airflow_dags/autonomous_fixing/prompt_engineer.py \
  config/experiments/test-creation-flutter.yaml

# Quick test (2 variants)
python airflow_dags/autonomous_fixing/prompt_engineer.py \
  config/experiments/quick-test.yaml
```

## Next Steps

After finding better prompts:

1. **Update config/prompts.yaml** with winning variants
2. **Document** what changed and why in git commit
3. **Test** in autonomous fixing mode
4. **Iterate** if needed with new experiment

---

**Key Insight**: Prompt engineering mode lets you **systematically improve** prompts instead of guessing. Each experiment gives you **data-driven insights** about what works.
