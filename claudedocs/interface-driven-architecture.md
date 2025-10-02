# Interface-Driven Architecture

## Core Principle

**We define interfaces. Claude generates implementations.**

```
Air-Executor          Claude             Air-Executor
   (Interface) ────>  (Implementation) ──> (Execution)

   "Generate a      "Here's a script     "Run script,
    script that      that does what       parse output,
    does X and       you want"            always works"
    outputs Y"
```

## The Problem We're Solving

### Anti-Pattern: Claude Does Everything

```yaml
# BAD: Vague, unpredictable
prompt: "Analyze this project and tell me about complexity issues"

# Claude might respond:
- "There are some complex functions"
- Or detailed JSON
- Or markdown tables
- Or just text descriptions

# Result: Fragile, hard to parse, unreliable
```

### Solution: Contract-Driven Generation

```yaml
# GOOD: Explicit contract
prompt: |
  Generate a script that checks complexity.

  Requirements:
  - Executable bash/node/python script
  - Takes args: project_path, threshold
  - Outputs JSON to: .air-executor/complexity.json
  - Schema: { violations: [...], total: int }
  - Exit 0 on success

  Save to: {project_path}/.air-executor/check-complexity.sh

# Claude generates CONCRETE, TESTABLE script
# Air-executor runs it - always the same way
```

## Interface Definition Pattern

### Step 1: Define Interface

```yaml
# config/interfaces/test-runner.yaml
interface:
  name: run_tests
  version: "1.0"

  contract:
    input:
      project_path: string
      strategy: enum[minimal, selective, comprehensive]

    output_location: "{project_path}/.air-executor/test-results.json"

    output_schema:
      total_tests: int
      passed: int
      failed: int
      skipped: int
      duration_seconds: float
      failures:
        - test_name: string
          file: string
          line: int
          error: string

    execution:
      script_path: "{project_path}/.air-executor/run-tests.sh"
      timeout: 1800
      exit_codes:
        0: success
        1: tests_failed
        2: setup_error
```

### Step 2: Claude Generates Implementation

**Prompt:**
```yaml
Generate a test runner script for {language} project.

CONTRACT (you must follow exactly):

1. Script location: {project_path}/.air-executor/run-tests.sh
2. Arguments: $1=strategy (minimal|selective|comprehensive)
3. Output: {project_path}/.air-executor/test-results.json

Output JSON schema (exact format):
{
  "total_tests": 0,
  "passed": 0,
  "failed": 0,
  "skipped": 0,
  "duration_seconds": 0.0,
  "failures": [
    {
      "test_name": "string",
      "file": "string",
      "line": 0,
      "error": "string"
    }
  ]
}

Exit codes:
- 0: Tests completed (even if some failed)
- 1: Tests failed to run
- 2: Setup error

Generate the script now. Make it robust and handle errors.
```

**Claude Output:**
```bash
#!/bin/bash
# Auto-generated test runner for cc-task-manager
set -e

PROJECT_PATH=$(dirname $(dirname "$0"))
STRATEGY=$1

cd "$PROJECT_PATH"

# Determine test command based on strategy
case "$STRATEGY" in
  minimal)
    ARGS="--testPathPattern=unit --bail"
    ;;
  selective)
    ARGS="--testPathPattern=(unit|integration)"
    ;;
  comprehensive)
    ARGS=""
    ;;
esac

# Run tests and capture JSON output
pnpm run test -- --json --outputFile=.air-executor/jest-raw.json $ARGS

# Parse Jest output to our contract format
node << 'EOF'
const fs = require('fs');
const jest = JSON.parse(fs.readFileSync('.air-executor/jest-raw.json'));

const result = {
  total_tests: jest.numTotalTests,
  passed: jest.numPassedTests,
  failed: jest.numFailedTests,
  skipped: jest.numPendingTests,
  duration_seconds: jest.testResults.reduce((sum, r) => sum + r.perfStats.runtime, 0) / 1000,
  failures: []
};

jest.testResults.forEach(file => {
  file.testResults.forEach(test => {
    if (test.status === 'failed') {
      result.failures.push({
        test_name: test.fullName,
        file: file.name,
        line: test.location?.line || 0,
        error: test.failureMessages.join('\n')
      });
    }
  });
});

fs.writeFileSync('.air-executor/test-results.json', JSON.stringify(result, null, 2));
console.log(`Tests: ${result.passed}/${result.total_tests} passed`);
EOF

exit 0
```

### Step 3: Air-Executor Runs It

```python
# executor.py - Simple, reliable
def run_tests(project_path: str, strategy: str) -> TestResults:
    script = Path(project_path) / ".air-executor" / "run-tests.sh"

    # Run script (contract guaranteed by Claude)
    result = subprocess.run(
        [str(script), strategy],
        timeout=1800,
        capture_output=True
    )

    # Read known output (contract guaranteed)
    output_file = Path(project_path) / ".air-executor" / "test-results.json"
    data = json.load(output_file.open())

    # Parse with confidence - schema is guaranteed!
    return TestResults(
        total=data['total_tests'],
        passed=data['passed'],
        failed=data['failed'],
        failures=[Failure(**f) for f in data['failures']]
    )
```

## Benefits

### 1. Robustness
- ✅ Scripts are testable independently
- ✅ Output format is guaranteed
- ✅ No parsing surprises

### 2. Simplicity
- ✅ Air-executor code is trivial (run script, read JSON)
- ✅ No complex parsing logic
- ✅ Easy to debug (inspect generated scripts)

### 3. Flexibility
- ✅ Claude adapts to project specifics
- ✅ Generated scripts handle edge cases
- ✅ Can regenerate if project changes

### 4. Testability
- ✅ Can test scripts manually: `bash check-complexity.sh /path 15`
- ✅ Can validate output: `cat .air-executor/complexity.json`
- ✅ Can mock for unit tests

### 5. Inversion of Control
- ✅ **We** define how things work
- ✅ Claude provides implementation
- ✅ Clear separation of concerns

## Complete Example: Complexity Check

### Interface Definition

```yaml
# config/interfaces/complexity-check.yaml
name: complexity_check
version: "1.0"

contract:
  script: "{project}/.air-executor/check-complexity.sh"

  args:
    - project_path
    - threshold (int)

  output: "{project}/.air-executor/complexity.json"

  schema:
    violations:
      type: array
      items:
        file: string
        function: string
        complexity: int
        line: int
        suggestion: string
    total_violations: int

  exit_codes:
    0: success
    1: error
```

### Prompt for Claude

```yaml
Generate complexity check script for {language} project.

CONTRACT (must follow):
- Script: {project}/.air-executor/check-complexity.sh
- Args: $1=project_path $2=threshold
- Output: {project}/.air-executor/complexity.json

Output JSON (exact schema):
{
  "violations": [
    {
      "file": "string",
      "function": "string",
      "complexity": 0,
      "line": 0,
      "suggestion": "string"
    }
  ],
  "total_violations": 0
}

Language-specific tools:
- JavaScript: eslint-plugin-complexity
- Python: radon
- Flutter: dart_code_metrics
- Go: gocyclo

Generate robust script that:
1. Runs appropriate tool
2. Parses tool output
3. Converts to our JSON format
4. Handles errors gracefully
5. Always produces valid JSON
```

### Claude's Output

**For JavaScript:**
```bash
#!/bin/bash
set -euo pipefail

PROJECT_PATH=$1
THRESHOLD=$2

cd "$PROJECT_PATH"

# Create output directory
mkdir -p .air-executor

# Run eslint with complexity checking
npx eslint . \
  --format json \
  --rule "complexity: [\"error\", $THRESHOLD]" \
  > .air-executor/eslint-raw.json 2>&1 || true

# Convert to contract format
node << 'EOF'
const fs = require('fs');

try {
  const eslint = JSON.parse(fs.readFileSync('.air-executor/eslint-raw.json', 'utf-8'));

  const violations = [];

  eslint.forEach(file => {
    file.messages.forEach(msg => {
      if (msg.ruleId === 'complexity') {
        const complexityMatch = msg.message.match(/complexity of (\d+)/);
        const functionMatch = msg.message.match(/'(.+?)' has/);

        violations.push({
          file: file.filePath.replace(process.cwd() + '/', ''),
          function: functionMatch ? functionMatch[1] : 'unknown',
          complexity: complexityMatch ? parseInt(complexityMatch[1]) : 0,
          line: msg.line,
          suggestion: `Refactor to reduce complexity below ${process.env.THRESHOLD}`
        });
      }
    });
  });

  const result = {
    violations: violations,
    total_violations: violations.length
  };

  fs.writeFileSync('.air-executor/complexity.json', JSON.stringify(result, null, 2));
  console.log(`Found ${violations.length} complexity violations`);

} catch (err) {
  // Error case - still write valid JSON
  fs.writeFileSync('.air-executor/complexity.json', JSON.stringify({
    violations: [],
    total_violations: 0,
    error: err.message
  }, null, 2));
  process.exit(1);
}
EOF
```

### Air-Executor Runs It

```python
def check_complexity(project_path: str, threshold: int) -> ComplexityResult:
    # Setup script location
    script = Path(project_path) / ".air-executor" / "check-complexity.sh"

    # Ensure script is executable
    script.chmod(0o755)

    # Run script with contract args
    subprocess.run([str(script), project_path, str(threshold)])

    # Read contract output
    output = Path(project_path) / ".air-executor" / "complexity.json"
    data = json.load(output.open())

    # Parse with confidence (schema guaranteed!)
    return ComplexityResult(
        violations=[Violation(**v) for v in data['violations']],
        total=data['total_violations']
    )
```

## Implementation Strategy

### Step 1: Define All Interfaces

```
config/interfaces/
├── complexity-check.yaml
├── test-runner.yaml
├── static-analysis.yaml
├── test-discovery.yaml
└── health-evaluation.yaml
```

### Step 2: Create Generator Prompts

```yaml
# config/prompts.yaml
script_generation:
  complexity_check:
    template: |
      Generate complexity check script for {language}.
      CONTRACT: [load from config/interfaces/complexity-check.yaml]

  test_runner:
    template: |
      Generate test runner script for {language}.
      CONTRACT: [load from config/interfaces/test-runner.yaml]
```

### Step 3: Setup Phase Generates Scripts

```python
# setup_phase.py
def setup_project(project_path, language):
    # Generate all scripts via Claude
    scripts = [
        'check-complexity',
        'run-tests',
        'static-analysis',
        'evaluate-health'
    ]

    for script_name in scripts:
        prompt = build_prompt(script_name, language)
        claude_wrapper(prompt, project_path)

        # Verify script exists and is valid
        script_path = Path(project_path) / ".air-executor" / f"{script_name}.sh"
        assert script_path.exists()
        script_path.chmod(0o755)
```

### Step 4: Execution Uses Scripts

```python
# Simple, predictable execution
def execute_phase(project_path, phase):
    script = Path(project_path) / ".air-executor" / f"{phase}.sh"
    subprocess.run([str(script)])

    output = Path(project_path) / ".air-executor" / f"{phase}.json"
    return json.load(output.open())
```

## Summary

**Your Insight:**
> "We must have tasks that can perform concretely, robustly. Claude should provide scripts we can execute reliably."

**Architecture:**
```
Interface Definition (We control)
        ↓
Script Generation (Claude implements)
        ↓
Script Execution (We run reliably)
        ↓
Known Output Format (We parse confidently)
```

**Benefits:**
- Inversion of control - we define, Claude implements
- Robust - scripts are testable, debuggable
- Simple - air-executor just runs scripts and reads JSON
- Flexible - Claude adapts to project specifics

**Next Step:**
Implement interface-driven architecture:
1. Define interfaces for all operations
2. Update prompts to generate scripts
3. Simplify air-executor to script runner
4. Test with real projects
