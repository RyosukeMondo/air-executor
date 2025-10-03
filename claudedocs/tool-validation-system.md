# Tool Validation System - Complete Implementation

## Overview

Pre-flight tool validation system that detects missing tools **before** autonomous fixing runs, providing clear error messages and fix suggestions.

**Problem Solved**: Prevent silent failures from missing tools (like Flutter not in PATH)

## Architecture

### **Components**

1. **ToolValidationResult** (base.py) - Data class for tool check results
2. **validate_tools()** (LanguageAdapter) - Interface method all adapters must implement
3. **ToolValidator** (tool_validator.py) - Orchestrates validation across all adapters
4. **Pre-flight Check** (multi_language_orchestrator.py) - Runs before autonomous fixing

---

## Implementation

### **1. Base Interface** (`language_adapters/base.py`)

```python
@dataclass
class ToolValidationResult:
    """Result of tool validation check."""
    tool_name: str
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error_message: Optional[str] = None
    fix_suggestion: Optional[str] = None
```

**Abstract Method** all adapters must implement:
```python
@abstractmethod
def validate_tools(self) -> List[ToolValidationResult]:
    """Validate all required tools are available."""
    pass
```

### **2. Flutter Implementation** (`language_adapters/flutter_adapter.py`)

**Validates**:
- `flutter` - Main Flutter SDK
- `dart` - Dart SDK (usually with Flutter)
- `flutter analyze` - Static analysis tool
- `flutter test` - Test runner

**Example Output**:
```python
results = adapter.validate_tools()
# [
#   ToolValidationResult(
#     tool_name='flutter',
#     available=True,
#     version='3.35.5',
#     path='/home/user/flutter/bin/flutter'
#   ),
#   ...
# ]
```

**Methods**:
- `_validate_flutter()` - Check Flutter installation + version
- `_validate_dart()` - Check Dart installation + version
- `_find_flutter_executable()` - Search PATH + common locations

### **3. Tool Validator** (`core/tool_validator.py`)

**Orchestrates** validation across all language adapters.

**Key Method**:
```python
def validate_all_tools(self) -> ValidationSummary:
    """
    Validate all tools for all language adapters.

    Returns:
        ValidationSummary with:
        - total_tools: int
        - available_tools: int
        - missing_tools: int
        - can_proceed: bool
        - fix_suggestions: List[str]
    """
```

**Logic**:
```python
# For each language
for lang_name, adapter in self.adapters.items():
    results = adapter.validate_tools()

    for result in results:
        if result.available:
            print(f"✅ {result.tool_name} (v{result.version})")
        else:
            print(f"❌ {result.tool_name} - NOT FOUND")
            print(f"   💡 {result.fix_suggestion}")

# Determine if can proceed
can_proceed = self._determine_can_proceed(all_results)
```

**Can Proceed Logic**:
- MUST have: Static analysis tool (flutter analyze, eslint, pylint)
- OPTIONAL: Test tool (falls back to file counting)
- OPTIONAL: Coverage, E2E tools

### **4. Orchestrator Integration** (`multi_language_orchestrator.py`)

**Pre-flight Check** added to `execute()`:

```python
def execute(self) -> Dict:
    # === PRE-FLIGHT: Tool Validation ===
    tool_validator = ToolValidator(self.adapters, self.config)
    validation_summary = tool_validator.validate_all_tools()

    if not validation_summary.can_proceed:
        print("\n❌ Cannot proceed - missing critical tools")
        return {
            'success': False,
            'error': 'Missing critical tools',
            'validation': validation_summary
        }

    # Continue with autonomous fixing...
```

---

## Example Output

### **All Tools Available** ✅

```
================================================================================
🔧 TOOL VALIDATION
================================================================================

📋 Validating FLUTTER toolchain...
   ✅ flutter (v3.35.5) @ /home/rmondo/flutter/bin/flutter
   ✅ dart (v3.9.2) @ /home/rmondo/flutter/bin/dart
   ✅ flutter analyze (v3.35.5) @ /home/rmondo/flutter/bin/flutter
   ✅ flutter test (v3.35.5) @ /home/rmondo/flutter/bin/flutter

================================================================================
📊 VALIDATION SUMMARY
================================================================================
Total tools checked: 4
Available: 4 ✅
Missing: 0 ❌

✅ All critical tools available - can proceed
================================================================================
```

### **Missing Tools** ❌

```
================================================================================
🔧 TOOL VALIDATION
================================================================================

📋 Validating FLUTTER toolchain...
   ❌ flutter - NOT FOUND
      💡 Install Flutter: https://docs.flutter.dev/get-started/install
      Or add to PATH: export PATH=$HOME/flutter/bin:$PATH
   ❌ dart - NOT FOUND
      💡 Dart usually comes with Flutter. Check: flutter doctor
   ❌ flutter analyze - NOT FOUND
      💡 Install Flutter: https://docs.flutter.dev/get-started/install
   ❌ flutter test - NOT FOUND
      💡 Install Flutter: https://docs.flutter.dev/get-started/install

================================================================================
📊 VALIDATION SUMMARY
================================================================================
Total tools checked: 4
Available: 0 ✅
Missing: 4 ❌

❌ Missing critical tools - cannot proceed

🔧 FIXES NEEDED:
   1. flutter: Install Flutter: https://docs.flutter.dev/get-started/install
   2. dart: Dart usually comes with Flutter. Check: flutter doctor
================================================================================

❌ Cannot proceed - missing critical tools
   Please install required tools and try again
```

---

## Usage

### **Standalone Tool Check**

```bash
# Check Flutter tools
python -c "
from airflow_dags.autonomous_fixing.language_adapters import FlutterAdapter
adapter = FlutterAdapter({})
results = adapter.validate_tools()

for result in results:
    status = '✅' if result.available else '❌'
    print(f'{status} {result.tool_name}')
    if result.version:
        print(f'   Version: {result.version}')
"
```

### **Integrated (Automatic)**

Tool validation runs automatically when you start autonomous fixing:

```bash
python airflow_dags/autonomous_fixing/multi_language_orchestrator.py \
  config/projects/money-making-app.yaml
```

**Output includes**:
1. Tool validation section
2. Either "✅ can proceed" or "❌ cannot proceed"
3. If cannot proceed → Lists fix suggestions → Exits early

---

## Benefits

### **1. Early Detection**
- Catches missing tools **before** wasting time
- No more "0/0 tests" silent failures
- Clear error messages immediately

### **2. Helpful Errors**
```
❌ flutter - NOT FOUND
   💡 Install Flutter: https://docs.flutter.dev/get-started/install
   Or add to PATH: export PATH=$HOME/flutter/bin:$PATH
```

### **3. Version Information**
```
✅ flutter (v3.35.5) @ /home/rmondo/flutter/bin/flutter
```
- Know exactly what version is installed
- Debug version-specific issues
- Verify tool paths

### **4. Smart Fallbacks**
- Test tool missing? → Fall back to filesystem counting (133 tests)
- Graceful degradation instead of complete failure

---

## Extending to Other Languages

### **Template for Python Adapter**

```python
def validate_tools(self) -> List[ToolValidationResult]:
    """Validate Python toolchain."""
    results = []

    # 1. Python itself
    results.append(self._validate_python())

    # 2. Linters
    results.append(self._validate_pylint())
    results.append(self._validate_mypy())

    # 3. Test runner
    results.append(self._validate_pytest())

    # 4. Coverage tool
    results.append(self._validate_coverage())

    return results

def _validate_python(self) -> ToolValidationResult:
    """Check Python installation."""
    try:
        result = subprocess.run(
            ['python', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        version_match = re.search(r'Python ([\d.]+)', result.stdout)
        version = version_match.group(1) if version_match else 'unknown'

        return ToolValidationResult(
            tool_name='python',
            available=True,
            version=version,
            path=shutil.which('python')
        )
    except Exception as e:
        return ToolValidationResult(
            tool_name='python',
            available=False,
            error_message=str(e),
            fix_suggestion='Install Python: https://python.org'
        )
```

### **Template for JavaScript Adapter**

```python
def validate_tools(self) -> List[ToolValidationResult]:
    """Validate JavaScript toolchain."""
    results = []

    # 1. Node.js
    results.append(self._validate_node())

    # 2. npm/yarn
    results.append(self._validate_npm())

    # 3. ESLint
    results.append(self._validate_eslint())

    # 4. Jest/Mocha (test runner)
    results.append(self._validate_test_runner())

    return results
```

---

## Files Modified/Created

### **Modified**
- `airflow_dags/autonomous_fixing/language_adapters/base.py` (+17 lines)
  - Added `ToolValidationResult` dataclass
  - Added `validate_tools()` abstract method

- `airflow_dags/autonomous_fixing/language_adapters/flutter_adapter.py` (+138 lines)
  - Implemented `validate_tools()`
  - Added `_validate_flutter()`
  - Added `_validate_dart()`

- `airflow_dags/autonomous_fixing/multi_language_orchestrator.py` (+15 lines)
  - Added pre-flight tool validation
  - Early exit if tools missing

- `airflow_dags/autonomous_fixing/core/__init__.py` (+2 lines)
  - Exported `ToolValidator`

### **Created**
- `airflow_dags/autonomous_fixing/core/tool_validator.py` (330 lines)
  - Complete tool validation orchestrator
  - Standalone utility mode

---

## Testing

### **Verify Flutter Tools**
```bash
python -c "
from airflow_dags.autonomous_fixing.language_adapters import FlutterAdapter
adapter = FlutterAdapter({})
results = adapter.validate_tools()
print(f'Validated {len(results)} tools')
print(f'Available: {sum(1 for r in results if r.available)}')
"
```

**Expected**: 4 tools, all available ✅

### **Run Full Validation**
```bash
python airflow_dags/autonomous_fixing/multi_language_orchestrator.py \
  config/projects/money-making-app.yaml
```

**Expected Output**:
```
🔧 TOOL VALIDATION
📋 Validating FLUTTER toolchain...
   ✅ flutter (v3.35.5)
   ✅ dart (v3.9.2)
   ✅ flutter analyze
   ✅ flutter test
✅ All critical tools available - can proceed
```

---

## Future Enhancements

### **1. Tool Installation Helpers**
```python
def install_flutter() -> bool:
    """Guide user through Flutter installation."""
    print("Installing Flutter:")
    print("1. Download: https://flutter.dev/docs/get-started/install")
    print("2. Extract to: $HOME/flutter")
    print("3. Add to PATH: export PATH=$HOME/flutter/bin:$PATH")

    # Could automate on some platforms
    if platform.system() == 'Linux':
        subprocess.run(['snap', 'install', 'flutter', '--classic'])
```

### **2. Auto-fix Common Issues**
```python
def auto_fix_path_issues(self) -> bool:
    """Auto-add tools to PATH."""
    flutter_dir = Path.home() / 'flutter' / 'bin'
    if flutter_dir.exists():
        # Add to current session
        os.environ['PATH'] = f"{flutter_dir}:{os.environ['PATH']}"

        # Suggest permanent fix
        print(f"💡 Add to ~/.bashrc:")
        print(f"   export PATH=$HOME/flutter/bin:$PATH")
        return True
    return False
```

### **3. Version Compatibility Checks**
```python
def check_version_compatibility(self, required_version: str) -> bool:
    """Check if installed version meets requirements."""
    current = self._get_version()
    required = parse_version(required_version)
    return parse_version(current) >= required
```

---

## Summary

**Built**: Complete tool validation system with pre-flight checks

**Validates**:
- ✅ Flutter SDK (v3.35.5)
- ✅ Dart SDK (v3.9.2)
- ✅ flutter analyze
- ✅ flutter test

**Prevents**:
- ❌ Silent failures from missing tools
- ❌ Wasted API calls
- ❌ Confusing "0/0 tests" errors

**Provides**:
- ✅ Clear error messages
- ✅ Fix suggestions with links
- ✅ Version information
- ✅ Early exit when tools missing

**Next**: Implement for Python, JavaScript, Go adapters using same template.
