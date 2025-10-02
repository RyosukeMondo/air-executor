# Systematic Fix Plan (Keep Session Context)

This plan is for fixing all project issues systematically when maintaining session context between fixes.

## 🔧 Systematic Fix Prompt (Copy-Paste Ready)

```
You are tasked with systematically fixing all issues in this Flutter project in atomic, meaningful commits.

## Context
- Project: Gravity Sort mobile game built with parallel spec-driven development
- Current state: 90.4% tasks complete, but with inconsistencies and missing implementations
- Goal: Fix all issues one logical group at a time, commit, and push

## Your Workflow (Execute Once Per Run)

### Phase 1: Discovery (First Run Only)
1. Read steering documents to understand the complete feature set:
   - Read @.spec-workflow/STEERING.md or equivalent project docs
   - Read @.spec-workflow/PARALLEL_SPECS_PLAN.md
   - Read @README.md

2. Create a master fix list by detecting:
   - **Missing implementations**: Code called but not defined (like initializeAsyncDependencies)
   - **Missing files**: Imports that don't exist (like environments.dart)
   - **Tasks marked complete but code missing**: Compare tasks.md vs actual files
   - **Runtime errors**: Check main.dart, providers, DI resolution
   - **Test failures**: Run `find test -name "*_test.dart" | head -5` and check if tests pass
   - **Compilation errors**: Check for syntax/import errors
   - **Incomplete features**: Features in steering docs but not in code

3. Categorize fixes into logical groups:
   - Group 1: Missing core files (environments.dart, init functions)
   - Group 2: Missing implementations (functions, classes)
   - Group 3: Task status corrections (update tasks.md to reflect reality)
   - Group 4: DI/Provider wiring issues
   - Group 5: Test failures
   - Group 6: Missing features from steering docs
   - Group 7: Runtime error fixes

4. Create execution plan as a numbered list with estimates

### Phase 2: Execute ONE Fix Group (Every Run)
1. Pick the NEXT unfinished group from your plan
2. Implement ALL fixes in that group
3. Verify the fixes work (run tests if applicable)
4. Update any related tasks.md files to mark tasks complete
5. Create ONE atomic commit with descriptive message
6. Push to remote
7. Report what was fixed and what's next

## Output Format

**Discovery Phase Output:**
```
## 🔍 Issues Found

### Group 1: Missing Core Files (Priority: CRITICAL)
- [ ] lib/core/injection/environments.dart - imported but doesn't exist
- [ ] initializeAsyncDependencies() - called but not defined
**Estimated time**: 10 minutes

### Group 2: Task Status Fixes (Priority: HIGH)
- [ ] dependency-injection-setup tasks.md - marked incomplete but code exists
- [ ] Update 3 other specs with incorrect status
**Estimated time**: 5 minutes

### Group 3: Missing Implementations (Priority: MEDIUM)
- [ ] Feature X from steering docs not implemented
**Estimated time**: 30 minutes

**Total Groups**: 7
**Estimated Total Time**: 2 hours
```

**Execution Phase Output:**
```
## ✅ Group 1 Complete: Missing Core Files

### Changes Made:
1. Created lib/core/injection/environments.dart with prodEnv/devEnv/testEnv
2. Added initializeAsyncDependencies() to injection.dart
3. Verified main.dart compiles without errors

### Commit:
```
feat: add missing DI core files

- Add environments.dart with environment constants
- Add initializeAsyncDependencies() for Firebase/Hive/AdMob init
- Fix compilation errors in main.dart

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Pushed: ✅ origin/main

### Next: Group 2 - Task Status Fixes
```

## Rules
1. **ONE group per run** - Don't try to fix everything at once
2. **Atomic commits** - Each commit should be self-contained and meaningful
3. **Always push** - Push after every successful commit
4. **Update tasks.md** - Mark tasks complete when fixing them
5. **Verify before commit** - Make sure the fix actually works
6. **No half-fixes** - Complete the entire group before committing

## First Run Instructions
On the FIRST run, execute Phase 1 (Discovery) and show me the full plan.
On SUBSEQUENT runs, execute Phase 2 (implement next group), commit, push, and tell me what's next.

## Ready?
START WITH PHASE 1 NOW.
```

## How to Use

1. **Copy the entire prompt above** (from "You are tasked..." to "START WITH PHASE 1 NOW")
2. **Paste into Claude Code** and press Enter
3. **Wait a few minutes** - Claude will discover all issues and create a plan
4. **Review the plan** - See what needs fixing
5. **Run again with same prompt** - Claude will execute Group 1, commit, push
6. **Repeat** - Keep pasting the same prompt until all groups are done

Each run should take 2-10 minutes and produce one clean commit pushed to remote.

## Expected Timeline

- **Discovery**: 5 minutes (first run only)
- **Per group**: 5-15 minutes
- **Total groups**: 5-10 typically
- **Total time**: 1-3 hours across multiple runs

## Benefits

- ✅ Maintains context across groups
- ✅ Can optimize based on previous fixes
- ✅ Clear progression through logical groups
- ✅ Each commit is meaningful and atomic
- ✅ Always know what's next

## When to Use

Use this approach when:
- You have a stable session (not refreshing browser)
- You want to see the full picture before starting
- You prefer planned, sequential execution
- You can supervise multiple runs in one sitting
