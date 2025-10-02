# Batch Fixing System

Intelligent grouping of similar issues for efficient batch processing.

## Overview

The autonomous fixing system now automatically groups conceptually similar issues and fixes them together in batches, resulting in:
- More substantial commits (not just single-line fixes)
- Efficient handling of repetitive issues (e.g., unused imports across multiple files)
- Comprehensive fixes that address root causes across multiple files

## How It Works

### 1. Issue Discovery
Issues are discovered per phase (build/test/lint) as before.

### 2. Issue Grouping
Similar issues are automatically grouped into batches based on patterns:

**Trivial Issues** (always batched):
- `unused_imports` - Unused import statements
- `formatting` - Code formatting issues

**Substantial Issues** (batched if ≥3 exist):
- `type_mismatches` - Type assignment errors
- `null_safety` - Null safety violations
- `missing_overrides` - Missing method overrides

**Other Issues**:
- Keep as individual tasks if no pattern match or insufficient quantity

### 3. Batch Task Creation
When batching occurs:
- Up to 10 related issues grouped per batch task
- Batch includes all affected files
- Context summary shows all issues to fix

### 4. Execution
- Individual tasks get focused prompts (1 file, 1 issue)
- Batch tasks get comprehensive prompts (multiple files, related issues)
- Batch prompts encourage root cause analysis and consistent fixes

## Configuration

```yaml
# config/autonomous_fix.yaml

issue_grouping:
  min_batch_size: 3    # Minimum issues to create a batch
  max_batch_size: 10   # Maximum issues per batch task
  enabled: true

batch_sizes:
  build_fixes: 3  # Can now include batch tasks
  test_fixes: 2
  lint_fixes: 2
```

## Example Output

### Before (Individual Fixes):
```
🔍 Discovering build issues...
  Found 15 build errors

📝 Queueing 1 task
  - fix_build_error: Unused import in lib/main.dart

🔨 Executing...
✅ Fixed 1/1 tasks
```
**Commit**: `fix: Unused import in lib/main.dart`

### After (Batch Fixes):
```
🔍 Discovering build issues...
  Found 15 build errors

📦 Grouping results:
   Input tasks: 15
   Output tasks: 4
   Batch tasks: 2
   Individual tasks: 2

📝 Queueing 3 tasks
  - fix_batch_unused_imports: 10 unused_imports across 8 files
  - fix_batch_type_mismatches: 5 type_mismatches across 3 files
  - fix_build_error: Undefined name 'foo'

🔨 Executing...
✅ Fixed 3/3 tasks
```
**Commits**:
- `fix: unused_imports across 8 files`
- `fix: type_mismatches across 3 files`
- `fix: Undefined name 'foo'`

## Batch Prompt Example

```
Fix batch of 10 related unused_imports issues in Flutter project.

**Batch Type**: unused_imports
**Files Affected** (8 total):
  - lib/main.dart
  - lib/screens/home.dart
  - lib/widgets/button.dart
  ...

**Issues to Fix**:
1. lib/main.dart:5 - Unused import: 'package:flutter/material.dart'
2. lib/screens/home.dart:3 - Unused import: 'dart:async'
3. lib/widgets/button.dart:2 - Unused import: 'package:flutter/widgets.dart'
...

**Instructions**:
1. Analyze the pattern across all these issues
2. Fix ALL related issues comprehensively (you can modify multiple files)
3. Apply consistent solution across all affected files
4. Consider root cause - if these issues share a common cause, fix that
5. Run `flutter analyze --no-pub` to verify all fixes
6. Stage and commit your changes with:
   git add -A
   git commit -m "fix: unused_imports across 8 files"

This is a BATCH fix - handle multiple files together for efficiency.
```

## Benefits

1. **Efficiency**: Fix 10 related issues in one task instead of 10 separate tasks
2. **Consistency**: Apply same pattern across all affected files
3. **Better Commits**: Meaningful commit messages describing scope of changes
4. **Root Cause Focus**: Encourages addressing underlying issues, not just symptoms
5. **Time Savings**: Fewer context switches, faster overall completion

## Customization

### Add New Batch Patterns

Edit `issue_grouping.py`:

```python
BATCH_PATTERNS = {
    'your_pattern_name': [
        r"regex pattern 1",
        r"regex pattern 2",
    ],
    # ...
}

# Decide if trivial or substantial
TRIVIAL_PATTERNS = ['unused_imports', 'formatting', 'your_pattern_name']
# or
SUBSTANTIAL_PATTERNS = ['type_mismatches', 'null_safety', 'your_pattern_name']
```

### Adjust Batch Sizes

```yaml
issue_grouping:
  min_batch_size: 5    # Require more issues before batching
  max_batch_size: 20   # Allow larger batches
```

### Disable Batching

```yaml
issue_grouping:
  enabled: false
```

Or set `min_batch_size` very high:

```yaml
issue_grouping:
  min_batch_size: 999  # Effectively disables batching
```

## Monitoring

Watch for batch tasks in orchestrator output:

```
📦 Grouping results:
   Input tasks: 50
   Output tasks: 12
   Batch tasks: 5      ← Number of batches created
   Individual tasks: 7  ← Remaining individual tasks
```

Check batch task types:
- `fix_batch_unused_imports`
- `fix_batch_type_mismatches`
- `fix_batch_null_safety`
- etc.

## See Also

- `issue_grouping.py` - Grouping logic
- `executor_runner.py` - Batch prompt generation
- `fix_orchestrator.py` - Integration
- `config/autonomous_fix.yaml` - Configuration
