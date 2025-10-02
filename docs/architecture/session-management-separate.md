# Self-Contained Fix Plan (Separate Sessions)

This plan is for fixing project issues when context resets between sessions (browser refresh, new chat, etc).

## 🔧 Self-Contained Fix Prompt (Copy-Paste for Each Session)

```
You are tasked with fixing ONE critical issue in this Flutter project per session.
Context resets between runs, so you must be fully autonomous.

## Your Workflow (Every Single Run)

### Step 1: Quick Analysis (2 minutes)
Scan the project to find ALL categories of issues:

1. **Compilation Blockers** (CRITICAL - breaks build)
   - Missing files that are imported
   - Undefined functions/classes that are called
   - Syntax errors
   Command: Check imports in main.dart and key files

2. **Runtime Blockers** (CRITICAL - app crashes)
   - DI resolution failures
   - Missing provider implementations
   - Null reference errors
   Command: Read main.dart, check DI setup

3. **Incomplete Features** (HIGH - promised but missing)
   - Steering document features not implemented
   - Specs marked complete but code missing
   Command: Compare .spec-workflow/PARALLEL_SPECS_PLAN.md with actual code

4. **Task Status Lies** (MEDIUM - tracking issues)
   - tasks.md says complete but code doesn't exist
   - tasks.md says incomplete but code exists
   Command: Sample check 3-5 specs

5. **Test Failures** (LOW - quality issues)
   - Unit tests failing
   - Integration tests broken
   Command: Check test/ directory

6. **Technical Debt** (LOW - polish)
   - Missing docs
   - Code smells
   - Performance issues

### Step 2: Priority Selection
Pick the SINGLE HIGHEST PRIORITY issue using this order:
1. Compilation Blockers → fix immediately
2. Runtime Blockers → fix immediately
3. Incomplete Features → pick one critical feature
4. Task Status Lies → batch update multiple tasks.md files
5. Test Failures → fix one test suite
6. Technical Debt → skip for now

### Step 3: Implement Fix
1. Fix the chosen issue completely
2. Verify it works (compile/run/test as needed)
3. Update related tasks.md if applicable
4. Commit with descriptive message
5. Push to remote

### Step 4: Report
Output this format:
```
## 🎯 Session Complete

### Issues Found (Priority Order):
1. [CRITICAL] Missing environments.dart breaks compilation
2. [CRITICAL] initializeAsyncDependencies() undefined
3. [HIGH] Admob rewarded ads incomplete (7 tasks)
4. [MEDIUM] 3 specs have incorrect task status
5. [LOW] 12 tests failing

### Fixed This Session:
**Priority**: CRITICAL
**Issue**: Missing environments.dart breaks compilation
**Solution**: Created lib/core/injection/environments.dart with environment constants

### Commit:
```
fix: add missing environments.dart for DI configuration

- Create environments.dart with prodEnv/devEnv/testEnv constants
- Fixes import error in main.dart
- Required for environment-based dependency injection

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Pushed: ✅ commit abc1234 to origin/main

### Next Session Should Fix:
**Priority**: CRITICAL
**Issue**: initializeAsyncDependencies() undefined
**Location**: Called in main.dart but not defined anywhere
**Estimated time**: 10 minutes
```

## Critical Rules
1. **Analyze FIRST** - Always scan for all issue categories before choosing
2. **Pick ONE** - Fix only the single highest priority issue
3. **Complete it** - Don't leave half-fixes
4. **Always commit & push** - Every session must produce one commit
5. **Tell me what's next** - So I know what to expect next run

## Optimization
- If you find multiple CRITICAL issues, fix the fastest one first
- If fixing one issue, and you notice a 30-second fix for another CRITICAL issue, do both in one commit
- Batch similar fixes (e.g., updating 5 tasks.md files is one commit)

## Anti-Patterns to Avoid
❌ Don't try to fix everything at once
❌ Don't skip analysis phase
❌ Don't commit without pushing
❌ Don't fix LOW priority before CRITICAL
❌ Don't leave compilation errors

## START NOW
Execute Step 1 (Analysis), Step 2 (Pick Priority), Step 3 (Fix), Step 4 (Report)
```

## How to Use

1. **Copy the entire prompt** (from "You are tasked..." to "Execute Step 1...")
2. **Paste into NEW Claude Code session**
3. **Wait 3-5 minutes** - Claude analyzes, picks highest priority, fixes, commits, pushes
4. **Read the "Next Session Should Fix"** section
5. **Start NEW session** (context reset)
6. **Paste the SAME prompt again**
7. **Repeat** until "No critical issues found"

## Expected Results Per Session

- **Time per session**: 3-10 minutes
- **Output**: 1 commit, pushed to remote
- **Progress**: One issue completely resolved
- **Clarity**: You'll know exactly what's next

## Example Session Flow

**Session 1**: Finds 5 issues → Fixes missing environments.dart → Commits → Pushes → Says "Next: fix initializeAsyncDependencies"

**Session 2** (new context): Finds 4 issues → Fixes initializeAsyncDependencies → Commits → Pushes → Says "Next: complete admob-rewarded-ads"

**Session 3** (new context): Finds 3 issues → Completes admob-rewarded-ads → Commits → Pushes → Says "Next: fix task status for 3 specs"

Continue until: "✅ No critical or high priority issues found. Project is healthy!"

## Benefits

- ✅ Works with context resets (browser refresh, new sessions)
- ✅ Each session is independent and complete
- ✅ Always makes progress regardless of context loss
- ✅ Clear priority system prevents wasted effort
- ✅ Git history shows incremental improvements

## When to Use

Use this approach when:
- Browser/editor might refresh between runs
- Working across multiple days/sessions
- Want maximum fault tolerance
- Prefer autonomous execution without supervision
- Need to step away and come back later

## Progress Tracking

Since context resets, track progress via:
- Git commit history (`git log --oneline -10`)
- "Next Session Should Fix" message from previous run
- Project health improves with each session

## Completion Indicator

You'll know you're done when a session reports:
```
## 🎯 Session Complete

### Issues Found (Priority Order):
(none at CRITICAL or HIGH priority)

### Fixed This Session:
Nothing - project is healthy!

### Next Session Should Fix:
No critical issues remaining. Consider:
- Running full test suite
- Performance optimization
- Documentation improvements
```
