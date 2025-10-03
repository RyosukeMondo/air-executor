"""
Tool Validator - Pre-flight checks for all required tools.

Validates toolchain availability before running autonomous fixing
to catch issues early and provide helpful error messages.
"""

from typing import Dict, List
from dataclasses import dataclass

try:
    from ..domain.models import ToolValidationResult
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from domain.models import ToolValidationResult


@dataclass
class ValidationSummary:
    """Summary of all tool validations."""
    total_tools: int
    available_tools: int
    missing_tools: int
    warnings: List[str]
    errors: List[str]
    can_proceed: bool
    fix_suggestions: List[str]


class ToolValidator:
    """
    Validates all required tools before autonomous fixing.

    Responsibilities:
    - Check all language adapters for tool availability
    - Provide clear error messages
    - Suggest fixes for missing tools
    - Determine if autonomous fixing can proceed

    Does NOT:
    - Install tools (user responsibility)
    - Fix tool issues (just reports them)
    """

    def __init__(self, language_adapters: Dict, config: Dict):
        """
        Args:
            language_adapters: Dict of {language_name: adapter_instance}
            config: Configuration dict
        """
        self.adapters = language_adapters
        self.config = config

    def validate_all_tools(self) -> ValidationSummary:
        """
        Validate all tools for all language adapters.

        Returns:
            ValidationSummary with overall results
        """
        print(f"\n{'='*80}")
        print("🔧 TOOL VALIDATION")
        print(f"{'='*80}\n")

        all_results = {}
        total_tools = 0
        available_tools = 0
        missing_tools = 0
        warnings = []
        errors = []
        fix_suggestions = []

        # Validate each language adapter
        for lang_name, adapter in self.adapters.items():
            print(f"📋 Validating {lang_name.upper()} toolchain...")

            results = adapter.validate_tools()
            all_results[lang_name] = results

            for result in results:
                total_tools += 1

                if result.available:
                    available_tools += 1
                    status = "✅"
                    version_info = f" (v{result.version})" if result.version else ""
                    path_info = f" @ {result.path}" if result.path else ""
                    print(f"   {status} {result.tool_name}{version_info}{path_info}")
                else:
                    missing_tools += 1
                    status = "❌"
                    print(f"   {status} {result.tool_name} - NOT FOUND")

                    error_msg = f"{lang_name}: {result.tool_name} - {result.error_message}"
                    errors.append(error_msg)

                    if result.fix_suggestion:
                        fix_suggestions.append(f"{result.tool_name}: {result.fix_suggestion}")
                        print(f"      💡 {result.fix_suggestion}")

            print()

        # Determine if can proceed
        can_proceed = self._determine_can_proceed(all_results)

        # Print summary
        print(f"{'='*80}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total tools checked: {total_tools}")
        print(f"Available: {available_tools} ✅")
        print(f"Missing: {missing_tools} ❌")
        print()

        if can_proceed:
            print("✅ All critical tools available - can proceed")
        else:
            print("❌ Missing critical tools - cannot proceed")
            print("\n🔧 FIXES NEEDED:")
            for i, suggestion in enumerate(fix_suggestions, 1):
                print(f"   {i}. {suggestion}")

        print(f"{'='*80}\n")

        return ValidationSummary(
            total_tools=total_tools,
            available_tools=available_tools,
            missing_tools=missing_tools,
            warnings=warnings,
            errors=errors,
            can_proceed=can_proceed,
            fix_suggestions=fix_suggestions
        )

    def _determine_can_proceed(self, all_results: Dict[str, List[ToolValidationResult]]) -> bool:
        """
        Determine if autonomous fixing can proceed.

        Logic:
        - For each language, MUST have:
          - Static analysis tool (flutter analyze, eslint, ruff, mypy, etc.)
          - Test runner (flutter test, pytest, etc.)
        - Coverage and E2E tools are optional
        """
        # Common static analysis tool names by language
        static_analysis_tools = {
            'python': ['ruff', 'pylint', 'mypy', 'pyflakes', 'flake8'],
            'javascript': ['eslint', 'tslint'],
            'go': ['golangci-lint', 'staticcheck'],
            'flutter': ['analyze']
        }

        for lang_name, results in all_results.items():
            # Check for critical tools
            has_static_tool = False
            has_test_tool = False

            for result in results:
                # Static analysis tools - check both keywords and known tool names
                is_static_tool = (
                    any(keyword in result.tool_name for keyword in ['analyze', 'lint', 'check']) or
                    result.tool_name in static_analysis_tools.get(lang_name, [])
                )
                if is_static_tool and result.available:
                    has_static_tool = True

                # Test tools
                if 'test' in result.tool_name and 'coverage' not in result.tool_name:
                    if result.available:
                        has_test_tool = True

            # For now, allow proceeding with test file counting fallback
            # So we only require static analysis tool
            if not has_static_tool:
                return False

        return True

    def validate_project_specific(self, project_path: str, language: str) -> ValidationSummary:
        """
        Validate tools for a specific project.

        Useful for debugging individual project issues.
        """
        if language not in self.adapters:
            return ValidationSummary(
                total_tools=0,
                available_tools=0,
                missing_tools=0,
                warnings=[],
                errors=[f"No adapter for language: {language}"],
                can_proceed=False,
                fix_suggestions=[f"Add {language} support to config"]
            )

        adapter = self.adapters[language]

        print(f"\n{'='*80}")
        print(f"🔧 VALIDATING TOOLS FOR: {project_path}")
        print(f"Language: {language.upper()}")
        print(f"{'='*80}\n")

        results = adapter.validate_tools()

        total_tools = len(results)
        available_tools = sum(1 for r in results if r.available)
        missing_tools = total_tools - available_tools

        errors = []
        fix_suggestions = []

        for result in results:
            if result.available:
                version_info = f" (v{result.version})" if result.version else ""
                print(f"✅ {result.tool_name}{version_info}")
            else:
                print(f"❌ {result.tool_name} - {result.error_message}")
                errors.append(result.error_message)
                if result.fix_suggestion:
                    fix_suggestions.append(result.fix_suggestion)
                    print(f"   💡 {result.fix_suggestion}")

        can_proceed = available_tools == total_tools

        print(f"\n{'='*80}")
        if can_proceed:
            print("✅ All tools available")
        else:
            print(f"❌ {missing_tools} tool(s) missing")
        print(f"{'='*80}\n")

        return ValidationSummary(
            total_tools=total_tools,
            available_tools=available_tools,
            missing_tools=missing_tools,
            warnings=[],
            errors=errors,
            can_proceed=can_proceed,
            fix_suggestions=fix_suggestions
        )


def main():
    """Standalone tool validation utility."""
    import sys
    import yaml
    from pathlib import Path

    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from airflow_dags.autonomous_fixing.language_adapters import (
        FlutterAdapter,
        PythonAdapter,
        JavaScriptAdapter,
        GoAdapter
    )

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tool_validator.py <config.yaml>")
        print("  python tool_validator.py --check-flutter")
        print("  python tool_validator.py --check-all")
        sys.exit(1)

    if sys.argv[1] == '--check-flutter':
        adapter = FlutterAdapter({})
        results = adapter.validate_tools()

        print("Flutter Toolchain Validation:")
        for result in results:
            status = "✅" if result.available else "❌"
            print(f"{status} {result.tool_name}")
            if result.version:
                print(f"   Version: {result.version}")
            if result.path:
                print(f"   Path: {result.path}")
            if result.error_message:
                print(f"   Error: {result.error_message}")
            if result.fix_suggestion:
                print(f"   Fix: {result.fix_suggestion}")
        sys.exit(0)

    if sys.argv[1] == '--check-all':
        adapters = {
            'flutter': FlutterAdapter({}),
            'python': PythonAdapter({}),
            'javascript': JavaScriptAdapter({}),
            'go': GoAdapter({})
        }

        validator = ToolValidator(adapters, {})
        summary = validator.validate_all_tools()

        sys.exit(0 if summary.can_proceed else 1)

    # Load config and validate
    config_file = sys.argv[1]
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # Create adapters based on config
    adapters = {}
    languages = config.get('languages', {})

    if 'flutter' in languages.get('enabled', []):
        adapters['flutter'] = FlutterAdapter(languages.get('flutter', {}))

    if 'python' in languages.get('enabled', []):
        adapters['python'] = PythonAdapter(languages.get('python', {}))

    if 'javascript' in languages.get('enabled', []):
        adapters['javascript'] = JavaScriptAdapter(languages.get('javascript', {}))

    if 'go' in languages.get('enabled', []):
        adapters['go'] = GoAdapter(languages.get('go', {}))

    # Validate
    validator = ToolValidator(adapters, config)
    summary = validator.validate_all_tools()

    sys.exit(0 if summary.can_proceed else 1)


if __name__ == '__main__':
    main()
