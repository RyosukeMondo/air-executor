# Running Autonomous Fixing on Real Projects

Complete guide for running multi-language autonomous fixing on your 5 real projects.

## Your Projects

| Project | Language | Path |
|---------|----------|------|
| **air-executor** | Python | `/home/rmondo/repos/air-executor` |
| **cc-task-manager** | JavaScript | `/home/rmondo/repos/cc-task-manager` |
| **mind-training** | JavaScript | `/home/rmondo/repos/mind-training` |
| **money-making-app** | Flutter | `/home/rmondo/repos/money-making-app` |
| **warps** | JavaScript | `/home/rmondo/repos/warps` |

## Quick Start

### Option 1: Test Run (Recommended First)

```bash
cd /home/rmondo/repos/air-executor
./scripts/run_real_projects.sh
```

This will:
1. ✅ Check all prerequisites (venv, Redis, Claude CLI)
2. ✅ Verify all 5 projects exist
3. ✅ Check git status (warn if uncommitted changes)
4. ✅ Run orchestrator once on all projects
5. ✅ Show results and next steps

### Option 2: PM2 Automation

```bash
cd /home/rmondo/repos/air-executor

# Start PM2 process
pm2 start ecosystem.real-projects.config.js

# Watch logs in realtime
pm2 logs real-projects-fixing

# Check status
pm2 status

# Stop
pm2 stop real-projects-fixing
```

## Prerequisites

### 1. Python Virtual Environment

```bash
# Should already exist from test suite
ls ~/.venv/air-executor/bin/python  # Verify

# If missing, create it:
python -m venv ~/.venv/air-executor
source ~/.venv/air-executor/bin/activate
pip install redis pyyaml pytest pylint mypy
```

### 2. Redis

```bash
# Check if running
redis-cli ping  # Should return PONG

# If not running:
redis-server &
```

### 3. Claude CLI

```bash
# Check authentication
claude login  # If not already logged in

# Or verify it's working
which claude
```

### 4. Language-Specific Tools

**For JavaScript projects** (cc-task-manager, mind-training, warps):
```bash
# Each project needs dependencies installed
cd /home/rmondo/repos/cc-task-manager && npm install
cd /home/rmondo/repos/mind-training && npm install
cd /home/rmondo/repos/warps && npm install
```

**For Flutter project** (money-making-app):
```bash
# Should already be set up if you ran autonomous fixing before
cd /home/rmondo/repos/money-making-app
flutter pub get
```

**For Python project** (air-executor):
```bash
# Should already have venv
cd /home/rmondo/repos/air-executor
source ~/.venv/air-executor/bin/activate
```

## Configuration

Configuration file: `config/real_projects_fix.yaml`

### Key Settings

```yaml
# More lenient thresholds for real projects
priorities:
  p1_static:
    success_threshold: 0.80  # 80% (vs 90% for tests)

  p2_tests:
    success_threshold: 0.70  # 70% (vs 85% for tests)

  p3_coverage:
    enabled: false  # Disabled initially

# Smaller batches for reviewable commits
issue_grouping:
  mega_batch_mode: false
  max_cleanup_batch_size: 30
  max_location_batch_size: 15

# Run 5 iterations before stopping
execution:
  max_iterations: 5
  max_duration_hours: 2
```

### Project-Specific Overrides

```yaml
project_overrides:
  # money-making-app: Lower thresholds (more issues)
  "/home/rmondo/repos/money-making-app":
    priorities:
      p1_static:
        success_threshold: 0.75
      p2_tests:
        success_threshold: 0.60

  # air-executor: Higher thresholds (cleaner)
  "/home/rmondo/repos/air-executor":
    priorities:
      p1_static:
        success_threshold: 0.85
      p2_tests:
        success_threshold: 0.80
```

## Expected Behavior

### First Run

**Priority 1: Static Analysis**
- Detects all 5 projects
- Runs static analysis in parallel
- Python: `pylint` + `mypy`
- JavaScript: `eslint` + `tsc`
- Flutter: `flutter analyze`
- **Time**: 2-5 minutes

**Priority 2: Strategic Tests**
- Adapts strategy based on P1 health
- Runs tests for each project
- **Time**: 10-60 minutes depending on health

**Results**:
- Stops at first gate that fails
- Shows which projects need attention
- Recommends next steps

### Subsequent Runs

Each iteration:
1. Re-checks health
2. Fixes 2 batches of P1 issues (if P1 gate failed)
3. Fixes 1 batch of P2 issues (if P2 gate failed)
4. Creates commits for fixes
5. Repeats until max_iterations (5) reached

## Monitoring Progress

### During Execution

```bash
# PM2 logs (if using PM2)
pm2 logs real-projects-fixing

# Or tail log file
tail -f logs/real-projects-out.log
```

### Check Git Commits

```bash
# air-executor (Python)
cd /home/rmondo/repos/air-executor
git log --oneline -5

# money-making-app (Flutter)
cd /home/rmondo/repos/money-making-app
git log --oneline -5

# cc-task-manager (JavaScript)
cd /home/rmondo/repos/cc-task-manager
git log --oneline -5

# etc...
```

### View Specific Changes

```bash
cd /home/rmondo/repos/air-executor

# See latest commit
git show HEAD

# See all changes
git diff HEAD~5 HEAD  # Last 5 commits

# See changes by file
git diff HEAD~5 HEAD --stat
```

## Safety Features

### Git-Based Safety

✅ **All changes are commits** - Easy to review and revert
✅ **No auto-push** - Manual push gives you control
✅ **Branch aware** - Works on current branch
✅ **Preserves history** - All commits are incremental

### Rollback if Needed

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo multiple commits
git reset --hard HEAD~5
```

### Recommended Workflow

1. **Test on one project first**:
   ```bash
   # Edit config to only enable one language
   languages:
     enabled:
       - python  # Just air-executor
   ```

2. **Review first commits**:
   ```bash
   cd /home/rmondo/repos/air-executor
   git log -p -1  # Review in detail
   ```

3. **If good, enable all**:
   ```yaml
   languages:
     enabled:
       - python
       - javascript
       - flutter
   ```

4. **Run full automation**:
   ```bash
   pm2 start ecosystem.real-projects.config.js
   ```

## Troubleshooting

### No commits created

**Cause**: Projects already healthy OR gates not passing

**Check**:
```bash
# Look for orchestrator output
cat logs/real-projects-out.log | grep "Score:"

# Example output:
# P1 Score: 85% ✅ Gate PASSED
# P2 Score: 65% ❌ (below 70% threshold)
```

**Solution**: Lower thresholds in config if needed

### Tests fail to run

**JavaScript projects**:
```bash
# Ensure dependencies installed
cd /home/rmondo/repos/cc-task-manager
npm install

# Verify tests work manually
npm test
```

**Python project**:
```bash
# Ensure pytest installed in venv
~/.venv/air-executor/bin/pip install pytest

# Verify tests work
cd /home/rmondo/repos/air-executor
pytest
```

### Redis connection errors

```bash
# Start Redis if not running
redis-server &

# Verify
redis-cli ping
```

### Claude wrapper fails

```bash
# Test wrapper manually
cd /home/rmondo/repos/air-executor
echo '{"action":"prompt","prompt":"Hello","options":{"cwd":"."}}' | \
  ~/.venv/air-executor/bin/python scripts/claude_wrapper.py

# Should return Claude's response
```

## PM2 Configuration

File: `ecosystem.real-projects.config.js`

```javascript
{
  name: 'real-projects-fixing',
  script: 'multi_language_orchestrator.py',
  args: 'config/real_projects_fix.yaml',
  interpreter: '~/.venv/air-executor/bin/python',

  // Run once then stop
  autorestart: false,
  max_restarts: 0,

  // Logs
  out_file: './logs/real-projects-out.log',
  error_file: './logs/real-projects-error.log'
}
```

### PM2 Commands

```bash
# Start
pm2 start ecosystem.real-projects.config.js

# View logs
pm2 logs real-projects-fixing

# Stop
pm2 stop real-projects-fixing

# Restart
pm2 restart real-projects-fixing

# Delete
pm2 delete real-projects-fixing

# Save PM2 state (survives reboots)
pm2 save
pm2 startup
```

## Performance Expectations

### Per Iteration

| Phase | Time | Projects |
|-------|------|----------|
| **P1 Static** | 2-5 min | All 5 in parallel |
| **P2 Tests** | 10-60 min | Depends on health |
| **Fixing** | 5-15 min | Per batch |
| **Total** | 20-80 min | Per iteration |

### Full Run (5 iterations)

**Best case** (healthy projects):
- 2-3 hours

**Worst case** (many issues):
- Stops after 2 hours (max_duration_hours)
- Can continue with another run

## Advanced Usage

### Adjust Thresholds

```bash
# Edit config
vim config/real_projects_fix.yaml

# Lower P1 threshold for projects with many issues
priorities:
  p1_static:
    success_threshold: 0.70  # Was 0.80
```

### Enable Coverage Phase

```bash
# Edit config after P1/P2 are clean
priorities:
  p3_coverage:
    enabled: true
```

### Run More Iterations

```bash
# Edit config
execution:
  max_iterations: 10  # Was 5
  max_duration_hours: 4  # Was 2
```

### Focus on One Project

```bash
# Temporarily move other projects
# Or edit config:
target_project: "/home/rmondo/repos/air-executor"  # Just one

# Disable other languages
languages:
  enabled:
    - python  # Only this one
```

## Next Steps After Fixing

### 1. Review All Commits

```bash
# Script to review all projects
for project in air-executor cc-task-manager mind-training money-making-app warps; do
  echo "=== $project ==="
  cd /home/rmondo/repos/$project
  git log --oneline -10
  echo ""
done
```

### 2. Test Manually

```bash
# Python
cd /home/rmondo/repos/air-executor
pytest

# JavaScript
cd /home/rmondo/repos/cc-task-manager
npm test

# Flutter
cd /home/rmondo/repos/money-making-app
flutter test
```

### 3. Push When Ready

```bash
# Push each project
cd /home/rmondo/repos/air-executor && git push
cd /home/rmondo/repos/cc-task-manager && git push
cd /home/rmondo/repos/mind-training && git push
cd /home/rmondo/repos/money-making-app && git push
cd /home/rmondo/repos/warps && git push
```

## Files Created

```
config/real_projects_fix.yaml           # Configuration
ecosystem.real-projects.config.js       # PM2 config
scripts/run_real_projects.sh            # Test runner
docs/REAL_PROJECTS_GUIDE.md            # This file
```

## See Also

- `docs/MULTI_LANGUAGE_USAGE.md` - General usage guide
- `docs/MULTI_LANGUAGE_ARCHITECTURE.md` - System architecture
- `tests/README.md` - Test suite documentation
- `scripts/README_AUTONOMOUS_FIXING.md` - Original autonomous fixing docs
