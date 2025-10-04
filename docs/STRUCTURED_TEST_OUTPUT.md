# Structured Test Output Strategy

## Philosophy

**Regex parsing is fragile and should be a last resort.**

Modern test frameworks provide structured output (JSON, XML, TAP) that is:
- **Reliable**: Machine-readable format, no ambiguity
- **Complete**: All test metadata available
- **Version-safe**: Format doesn't change with cosmetic output updates
- **Parseable**: Standard libraries, no regex needed

**Fallback hierarchy:**
1. ✅ **BEST**: Structured output (JSON/XML/TAP)
2. ⚠️  **OK**: Well-documented text format
3. ❌ **LAST RESORT**: Regex parsing of arbitrary text

## Test Framework Support Matrix

### JavaScript/TypeScript

| Framework | Structured Output | Command | Notes |
|-----------|------------------|---------|-------|
| **Jest** | ✅ JSON | `jest --json` | Outputs JSON to stdout (mixed with test output) |
| **Jest** | ✅ JSON File | `jest --json --outputFile=results.json` | Clean JSON file |
| **Jest** | ✅ JUnit XML | `jest --reporters=jest-junit` | Requires jest-junit package |
| **Vitest** | ✅ JSON | `vitest --reporter=json` | Clean JSON output |
| **Mocha** | ✅ JSON | `mocha --reporter json` | Structured JSON |
| **Mocha** | ✅ TAP | `mocha --reporter tap` | TAP format |

###Python

| Framework | Structured Output | Command | Notes |
|-----------|------------------|---------|-------|
| **pytest** | ✅ JUnit XML | `pytest --junitxml=results.xml` | Standard XML format |
| **pytest** | ✅ JSON | `pytest --json-report --json-report-file=results.json` | Requires pytest-json-report |
| **unittest** | ✅ XML | `python -m xmlrunner` | Requires xmlrunner package |

### Go

| Framework | Structured Output | Command | Notes |
|-----------|------------------|---------|-------|
| **go test** | ✅ JSON | `go test -json` | Native JSON support |
| **gotestsum** | ✅ JUnit XML | `gotestsum --junitfile results.xml` | Enhanced test runner |

### Flutter/Dart

| Framework | Structured Output | Command | Notes |
|-----------|------------------|---------|-------|
| **flutter test** | ✅ JSON | `flutter test --machine` | Machine-readable JSON |
| **flutter test** | ✅ JSON File | `flutter test --machine > results.json` | Redirect to file |

## Recommended Implementation Strategy

### Priority 1: Use Structured Output

```python
class JavaScriptAdapter:
    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run tests with structured JSON output."""

        # Try JSON first (best)
        json_result = self._run_tests_json(project_path, strategy)
        if json_result:
            return json_result

        # Fallback to text parsing (last resort)
        return self._run_tests_text(project_path, strategy)

    def _run_tests_json(self, project_path: str, strategy: str):
        """Try to get structured JSON output."""
        try:
            # Method 1: JSON file output (cleanest)
            output_file = Path(project_path) / '.test-results.json'
            cmd = ['npm', 'test', '--', '--json', f'--outputFile={output_file}']

            subprocess.run(cmd, cwd=project_path, timeout=timeout)

            if output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)

                # Parse structured data
                return AnalysisResult(
                    tests_passed=data['numPassedTests'],
                    tests_failed=data['numFailedTests'],
                    tests_skipped=data['numPendingTests'],
                    success=data['success']
                )
        except Exception as e:
            print(f"Structured output failed: {e}, falling back to text parsing")
            return None

    def _run_tests_text(self, project_path: str, strategy: str):
        """Fallback: Parse text output with regex."""
        # Current implementation with regex
        # ... (existing code)
```

### Priority 2: Fallback to Regex (Current)

When structured output fails or isn't available:
- Parse stderr + stdout (Jest outputs to stderr)
- Use findall() to get last match (final summary)
- Handle multiple output formats

## JSON Output Formats

### Jest JSON Structure

```json
{
  "numFailedTestSuites": 1,
  "numFailedTests": 28,
  "numPassedTestSuites": 1,
  "numPassedTests": 64,
  "numPendingTestSuites": 0,
  "numPendingTests": 5,
  "numRuntimeErrorTestSuites": 0,
  "numTotalTestSuites": 2,
  "numTotalTests": 97,
  "success": false,
  "startTime": 1728000000000,
  "testResults": [
    {
      "name": "src/__tests__/validation/schema-tests.ts",
      "status": "passed",
      "summary": "",
      "message": "",
      "assertionResults": [...]
    }
  ]
}
```

**Key Fields:**
- `numPassedTests`: Passed count
- `numFailedTests`: Failed count
- `numPendingTests`: Skipped count
- `numTotalTests`: Total count
- `success`: Overall pass/fail

### Vitest JSON Structure

```json
{
  "testResults": {
    "numTotalTests": 50,
    "numPassedTests": 48,
    "numFailedTests": 2,
    "numPendingTests": 0
  },
  "success": false
}
```

### pytest JSON Structure (with pytest-json-report)

```json
{
  "summary": {
    "passed": 42,
    "failed": 3,
    "skipped": 1,
    "total": 46
  },
  "tests": [
    {
      "nodeid": "test_example.py::test_function",
      "outcome": "passed",
      "duration": 0.001
    }
  ]
}
```

### Go test -json Structure

```json
{"Time":"2025-10-04T10:00:00Z","Action":"run","Package":"github.com/user/pkg","Test":"TestExample"}
{"Time":"2025-10-04T10:00:01Z","Action":"output","Package":"github.com/user/pkg","Test":"TestExample","Output":"=== RUN   TestExample\n"}
{"Time":"2025-10-04T10:00:01Z","Action":"pass","Package":"github.com/user/pkg","Test":"TestExample","Elapsed":0.001}
{"Time":"2025-10-04T10:00:01Z","Action":"pass","Package":"github.com/user/pkg","Elapsed":0.05}
```

**Note:** Go outputs newline-delimited JSON (NDJSON), one event per line.

## Implementation Examples

### Jest with JSON File

```python
def _run_jest_with_json(self, project_path: str) -> Optional[Dict]:
    """Run Jest with JSON output to file."""
    output_file = Path(project_path) / '.jest-results.json'

    try:
        # Remove old results
        output_file.unlink(missing_ok=True)

        # Run with JSON output
        cmd = ['npm', 'test', '--', '--json', f'--outputFile={output_file}']
        subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,  # Suppress test output
            timeout=timeout
        )

        # Read JSON file
        if output_file.exists():
            with open(output_file) as f:
                return json.load(f)

        return None

    except Exception as e:
        print(f"Jest JSON output failed: {e}")
        return None
    finally:
        # Cleanup
        output_file.unlink(missing_ok=True)
```

### pytest with JUnit XML

```python
def _run_pytest_with_xml(self, project_path: str) -> Optional[Dict]:
    """Run pytest with JUnit XML output."""
    xml_file = Path(project_path) / '.pytest-results.xml'

    try:
        cmd = ['pytest', f'--junitxml={xml_file}']
        subprocess.run(cmd, cwd=project_path, timeout=timeout)

        if xml_file.exists():
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Parse JUnit XML
            return {
                'total': int(root.attrib.get('tests', 0)),
                'failures': int(root.attrib.get('failures', 0)),
                'errors': int(root.attrib.get('errors', 0)),
                'skipped': int(root.attrib.get('skipped', 0)),
                'passed': int(root.attrib.get('tests', 0)) -
                         int(root.attrib.get('failures', 0)) -
                         int(root.attrib.get('errors', 0))
            }

        return None

    finally:
        xml_file.unlink(missing_ok=True)
```

### Go with JSON Lines

```python
def _run_go_test_with_json(self, project_path: str) -> Optional[Dict]:
    """Run go test with JSON output."""
    try:
        cmd = ['go', 'test', '-json', './...']
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Parse NDJSON (newline-delimited JSON)
        passed = 0
        failed = 0
        skipped = 0

        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
                if event.get('Action') == 'pass' and 'Test' in event:
                    passed += 1
                elif event.get('Action') == 'fail' and 'Test' in event:
                    failed += 1
                elif event.get('Action') == 'skip' and 'Test' in event:
                    skipped += 1
            except json.JSONDecodeError:
                continue

        return {
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': passed + failed + skipped
        }

    except Exception as e:
        print(f"Go JSON output failed: {e}")
        return None
```

## Migration Plan

### Phase 1: Add Structured Output (Backward Compatible)

```python
class LanguageAdapter:
    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run tests with structured output + fallback."""

        # Try structured first
        if structured_result := self._try_structured_output(project_path, strategy):
            return structured_result

        # Fallback to regex parsing (current implementation)
        return self._run_tests_with_regex(project_path, strategy)
```

### Phase 2: Prefer Structured, Keep Fallback

- Use structured output by default
- Log warning if falling back to regex
- Collect metrics on fallback usage

### Phase 3: Optional - Structured Only

- Once all projects use modern frameworks
- Remove regex fallback
- Fail fast if structured output unavailable

## Benefits

### Reliability
- ✅ No regex ambiguity
- ✅ Handles format changes
- ✅ Machine-readable

### Completeness
- ✅ Test durations
- ✅ Test names
- ✅ Error messages
- ✅ Stack traces

### Performance
- ✅ No regex compilation
- ✅ Fast JSON parsing
- ✅ Standard libraries

### Maintainability
- ✅ Standard formats
- ✅ Less code
- ✅ Easier debugging

## Challenges & Solutions

### Challenge: Jest --json mixes output

**Solution:** Use `--outputFile` to write clean JSON to file:
```bash
jest --json --outputFile=results.json
```

### Challenge: npm test adds wrapper output

**Solution:** Call jest directly:
```bash
npx jest --json --outputFile=results.json
```

### Challenge: Some projects don't have JSON support

**Solution:** Fallback hierarchy:
1. Try JSON
2. Try XML
3. Try TAP
4. Fall back to regex

### Challenge: Different JSON schemas per framework

**Solution:** Adapter pattern with framework-specific parsers:
```python
class JestParser:
    @staticmethod
    def parse(data: Dict) -> TestResult:
        return TestResult(
            passed=data['numPassedTests'],
            failed=data['numFailedTests'],
            ...
        )

class VitestParser:
    @staticmethod
    def parse(data: Dict) -> TestResult:
        results = data['testResults']
        return TestResult(
            passed=results['numPassedTests'],
            ...
        )
```

## See Also

- [Jest CLI Documentation](https://jestjs.io/docs/cli)
- [pytest Documentation](https://docs.pytest.org/)
- [Go test -json Format](https://golang.org/cmd/test2json/)
- [TAP Protocol](https://testanything.org/)
