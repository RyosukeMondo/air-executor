# LLM-First Architecture - Design Document

## Philosophy

**Core Principle:** Use LLM for ALL complex, vague, uncertain work.

```
Complex/Vague/Uncertain → claude_wrapper (LLM intelligence)
                              ↓
                        Concrete Configs
                              ↓
                  Simple/Deterministic → air-executor (orchestration)
```

**Roles:**
- **claude_wrapper**: Researcher, Fixer, Evaluator (Intelligence)
- **air-executor**: Reader, Executor, Tracker (Orchestration)

## Current Architecture Issues

### What We're Doing Wrong

**1. Language Adapters = Complex Logic**
```python
# javascript_adapter.py - 400+ lines of detection logic
def static_analysis(self):
    # Parse eslint output
    # Parse tsc output
    # Detect complexity
    # Parse file sizes
    # Return structured data
```

**Problem:** We're writing complex parsers, detectors, analyzers in Python.

**Solution:** Ask Claude to analyze and report findings.

---

**2. Hardcoded Analysis Logic**
```python
# Complexity calculation
complexity = self._calculate_complexity(file)
if complexity > threshold:
    violations.append(...)
```

**Problem:** Brittle, language-specific, maintenance burden.

**Solution:** Claude analyzes code quality, reports findings.

---

**3. Scoring Logic in Python**
```python
# scorer.py
score = projects_with_no_errors / total_projects
if score >= threshold:
    passed = True
```

**Problem:** Scoring is judgement - perfect for LLM!

**Solution:** Claude evaluates health, provides score + reasoning.

## LLM-First Architecture

### Principle 1: Claude Does Intelligence Work

**OLD (Code-First):**
```python
# adapter.py - 200 lines of parsing logic
def static_analysis(self, project_path):
    # Run eslint
    # Parse output
    # Extract errors
    # Categorize issues
    # Calculate metrics
    return AnalysisResult(errors, warnings, complexity, ...)
```

**NEW (LLM-First):**
```python
# adapter.py - 20 lines
def static_analysis(self, project_path):
    # Ask Claude to analyze
    prompt = self.prompts['analysis']['static_analysis']
    result = claude_wrapper(prompt, project_path)

    # Claude saves: config/analysis-cache/{project}-static.yaml
    return load_config(f"config/analysis-cache/{project}-static.yaml")
```

**Claude's Output:**
```yaml
# config/analysis-cache/cc-task-manager-static.yaml
project: cc-task-manager
language: javascript
analyzed_at: 2025-10-03T11:00:00

health:
  overall: "good"
  score: 0.85

errors:
  count: 0
  critical: []

warnings:
  count: 12
  top_3:
    - file: src/utils/helper.js
      line: 45
      message: "Unused variable 'temp'"

complexity:
  violations: 3
  top_violations:
    - file: src/api/handler.js
      function: processRequest
      complexity: 18
      threshold: 15
      suggestion: "Extract validation logic into separate function"

file_sizes:
  violations: 2
  top_violations:
    - file: src/components/Dashboard.js
      lines: 850
      threshold: 800
      suggestion: "Split into Dashboard.js and DashboardCharts.js"

recommendations:
  priority: "medium"
  actions:
    - "Refactor processRequest function to reduce complexity"
    - "Split Dashboard component into smaller files"

reasoning: |
  Project health is good (85%). No critical errors.
  Main concerns are code complexity and file size in 2 files.
  These are maintainability issues, not functionality blockers.
```

### Principle 2: Configs Are Communication Protocol

**Phases communicate via YAML configs:**

```
PHASE 1: Discovery (Claude researches)
   └─> config/discovery/{project}-setup.yaml

PHASE 2: Analysis (Claude analyzes)
   └─> config/analysis/{project}-static.yaml
   └─> config/analysis/{project}-tests.yaml

PHASE 3: Fixing (Claude fixes)
   └─> config/fixes/{project}-iteration-{N}.yaml

PHASE 4: Evaluation (Claude judges)
   └─> config/evaluation/{project}-health.yaml
```

**Air-executor reads configs, orchestrates flow:**

```python
# iteration_engine.py - SIMPLE orchestration
def run_loop(self):
    # 1. Ask Claude to analyze
    self.fixer.analyze_project(project)

    # 2. Read Claude's analysis
    analysis = load_yaml(f"config/analysis/{project}-static.yaml")

    # 3. Check health score
    if analysis['health']['score'] < threshold:
        # 4. Ask Claude to fix
        self.fixer.fix_issues(project, analysis['recommendations'])

    # 5. Ask Claude to evaluate
    evaluation = self.fixer.evaluate_health(project)
```

### Principle 3: Separation by Complexity

**Rule:** If logic requires judgement, parsing, or heuristics → Claude does it.

**Examples:**

| Task | Complexity | Who Does It |
|------|------------|-------------|
| Parse eslint output | Complex | ❌ Python → ✅ Claude |
| Calculate complexity | Complex | ❌ Python → ✅ Claude |
| Determine if code is "good" | Judgement | ✅ Claude |
| Decide what to fix first | Judgement | ✅ Claude |
| Run subprocess | Simple | ✅ Python |
| Load YAML | Simple | ✅ Python |
| Track iterations | Simple | ✅ Python |

## Implementation Plan

### Phase 1: Analysis → Claude

**Current (Complex Python):**
- `language_adapters/*.py` - 400+ lines each
- Parse linter output
- Calculate complexity
- Extract errors/warnings

**New (Simple Delegation):**
```python
# analyzer.py - SIMPLE
class ProjectAnalyzer:
    def analyze_static(self, project_path, language):
        prompt = self.prompts['analysis']['static_analysis']
        cache_file = f"config/analysis/{project_name}-static.yaml"

        # Check cache (fast path)
        if cache_file.exists() and self._is_fresh(cache_file):
            return load_yaml(cache_file)

        # Ask Claude to analyze
        subprocess.run([
            self.python_exec, self.wrapper_path,
            '--prompt', prompt,
            '--project', project_path,
            '--output', cache_file
        ])

        return load_yaml(cache_file)
```

**Claude's Prompt:**
```yaml
# prompts.yaml
analysis:
  static_analysis:
    template: |
      Analyze the {language} project for code quality issues.

      Your task:
      1. Run appropriate linters (eslint, pylint, flutter analyze)
      2. Check for errors and warnings
      3. Analyze code complexity (functions >15 complexity)
      4. Check file sizes (files >800 lines)
      5. Provide overall health assessment

      Save findings to: {output_file}

      Use the YAML format provided in the template.
      Be thorough but focus on actionable issues.
```

---

### Phase 2: Scoring → Claude

**Current (Python Logic):**
```python
# scorer.py - Hardcoded rules
score = projects_with_no_errors / total_projects
if score >= threshold:
    passed = True
```

**New (LLM Evaluation):**
```python
# evaluator.py - Simple
class HealthEvaluator:
    def evaluate(self, project_path):
        prompt = self.prompts['evaluation']['health_check']
        cache_file = f"config/evaluation/{project_name}-health.yaml"

        subprocess.run([
            self.python_exec, self.wrapper_path,
            '--prompt', prompt,
            '--project', project_path,
            '--output', cache_file
        ])

        return load_yaml(cache_file)
```

**Claude's Output:**
```yaml
# config/evaluation/cc-task-manager-health.yaml
project: cc-task-manager
evaluated_at: 2025-10-03T11:05:00

health_check:
  p1_static:
    score: 0.90
    passed: true
    reasoning: "No critical errors. 3 complexity violations are manageable."

  p2_tests:
    score: 0.85
    passed: true
    reasoning: "85% tests passing. 3 failing tests are in edge case handling."

  overall:
    score: 0.875
    grade: "B+"
    passed: true

recommendations:
  continue_to_next_phase: true
  priority_fixes:
    - "Fix 3 failing edge case tests"
    - "Refactor processRequest function"

evaluation_notes: |
  Project is in good health overall. Static analysis passed with minor
  complexity issues. Tests mostly passing - 3 failures are in error
  handling for edge cases. Safe to continue to next phase.
```

---

### Phase 3: Simplify Adapters → Config Readers

**OLD (Complex Adapter):**
```python
# javascript_adapter.py - 400 lines
class JavaScriptAdapter:
    def static_analysis(self):
        # 100 lines: Run eslint, parse output
        # 50 lines: Run tsc, parse errors
        # 80 lines: Calculate complexity
        # 50 lines: Check file sizes
        # Return structured data

    def run_tests(self):
        # 80 lines: Detect test framework
        # 60 lines: Build test command
        # 40 lines: Parse test output
        # Return test results
```

**NEW (Simple Config Reader):**
```python
# adapters/base.py - 50 lines TOTAL for ALL languages
class ConfigBasedAdapter:
    def __init__(self, project_path):
        self.project = Path(project_path).name

    def analyze_static(self):
        return self._call_claude('analysis', 'static_analysis')

    def run_tests(self):
        return self._call_claude('testing', 'run_tests')

    def _call_claude(self, phase, task):
        output = f"config/{phase}/{self.project}-{task}.yaml"
        prompt = self.prompts[phase][task]

        subprocess.run([
            'python', 'scripts/claude_wrapper.py',
            '--prompt', prompt,
            '--project', self.project_path,
            '--output', output
        ])

        return yaml.safe_load(open(output))
```

**No more language-specific adapters!** Just config-driven Claude calls.

---

### Phase 4: Config Organization

**Structure:**
```
config/
├── prompts.yaml              # All prompts (already done)
│
├── discovery/                # SETUP phase outputs
│   ├── cc-task-manager-setup.yaml
│   ├── mind-training-setup.yaml
│   └── warps-setup.yaml
│
├── analysis/                 # Analysis phase outputs
│   ├── cc-task-manager-static.yaml
│   ├── cc-task-manager-tests.yaml
│   └── ...
│
├── fixes/                    # Fix phase outputs
│   ├── cc-task-manager-iteration-1.yaml
│   ├── cc-task-manager-iteration-2.yaml
│   └── ...
│
├── evaluation/               # Evaluation phase outputs
│   ├── cc-task-manager-health.yaml
│   └── ...
│
└── projects/                 # Project configs (existing)
    ├── cc-task-manager.yaml
    └── ...
```

**Config Size Management:**

If `prompts.yaml` gets too big:
```
config/
├── prompts/
│   ├── discovery.yaml
│   ├── analysis.yaml
│   ├── fixing.yaml
│   └── evaluation.yaml
```

## Benefits

### 1. Simplicity
- **Before**: 2000+ lines of adapter logic
- **After**: 200 lines of orchestration

### 2. Flexibility
- Change analysis strategy? → Edit prompt
- Add new language? → No code changes
- Improve evaluation? → Iterate on prompt

### 3. Transparency
- Every phase documented in YAML
- Easy to inspect Claude's reasoning
- Can replay/debug easily

### 4. Maintainability
- Code = simple orchestration
- Intelligence = in prompts (easy to iterate)
- No complex parsing/detection logic

### 5. Development Velocity
- **Before**: Write Python code, test, debug
- **After**: Write prompt, test output, iterate

### 6. Self-Improvement
- Claude analyzes its own output
- Suggests prompt improvements
- Can iterate autonomously

## Implementation Order

### Step 1: Add Analysis Prompt ✅ (Ready)
```yaml
# prompts.yaml
analysis:
  static_analysis:
    template: |
      Analyze {language} project for quality issues...
```

### Step 2: Simplify Analyzer (This PR)
```python
# core/analyzer.py - Remove complex logic, delegate to Claude
def analyze_static(self, project):
    return self._call_claude('analysis/static_analysis', project)
```

### Step 3: Add Evaluation Prompt
```yaml
# prompts.yaml
evaluation:
  health_check:
    template: |
      Evaluate project health and determine if gates passed...
```

### Step 4: Simplify Scorer
```python
# core/scorer.py → core/evaluator.py
def evaluate_health(self, project):
    return self._call_claude('evaluation/health_check', project)
```

### Step 5: Remove Language Adapters
```python
# Delete: language_adapters/*.py (1600 lines)
# Keep: One simple config-based adapter (50 lines)
```

### Step 6: Test & Iterate
- Run with real projects
- Inspect Claude's outputs
- Refine prompts based on results
- Let system self-improve

## Migration Strategy

**Option 1: Big Bang (Risky)**
- Rewrite everything at once
- ❌ High risk

**Option 2: Gradual (Safe)** ✅
1. Add Claude-based analysis (parallel to existing)
2. Compare outputs
3. When confident, switch to Claude
4. Repeat for each component
5. Remove old code

**We'll use Option 2.**

## Example: Before & After

### Before (Code-First)
```python
# 400 lines of adapter logic
class JavaScriptAdapter:
    def static_analysis(self, project_path):
        # Run eslint
        eslint_result = subprocess.run(['eslint', '.'], ...)

        # Parse output - 50 lines of regex
        errors = []
        for line in eslint_result.stdout.split('\n'):
            match = re.match(r'(.+?):(\d+):(\d+): (.+)', line)
            if match:
                errors.append({
                    'file': match.group(1),
                    'line': int(match.group(2)),
                    'message': match.group(4)
                })

        # Calculate complexity - 80 lines
        complexity = self._analyze_complexity(project_path)

        # Check file sizes - 40 lines
        large_files = self._check_file_sizes(project_path)

        return AnalysisResult(
            errors=errors,
            complexity_violations=complexity,
            large_files=large_files
        )
```

### After (LLM-First)
```python
# 20 lines - simple delegation
class Analyzer:
    def analyze_static(self, project_path):
        # Ask Claude to analyze and save results
        prompt = self.prompts['analysis']['static_analysis']
        output = f"config/analysis/{project_name}-static.yaml"

        claude_wrapper(prompt, project_path, output)

        # Load Claude's analysis
        return yaml.safe_load(open(output))
```

**Claude does:**
- Run linters
- Parse output
- Calculate complexity
- Analyze file sizes
- Provide reasoning
- Save structured YAML

**Python does:**
- Load config
- Orchestrate flow
- Track progress

## Summary

**Philosophy Shift:**
- ❌ OLD: Python code does intelligence work
- ✅ NEW: Claude does intelligence, Python orchestrates

**Architecture:**
```
Claude (Researcher/Fixer/Evaluator)
        ↓
  Concrete Configs
        ↓
Air-Executor (Reader/Orchestrator)
```

**Benefits:**
- Simpler code (80% reduction)
- More flexible (prompt iteration)
- More maintainable (no complex logic)
- Self-improving (Claude evaluates Claude)

**Next Step:**
Start migration - one component at a time, validate each step.
