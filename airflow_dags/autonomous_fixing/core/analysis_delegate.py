"""
Analysis Delegate - Handles analysis and setup operations.

Delegates analysis and configuration tasks to Claude.
"""

import time
from pathlib import Path

import yaml

from ..adapters.ai.claude_client import ClaudeClient
from ..config.analysis_delegate_config import AnalysisDelegateConfig
from ..domain.models import FixResult
from .prompt_manager import PromptManager


class AnalysisDelegate:
    """Delegates analysis and setup operations to Claude."""

    def __init__(
        self,
        config: dict,
        debug_logger=None,
        delegate_config: AnalysisDelegateConfig | None = None,
    ):
        """
        Initialize analysis delegate.

        Args:
            config: Configuration dict with wrapper settings (backward compat)
            debug_logger: Optional DebugLogger instance
            delegate_config: Optional AnalysisDelegateConfig for paths
        """
        self.config = config
        self.delegate_config = delegate_config or AnalysisDelegateConfig()

        # Get wrapper settings from delegate_config or fallback to config dict
        wrapper_settings = self.delegate_config.wrapper_settings
        wrapper_path = config.get("wrapper", {}).get("path", wrapper_settings["path"])
        python_exec = config.get("wrapper", {}).get(
            "python_executable", wrapper_settings["python_executable"]
        )

        # Initialize Claude client
        self.claude = ClaudeClient(wrapper_path, python_exec, debug_logger)

        # Initialize prompt manager
        self.prompt_manager = PromptManager()

    def analyze_static(self, project_path: str, language: str) -> dict:
        """
        ANALYSIS PHASE: Static code quality analysis via claude_wrapper.

        Delegates to claude_wrapper to:
        1. Run linters/analyzers (eslint, pylint, flutter analyze, etc.)
        2. Analyze errors, warnings, complexity, file sizes
        3. Assess overall health with reasoning
        4. Save structured report to config/analysis-cache/

        Args:
            project_path: Path to project
            language: Project language

        Returns: Dict with analysis results (from YAML)
        """
        project_name = Path(project_path).name
        cache_path = self.delegate_config.analysis_cache_dir / f"{project_name}-static.yaml"

        # Check if recently analyzed (< 5 min old)
        if cache_path.exists():
            age_seconds = time.time() - cache_path.stat().st_mtime
            if age_seconds < 300:  # 5 minutes
                print(f"   ✓ Using cached analysis ({int(age_seconds)}s old)")
                with open(cache_path, encoding="utf-8") as f:
                    return yaml.safe_load(f)

        print(f"\n🔍 Analyzing {project_name} static code quality...")

        # Build prompt
        prompt = self.prompt_manager.build_static_analysis_prompt(language, project_name)

        # Get timeout
        timeout = self.prompt_manager.get_timeout("analyze_static")

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, project_path, timeout, prompt_type="analysis")

        if result["success"] and cache_path.exists():
            print(f"   ✓ Analysis complete, saved to {cache_path}")
            with open(cache_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            error_msg = result.get("error_message") or result.get("error", "Unknown error")
            print(f"   ✗ Analysis failed: {error_msg}")
            # Return empty analysis
            return {
                "health": {"overall_score": 0.0},
                "errors": {"count": 0},
                "warnings": {"count": 0},
            }

    def configure_precommit_hooks(self, project_path: str, language: str) -> bool:
        """
        SETUP PHASE: Configure pre-commit hooks for quality enforcement.

        This shifts quality gates from AI prompts to enforced tooling:
        - AI configures hooks once
        - Hooks enforce quality on every commit
        - AI cannot bypass hooks (must fix issues)

        Args:
            project_path: Path to project
            language: Project language

        Returns: True if hooks configured successfully
        """
        project_name = Path(project_path).name
        cache_path = self.delegate_config.hook_cache_dir / f"{project_name}-hooks.yaml"

        # Ensure cache directory exists
        self.delegate_config.hook_cache_dir.mkdir(parents=True, exist_ok=True)

        # Check if already configured (< 7 days old)
        if cache_path.exists():
            age_seconds = time.time() - cache_path.stat().st_mtime
            if age_seconds < 604800:  # 7 days
                print(
                    f"   ✓ Pre-commit hooks already configured ({int(age_seconds/86400)} days ago)"
                )
                with open(cache_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    return config.get("hook_framework", {}).get("installed", False)

        print(f"\n🔧 Configuring pre-commit hooks for {project_name}...")

        # Build prompt
        prompt = self.prompt_manager.build_configure_hooks_prompt(language, project_name)

        # Get timeout
        timeout = self.prompt_manager.get_timeout("configure_hooks")

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, project_path, timeout, prompt_type="configure_hooks")

        if result["success"] and cache_path.exists():
            print(f"   ✓ Pre-commit hooks configured and saved to {cache_path}")
            return True
        if result["success"] and not cache_path.exists():
            # Wrapper succeeded but didn't create cache file
            # (likely timeout without completion event)
            error_msg = "Wrapper completed but output file not created (possible timeout)"
            print(f"   ⚠️  Hook configuration failed: {error_msg}")
            print("   Continuing without pre-commit enforcement (less robust)")
            return False
        error_msg = result.get("error_message") or result.get("error", "Unknown error")
        print(f"   ⚠️  Hook configuration failed: {error_msg}")
        print("   Continuing without pre-commit enforcement (less robust)")
        return False

    def discover_test_config(self, project_path: str, language: str) -> FixResult:
        """
        SETUP PHASE: Discover how to run tests for this project.

        Delegates to claude_wrapper to:
        1. Analyze project structure
        2. Detect package manager, test framework, test locations
        3. Try running tests to verify
        4. Save discovered config to config/test-cache/

        Args:
            project_path: Path to project
            language: Project language

        Returns: FixResult with stats
        """
        project_name = Path(project_path).name
        cache_path = self.delegate_config.test_cache_dir / f"{project_name}-tests.yaml"

        # Check if already discovered
        if cache_path.exists():
            print(f"   ✓ Test config already exists: {cache_path}")
            return FixResult(success=False)  # No discovery needed

        print(f"\n🔍 SETUP: Discovering test configuration for {project_name}...")

        # Build prompt
        prompt = self.prompt_manager.build_discover_tests_prompt(
            language, project_name, project_path
        )

        # Get timeout
        timeout = self.prompt_manager.get_timeout("discover_tests")

        # Call Claude via JSON protocol
        result = self.claude.query(prompt, project_path, timeout, prompt_type="discover_tests")

        if result["success"] and cache_path.exists():
            print(f"   ✓ Test config discovered and saved to {cache_path}")
            return FixResult(fixes_applied=1, fixes_attempted=1, success=True)
        error_msg = result.get("error_message") or result.get("error", "Unknown error")
        print(f"   ✗ Test discovery failed: {error_msg}")
        return FixResult(fixes_applied=0, fixes_attempted=1, success=False)
