#!/usr/bin/env python3
"""Find and categorize silent failures in the codebase.

Identifies exception handling patterns and categorizes by severity:
- CRITICAL: Setup/config errors that should fail fast
- WARNING: Should log but may continue
- INFO: Expected errors that can be skipped
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ExceptionPattern:
    """Represents an exception handling block."""
    file: str
    line: int
    except_clause: str
    handler_code: List[str]
    severity: str = "UNKNOWN"

    def __str__(self):
        return f"{self.severity:8} | {self.file}:{self.line} | {self.except_clause}"

def extract_handler_code(lines: List[str], start_idx: int) -> List[str]:
    """Extract the exception handler code block."""
    handler = []
    indent_level = None

    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        stripped = line.lstrip()

        if not stripped:
            continue

        # Calculate indent
        current_indent = len(line) - len(stripped)

        if indent_level is None:
            indent_level = current_indent
        elif current_indent < indent_level:
            # End of handler block
            break

        handler.append(stripped)

        if len(handler) > 10:  # Limit handler size
            break

    return handler

def categorize_exception(except_clause: str, handler_code: List[str], file_path: str) -> str:
    """Categorize exception by severity based on what's being caught and how it's handled."""
    handler_text = ' '.join(handler_code).lower()
    except_lower = except_clause.lower()

    # CRITICAL: Config/setup errors
    critical_patterns = [
        'import', 'module', 'config', 'install', 'not found',
        'runtime', 'configuration', 'setup', 'radon', 'pytest'
    ]

    # Check if it's being re-raised (good!)
    if 'raise' in handler_text and 'runtimeerror' in handler_text:
        return "OK"
    if 'raise' in handler_text and not 'raise ' in handler_text:  # bare raise
        return "OK"

    # Bare except or except Exception
    if except_clause.strip() in ['except:', 'except Exception:']:
        # Check handler
        if 'pass' in handler_text or 'continue' in handler_text:
            # Silent failure!
            for pattern in critical_patterns:
                if pattern in file_path.lower():
                    return "CRITICAL"
            return "WARNING"
        elif 'print' in handler_text or 'log' in handler_text:
            return "WARNING"
        else:
            return "WARNING"

    # Specific exceptions - usually OK
    specific_ok = [
        'json.jsondecodeerror', 'filenotfounderror', 'permissionerror',
        'timeout', 'keyerror', 'valueerror', 'indexerror', 'attributeerror'
    ]

    for ok_pattern in specific_ok:
        if ok_pattern in except_lower:
            return "INFO"

    # except Exception with specific handling
    if 'exception' in except_lower:
        if 'raise' in handler_text:
            return "OK"
        elif 'print' in handler_text or 'log' in handler_text:
            return "WARNING"
        else:
            return "CRITICAL"  # Silent broad exception catch!

    return "UNKNOWN"

def find_exceptions_in_file(file_path: Path) -> List[ExceptionPattern]:
    """Find all exception patterns in a file."""
    patterns = []

    try:
        lines = file_path.read_text().splitlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return patterns

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Match except clauses
        if stripped.startswith('except'):
            handler_code = extract_handler_code(lines, i - 1)

            # Get relative path safely
            try:
                rel_path = file_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = file_path

            pattern = ExceptionPattern(
                file=str(rel_path),
                line=i,
                except_clause=stripped,
                handler_code=handler_code
            )

            pattern.severity = categorize_exception(
                stripped, handler_code, str(file_path)
            )

            patterns.append(pattern)

    return patterns

def main():
    """Find and categorize all exception patterns."""
    root = Path('airflow_dags')

    all_patterns = []

    for py_file in root.rglob('*.py'):
        # Skip test fixtures
        if 'sample_' in str(py_file) or 'tmp_test' in str(py_file):
            continue

        patterns = find_exceptions_in_file(py_file)
        all_patterns.extend(patterns)

    # Group by severity
    by_severity = defaultdict(list)
    for pattern in all_patterns:
        by_severity[pattern.severity].append(pattern)

    # Print summary
    print(f"\n{'='*100}")
    print(f"EXCEPTION HANDLING ANALYSIS - {len(all_patterns)} patterns found")
    print(f"{'='*100}\n")

    severity_order = ['CRITICAL', 'WARNING', 'UNKNOWN', 'INFO', 'OK']

    for severity in severity_order:
        patterns = by_severity.get(severity, [])
        if not patterns:
            continue

        print(f"\n{severity} ({len(patterns)}):")
        print("-" * 100)

        for pattern in patterns[:15]:  # Limit output
            print(f"  {pattern}")
            if severity == "CRITICAL":
                print(f"    Handler: {' '.join(pattern.handler_code[:3])}...")

        if len(patterns) > 15:
            print(f"  ... and {len(patterns) - 15} more")

    # Export to file
    with open('claudedocs/silent-failures-report.txt', 'w') as f:
        f.write(f"EXCEPTION HANDLING ANALYSIS\n")
        f.write(f"Generated: {Path.cwd()}\n\n")

        for severity in severity_order:
            patterns = by_severity.get(severity, [])
            if not patterns:
                continue

            f.write(f"\n{severity} ({len(patterns)}):\n")
            f.write("-" * 100 + "\n")

            for pattern in patterns:
                f.write(f"{pattern}\n")
                if severity in ['CRITICAL', 'WARNING']:
                    f.write(f"  Handler: {' '.join(pattern.handler_code)}\n")

    print(f"\n\nFull report saved to: claudedocs/silent-failures-report.txt")

    # Return exit code based on findings
    critical_count = len(by_severity.get('CRITICAL', []))
    if critical_count > 0:
        print(f"\n⚠️  Found {critical_count} CRITICAL silent failures that need fixing!")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
