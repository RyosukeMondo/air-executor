# Prompt Engineering Mode - Quick Start

## 🚀 5-Minute Quick Start

### 1. Run Your First Experiment

```bash
# Test 2 different error-fixing prompts
python airflow_dags/autonomous_fixing/prompt_engineer.py \
  config/experiments/quick-test.yaml
```

**Output:**
- Runs both prompts on same project
- Resets git state between tests
- Shows winner
- Saves detailed logs

### 2. View Results

```bash
# List all experiments
python scripts/analyze_experiments.py --list

# Analyze latest experiment
python scripts/analyze_experiments.py logs/prompt-experiments/suite_[SESSION_ID].json
```

### 3. Examine Winning Prompt

```bash
# Show prompt details
python scripts/analyze_experiments.py \
  logs/prompt-experiments/suite_[SESSION_ID].json \
  --prompt [PROMPT_NAME]
```

### 4. Use Winner in Production

```yaml
# Update config/prompts.yaml with winning approach
tests:
  create_tests:
    template: |
      [Copy winning prompt text here]
```

---

## 📋 Common Tasks

### Test Flutter Test Creation (5 variants)

```bash
python airflow_dags/autonomous_fixing/prompt_engineer.py \
  config/experiments/test-creation-flutter.yaml
```

**What it tests:**
- Baseline (current prompt)
- Explicit location specification
- Discovery-first approach
- Step-by-step with verification
- Example-driven
- Minimal viable

**Duration:** ~30-45 minutes (5 variants × 6-9 min each)

### Create Custom Experiment

```bash
cat > config/experiments/my-test.yaml << 'EOF'
name: "My Custom Test"
project:
  path: "/home/rmondo/repos/my-project"
baseline:
  git_ref: "HEAD"
prompts:
  - name: "current"
    text: "Current approach"
  - name: "improved"
    text: "Improved approach"
EOF

python airflow_dags/autonomous_fixing/prompt_engineer.py \
  config/experiments/my-test.yaml
```

### Compare Two Experiment Runs

```bash
# Run experiments at different times
python prompt_engineer.py config/experiments/test1.yaml  # Morning
python prompt_engineer.py config/experiments/test1.yaml  # After changes

# Compare results
python scripts/analyze_experiments.py --compare \
  logs/prompt-experiments/suite_20251003_090000.json \
  logs/prompt-experiments/suite_20251003_150000.json
```

---

## 📊 Understanding Results

### Success Indicators

✅ **Good Experiment:**
```
Prompt                         Success    Duration      Files    Lines
------------------------------ ---------- ------------ -------- --------
improved_v2                    ✅              38.7s        8      156

🏆 Winner: improved_v2
   Reason: Fastest successful experiment (38.7s)
```

⚠️ **Problem Experiment:**
```
Prompt                         Success    Duration      Files    Lines
------------------------------ ---------- ------------ -------- --------
broken_approach                ❌              12.3s        0        0

Failed Experiments: 1
  - broken_approach: Timeout waiting for response
```

### Key Metrics

| Metric | What it means | Good value |
|--------|---------------|------------|
| **Success** | Did it complete without errors? | ✅ |
| **Duration** | How long did it take? | Lower is better (but not too fast) |
| **Files** | How many files changed? | Depends on task |
| **Lines** | Total lines added/removed | Fewer changes = more focused |
| **Commit** | Was a git commit made? | Should exist for fixes |

### Red Flags

🚩 **Too fast (< 5s):** Probably failed immediately
🚩 **No commit:** Changes not saved
🚩 **0 files changed:** Nothing actually happened
🚩 **Success but wrong result:** Need to check Claude response manually

---

## 🔍 Investigation Workflow

### When Tests Aren't Detected (0/0 tests bug)

```bash
# 1. Run experiment with 5 variants
python prompt_engineer.py config/experiments/test-creation-flutter.yaml

# 2. Check which ones created tests
python scripts/analyze_experiments.py logs/prompt-experiments/suite_*.json

# 3. Look at winner's approach
python scripts/analyze_experiments.py \
  logs/prompt-experiments/suite_*.json \
  --prompt minimal_viable

# 4. Verify tests actually work
cd /home/rmondo/repos/money-making-app
git log -1 --stat  # Check what was committed
flutter test       # Verify tests run

# 5. If tests work, update prompts.yaml
# If not, create new experiment with refined prompts
```

### When Fixes Take Too Long

```bash
# Test concise vs detailed prompts
cat > config/experiments/speed-test.yaml << 'EOF'
name: "Speed Optimization"
prompts:
  - name: "detailed_slow"
    text: |
      Analyze all errors
      Categorize by type
      Fix each systematically
      Verify after each fix
    timeout: 600

  - name: "concise_fast"
    text: "Fix first error from linter"
    timeout: 300
EOF

python prompt_engineer.py config/experiments/speed-test.yaml
```

### When Results Are Inconsistent

```bash
# Run same experiment 3 times
for i in 1 2 3; do
  python prompt_engineer.py config/experiments/stability-test.yaml
  sleep 5
done

# Compare variance
python scripts/analyze_experiments.py --compare \
  logs/prompt-experiments/suite_*_run1.json \
  logs/prompt-experiments/suite_*_run2.json
```

---

## 💡 Prompt Engineering Tips

### Start Simple, Add Complexity

```yaml
# Iteration 1: Test basic idea
prompts:
  - name: "basic"
    text: "Create tests"

# Iteration 2: Add specificity
prompts:
  - name: "specific"
    text: "Create tests in test/ directory"

# Iteration 3: Add verification
prompts:
  - name: "verified"
    text: |
      Create tests in test/ directory
      Run flutter test to verify
      Show test count
```

### Use Control Experiments

```yaml
prompts:
  - name: "baseline"
    file: "config/prompts/current.txt"  # Known working prompt

  - name: "experiment"
    text: "New approach..."  # What you're testing
```

### Test Edge Cases

```yaml
name: "Edge Case Testing"
prompts:
  - name: "handles_no_tests"
    text: "Create tests (even if none exist)"

  - name: "handles_broken_tests"
    text: "Fix or replace broken tests"

  - name: "handles_partial_tests"
    text: "Expand existing test coverage"
```

---

## 📁 File Organization

```
air-executor/
├── config/
│   ├── experiments/           # Experiment configs
│   │   ├── test-creation-flutter.yaml
│   │   ├── quick-test.yaml
│   │   └── my-custom.yaml
│   └── prompts/              # Saved prompt templates
│       └── test-creation-baseline.txt
├── logs/
│   └── prompt-experiments/   # Results
│       ├── suite_20251003_151530.json      # Summary
│       ├── 20251003_151530_variant1.json   # Individual
│       └── 20251003_151530_variant2.json   # Individual
└── scripts/
    └── analyze_experiments.py
```

---

## 🎯 Next Steps

### After Running Experiments

1. **Analyze winner:**
   ```bash
   python scripts/analyze_experiments.py \
     logs/prompt-experiments/suite_*.json \
     --prompt [WINNER_NAME]
   ```

2. **Test in real workflow:**
   - Copy winning prompt to `config/prompts.yaml`
   - Run autonomous fixing with new prompt
   - Verify it works in production

3. **Iterate if needed:**
   - Create new experiment with refined variants
   - Focus on remaining issues
   - Repeat until optimal

### Sharing Results

```bash
# Export experiment results
cp logs/prompt-experiments/suite_*.json docs/experiments/

# Commit improvements
git add config/prompts.yaml docs/experiments/
git commit -m "feat: improve test creation prompt (experiment suite_20251003)"
```

---

## 🔧 Troubleshooting

### "No such file or directory"

```bash
# Create missing directories
mkdir -p config/experiments
mkdir -p config/prompts
mkdir -p logs/prompt-experiments
```

### "Timeout waiting for response"

```yaml
# Increase timeout in experiment config
prompts:
  - name: "slow_task"
    timeout: 1200  # 20 minutes
```

### "Git reset failed"

```bash
# Manual cleanup
cd /path/to/project
git reset --hard HEAD
git clean -fd
```

### "Can't find experiment suite"

```bash
# List all suites
python scripts/analyze_experiments.py --list

# Use full path
python scripts/analyze_experiments.py \
  /full/path/to/logs/prompt-experiments/suite_*.json
```

---

## 📚 Learn More

- **Full Documentation:** [claudedocs/prompt-engineering-mode.md](prompt-engineering-mode.md)
- **Example Configs:** `config/experiments/`
- **System Design:** [claudedocs/commit-verification-implementation.md](commit-verification-implementation.md)
