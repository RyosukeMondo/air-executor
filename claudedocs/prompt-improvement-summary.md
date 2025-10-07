# Prompt Improvement: Multi-Step Completion

## Problem Identified

**Original Approach:** One tiny step per iteration
- Iteration 1: Step 1 analysis (no commit)
- Iteration 2: Step 1 analysis again (Claude didn't track completion)
- Iteration 3: Step 1 analysis again...
- Result: Claude repeats Step 1 forever, never makes commits

## Root Cause

1. **Too Granular**: Each step is tiny (add interface method, implement method, etc.)
2. **Poor Progress Tracking**: Claude couldn't tell which steps were complete
3. **Analysis Paralysis**: Step 1 has no commit, so Claude loops on it

## Solution: Multi-Step Completion

**New Approach:** Complete as many steps as possible in one iteration
- Iteration 1: Steps 1-6 all done, 5 commits made
- Iteration 2: (if needed) Continue from where you stopped
- Result: Efficient progress with clear commit trail

## Changes Made

### Before (Too Granular)
```
**THIS ITERATION - Complete ONE step only:**
1. Identify which step to work on
2. Execute that one step
3. Commit OR report analysis
4. STOP
```

### After (Multi-Step)
```
**THIS ITERATION - Complete as many steps as possible:**
1. Check which steps are done (via git log grep)
2. Execute ALL remaining steps
3. Commit as you complete each step
4. Continue until ALL done OR blocker hit
```

## Key Improvements

1. **Clear Progress Detection**: `git log --grep="Part of X route DI migration"`
2. **Explicit Instructions**: "Work through ALL remaining steps (don't stop after one!)"
3. **Success Criteria**: "5 commits made (Steps 2-6)"
4. **Analysis Handling**: "Step 1: NO commit (analysis only), proceed to Step 2"

## Updated Configs

1. `warps-fix-plan-1-battle-session-service.json` - 8 steps, 6 commits expected
2. `warps-fix-plan-2-cards-registered-route.json` - 6 steps, 5 commits expected
3. `warps-fix-plan-3-gacha-history-route.json` - 5 steps, 4 commits expected

## Expected Behavior

```
================================================================================
🔁 ITERATION 1/10
================================================================================
Claude: "Checking progress... No commits found. Starting from Step 2."
Claude: "Completing Step 2..." [adds interface method]
Claude: "Committing: feat(repository): Add findRegisteredByUserId to ICardRepository"
Claude: "Completing Step 3..." [implements in repos]
Claude: "Committing: feat(repository): Implement findRegisteredByUserId in repositories"
...
Claude: "ALL STEPS COMPLETE. 5 commits made."
✅ Success: True
📝 Progress check: New commit detected: xyz789ab (was 460ff90b)
```

## Testing

Run with improvements:
```bash
/home/rmondo/sequential_warps.sh
```

Expected: Each fix plan completes in 1-2 iterations instead of getting stuck.
