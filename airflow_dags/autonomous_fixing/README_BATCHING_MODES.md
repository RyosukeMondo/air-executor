# Batching Modes for Human-Friendly Commits

Three batching strategies for autonomous fixing, designed for human-reviewable git commits.

## Overview

The system supports three modes for grouping issues into fixable batches:

1. **Mega Batch Mode** - ONE comprehensive fix per phase
2. **Smart Batch Mode** (default) - Human-like logical grouping
3. **Individual Mode** - One issue at a time

## Mode Comparison

| Mode | Issues → Tasks | Claude Sessions | Commits | Use Case |
|------|---------------|-----------------|---------|----------|
| **Mega Batch** | 100 → 1 | 1 comprehensive | 1 big commit | Fast cleanup, aggressive |
| **Smart Batch** | 100 → 5-10 | 5-10 focused | 5-10 clear commits | Reviewable, balanced |
| **Individual** | 100 → 100 | 100 small | 100 tiny commits | Conservative, noisy |

## 1. Mega Batch Mode (Fast & Comprehensive)

**Configuration:**
```yaml
issue_grouping:
  mega_batch_mode: true

batch_sizes:
  build_fixes: 1  # ONE mega-task per phase
  test_fixes: 1
  lint_fixes: 1
```

**Behavior:**
- Takes ALL issues in a phase (e.g., all 100 build errors)
- Creates ONE comprehensive batch task
- ONE Claude session fixes everything
- ONE commit: `fix: comprehensive cleanup of 100 issues`

**Example:**
```
🔍 Discovering build issues... Found 100 errors

📦 Mega Batch Mode:
   Input tasks: 100
   Output: 1 comprehensive mega-batch

🔨 Executing 1 task...
  [1/1] fix_mega_batch...

✅ Fixed 1/1 tasks

Commit: fix: comprehensive cleanup of 100 issues
```

**Pros:**
- Fast: ONE Claude session instead of many
- Efficient: Claude sees full context
- Fewer API calls

**Cons:**
- Large commit (harder to review)
- All-or-nothing (if it fails, everything fails)
- Less granular progress tracking

## 2. Smart Batch Mode (Human-Friendly, Default)

**Configuration:**
```yaml
issue_grouping:
  mega_batch_mode: false
  max_cleanup_batch_size: 50
  max_location_batch_size: 20

batch_sizes:
  build_fixes: 3  # Process 3 batches per run
  test_fixes: 2
  lint_fixes: 2
```

**Behavior:**
- Groups issues by type and location
- **Cleanup batches**: "Remove all unused imports" (project-wide, one type)
- **Location batches**: "Fix type errors in home/" (one screen/module)
- Multiple focused Claude sessions
- Multiple clear commits with separation of concerns

**Example:**
```
🔍 Discovering build issues... Found 100 errors

  🧹 Cleanup batch: 30 unused_imports
  📍 Location-based batching: 40 type_mismatches

📦 Grouping results:
   Input tasks: 100
   Output tasks: 7
   Batch tasks: 5
   Individual tasks: 2

Executing 3 batches:
  [1/3] fix_cleanup_unused_imports (30 issues, 25 files)
  [2/3] fix_location_type_mismatches in home/ (15 issues, 8 files)
  [3/3] fix_location_type_mismatches in auth/ (12 issues, 6 files)

Commits:
- chore: remove all unused_imports
- fix: type_mismatches in home/
- fix: type_mismatches in auth/
```

**Pros:**
- Clear separation of concerns (cleanup vs bug fix)
- Reviewable commit sizes (10-30 files)
- Logical grouping (by module/screen)
- Faster than individual mode
- Resilient (one batch failure doesn't stop others)

**Cons:**
- More Claude sessions than mega mode
- Still multiple commits (but logical)

## 3. Individual Mode (Conservative)

**Configuration:**
```yaml
issue_grouping:
  mega_batch_mode: false
  max_cleanup_batch_size: 1  # Effectively disables batching
  max_location_batch_size: 1

batch_sizes:
  build_fixes: 5  # 5 individual fixes per run
```

**Behavior:**
- Each issue is a separate task
- Each task = one Claude session
- Each fix = one commit

**Example:**
```
Executing 5 individual fixes:
  [1/5] fix_build_error: Unused import in lib/main.dart
  [2/5] fix_build_error: Unused import in lib/home.dart
  ...

Commits:
- fix: Unused import in lib/main.dart
- fix: Unused import in lib/home.dart
- fix: Unused import in lib/auth.dart
- fix: Type error in lib/widgets/button.dart
- fix: Null safety in lib/services/api.dart
```

**Pros:**
- Very fine-grained control
- Easy to revert individual commits
- Clear what each commit does

**Cons:**
- Very slow (100 issues = 100 Claude sessions)
- Noisy commit history
- No pattern recognition across similar issues

## Recommended Settings by Scenario

### Aggressive Cleanup (Get it done fast)
```yaml
issue_grouping:
  mega_batch_mode: true

batch_sizes:
  build_fixes: 1
  test_fixes: 1
  lint_fixes: 1
```

**Use when:** Initial cleanup, tech debt sprint, not worried about commit review

### Production/Review (Balanced, default)
```yaml
issue_grouping:
  mega_batch_mode: false
  max_cleanup_batch_size: 50
  max_location_batch_size: 20

batch_sizes:
  build_fixes: 3
  test_fixes: 2
  lint_fixes: 2
```

**Use when:** Normal development, commits will be reviewed, want logical grouping

### Conservative/Learning (Careful)
```yaml
issue_grouping:
  mega_batch_mode: false
  max_cleanup_batch_size: 1  # No batching

batch_sizes:
  build_fixes: 5
  test_fixes: 3
  lint_fixes: 5
```

**Use when:** Testing the system, need fine-grained control, critical codebase

## Batching Strategy Details

### Cleanup Batches (Human: "I'll clean up all X today")
```
Examples:
- chore: remove all unused imports (30 files)
- style: format all code (50 files)
- chore: add missing const keywords (40 files)
```

**Criteria:**
- Same issue type (unused imports, formatting, etc.)
- Project-wide scope
- No functional changes
- Clear, atomic commit

### Location Batches (Human: "I'll fix the home screen")
```
Examples:
- fix: type errors in home/ (15 issues, 8 files)
- fix: null safety in auth/ (12 issues, 6 files)
- fix: missing overrides in widgets/ (8 issues, 5 files)
```

**Criteria:**
- Same directory/module
- Related functionality
- Logical unit (one screen, one feature)
- Reviewable scope (typically 5-20 files)

### Mega Batch (Human: "Fix everything")
```
Example:
- fix: comprehensive cleanup of 100 issues

Categories fixed:
  - Unused Imports (30)
  - Type Errors (40)
  - Null Safety (20)
  - Other (10)
```

**Criteria:**
- All issues in phase
- One comprehensive session
- Fast, aggressive cleanup

## Performance Comparison

**100 build errors to fix:**

| Mode | Claude Sessions | Wall Time | Commits |
|------|----------------|-----------|---------|
| Mega Batch | 1 | ~15 min | 1 |
| Smart Batch | 5-7 | ~60 min | 5-7 |
| Individual | 100 | ~150 min | 100 |

## See Also

- `issue_grouping.py` - Grouping implementation
- `executor_runner.py` - Prompt generation
- `fix_orchestrator.py` - Orchestration
- `config/autonomous_fix.yaml` - Configuration
