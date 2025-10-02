# Quick Start: Real Projects Autonomous Fixing

## ✅ Setup Complete!

Your 5 real projects are configured for multi-language autonomous fixing:

| Project | Language | Status |
|---------|----------|--------|
| **air-executor** | Python | ✅ Ready |
| **cc-task-manager** | JavaScript | ⚠️ Has uncommitted changes |
| **mind-training** | JavaScript | ✅ Ready |
| **money-making-app** | Flutter | ⚠️ Has uncommitted changes |
| **warps** | JavaScript | ✅ Ready |

## 🚀 How to Run

### Option 1: Safe Test Run (Recommended First)

```bash
cd /home/rmondo/repos/air-executor
./scripts/run_real_projects.sh
```

**What it does**:
- ✅ Checks all prerequisites
- ✅ Verifies projects exist
- ✅ Warns about uncommitted changes
- ✅ Runs orchestrator once
- ✅ Shows results

**Time**: ~5-20 minutes for first run

### Option 2: PM2 Automation

```bash
cd /home/rmondo/repos/air-executor

# Start background process
pm2 start ecosystem.real-projects.config.js

# Watch logs in realtime
pm2 logs real-projects-fixing

# Check status
pm2 status
```

**What it does**:
- Runs 5 iterations automatically
- Stops after 2 hours or 5 iterations
- Logs everything to `logs/real-projects-out.log`
- No auto-restart (run once then stop)

## ⚠️ Before First Run

### 1. Handle Uncommitted Changes

**cc-task-manager** and **money-making-app** have uncommitted changes.

**Options**:
```bash
# Option A: Commit current changes first
cd /home/rmondo/repos/cc-task-manager
git add -A && git commit -m "WIP: Before autonomous fixing"

cd /home/rmondo/repos/money-making-app
git add -A && git commit -m "WIP: Before autonomous fixing"

# Option B: Stash changes
cd /home/rmondo/repos/cc-task-manager
git stash

cd /home/rmondo/repos/money-making-app
git stash

# Option C: Continue anyway (orchestrator will commit on top)
# Just answer 'y' when prompted
```

### 2. Ensure Dependencies Installed

**JavaScript projects** need `npm install`:
```bash
cd /home/rmondo/repos/cc-task-manager && npm install
cd /home/rmondo/repos/mind-training && npm install
cd /home/rmondo/repos/warps && npm install
```

**Flutter project** needs `flutter pub get`:
```bash
cd /home/rmondo/repos/money-making-app && flutter pub get
```

## 📊 What to Expect

### First Run Output

```
🚀 Multi-Language Autonomous Fixing
Languages enabled: python, javascript, flutter

📦 Detected Projects:
   PYTHON: 1 project(s)
     - /home/rmondo/repos/air-executor
   JAVASCRIPT: 3 project(s)
     - /home/rmondo/repos/cc-task-manager
     - /home/rmondo/repos/mind-training
     - /home/rmondo/repos/warps
   FLUTTER: 1 project(s)
     - /home/rmondo/repos/money-making-app

📍 PRIORITY 1: Fast Static Analysis
   🔍 PYTHON: Analyzing...
   🔍 JAVASCRIPT: Analyzing...
   🔍 FLUTTER: Analyzing...

   📊 Phase Result:
      Score: 75.0%  (example)
      ✅ or ❌ based on threshold
```

### If Gates Pass

Orchestrator will:
1. Fix static issues (P1)
2. Run tests (P2)
3. Fix test failures
4. Create commits for each batch
5. Repeat up to 5 times

### If Gates Fail

Orchestrator will:
1. Show which priority failed
2. Show score vs threshold
3. Recommend fixing those issues
4. Exit (can run again)

## 🔍 Monitoring Progress

### During Run

```bash
# If using PM2
pm2 logs real-projects-fixing

# Or tail log file
tail -f logs/real-projects-out.log
```

### Check Commits After

```bash
# air-executor
cd /home/rmondo/repos/air-executor
git log --oneline -5

# money-making-app
cd /home/rmondo/repos/money-making-app
git log --oneline -5

# All projects at once
for p in air-executor cc-task-manager mind-training money-making-app warps; do
  echo "=== $p ==="
  cd /home/rmondo/repos/$p && git log --oneline -3
done
```

## ⚙️ Configuration

File: `config/real_projects_fix.yaml`

**Key settings**:
```yaml
# Lenient thresholds for real projects
priorities:
  p1_static:
    success_threshold: 0.80  # 80% (more lenient)
  p2_tests:
    success_threshold: 0.70  # 70% (more lenient)
  p3_coverage:
    enabled: false  # Disabled initially

# Run settings
execution:
  max_iterations: 5       # Run 5 times max
  max_duration_hours: 2   # Stop after 2 hours

# Batch sizes (per iteration)
batch_sizes:
  p1_fixes: 2  # Fix 2 batches of static issues
  p2_fixes: 1  # Fix 1 batch of test issues
```

**Project-specific overrides**:
```yaml
project_overrides:
  # money-making-app: More lenient (more issues)
  "/home/rmondo/repos/money-making-app":
    priorities:
      p1_static:
        success_threshold: 0.75
      p2_tests:
        success_threshold: 0.60

  # air-executor: Higher standards (cleaner project)
  "/home/rmondo/repos/air-executor":
    priorities:
      p1_static:
        success_threshold: 0.85
```

## 🛡️ Safety Features

✅ **All changes are commits** - Easy to review
✅ **No auto-push** - You push when ready
✅ **Git status check** - Warns about uncommitted changes
✅ **Rollback anytime** - `git reset --hard HEAD~N`
✅ **Stops on time limit** - Won't run forever

## 🎯 Recommended Workflow

### Day 1: Test Run

```bash
# Run once to see what happens
./scripts/run_real_projects.sh

# Review commits
for p in air-executor cc-task-manager mind-training money-making-app warps; do
  cd /home/rmondo/repos/$p
  git log -p -1  # Review latest commit
done
```

### Day 2: If Good, Automate

```bash
# Start PM2 automation
pm2 start ecosystem.real-projects.config.js

# Let it run for 5 iterations
pm2 logs real-projects-fixing

# Check results after it stops
pm2 status real-projects-fixing
```

### Day 3: Review & Push

```bash
# Review all changes
# Push projects you're happy with
cd /home/rmondo/repos/air-executor && git push
cd /home/rmondo/repos/money-making-app && git push
# etc...

# Reset projects you're not happy with
cd /home/rmondo/repos/someproject && git reset --hard HEAD~5
```

## 🔧 Troubleshooting

### Script won't run

```bash
# Make it executable
chmod +x scripts/run_real_projects.sh

# Check venv exists
ls ~/.venv/air-executor/bin/python

# Check Redis
redis-cli ping
```

### No commits created

**Possible reasons**:
1. Projects already healthy (good!)
2. Thresholds not met (check logs)
3. Tests not installed (`npm install`, etc.)

**Check logs**:
```bash
cat logs/real-projects-out.log | grep "Score:"
```

### Want to test on just one project

Edit `config/real_projects_fix.yaml`:
```yaml
languages:
  enabled:
    - python  # Only air-executor

# Or change target
target_project: "/home/rmondo/repos/air-executor"
```

## 📚 Full Documentation

See `docs/REAL_PROJECTS_GUIDE.md` for comprehensive guide including:
- Detailed configuration options
- Advanced usage
- PM2 commands
- Performance expectations
- Rollback procedures

## ✅ You're Ready!

Everything is set up. Just run:

```bash
./scripts/run_real_projects.sh
```

And watch the orchestrator work! 🚀
