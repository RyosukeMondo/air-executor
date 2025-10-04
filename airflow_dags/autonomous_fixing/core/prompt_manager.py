"""
Prompt Manager - Centralized prompt loading and building.

Handles loading prompts from YAML config and building prompt strings.
"""

from pathlib import Path

import yaml

from ..config.prompt_manager_config import PromptManagerConfig


class PromptManager:
    """Manages prompt templates and configuration."""

    def __init__(self, config: PromptManagerConfig | None = None):
        """Initialize prompt manager and load prompts from config.

        Args:
            config: Optional PromptManagerConfig. If not provided, uses default path.
        """
        self.config = config or PromptManagerConfig()
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> dict:
        """Load prompts from centralized config file."""
        # First try the configured path
        if self.config.prompts_config_path.exists():
            with open(self.config.prompts_config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)

        # Fallback: Try to find prompts.yaml in standard locations
        possible_paths = [
            Path(__file__).parent.parent.parent / "config" / "prompts.yaml",  # From core/
            Path("config/prompts.yaml"),  # From project root
            Path(__file__).parent.parent / "config" / "prompts.yaml",  # Alternative
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    return yaml.safe_load(f)

        # Fallback: return minimal default prompts if config not found
        print("⚠️  Warning: prompts.yaml not found, using fallback prompts")
        return self._get_fallback_prompts()

    def _get_fallback_prompts(self) -> dict:
        """Return fallback prompts if config file not found."""
        return {
            "static_issues": {
                "error": {"template": "Fix this {language} error in {file}:\n{message}"},
                "complexity": {
                    "template": (
                        "Refactor {file} to reduce complexity "
                        "from {complexity} to below {threshold}"
                    )
                },
            },
            "tests": {
                "fix_failures": {
                    "template": "Fix failing {language} tests. {failed}/{total} tests failing."
                },
                "create_tests": {
                    "template": "This {language} project has NO TESTS. Create initial test suite."
                },
            },
            "analysis": {
                "static_analysis": {
                    "template": "Analyze {language} code quality for {project_name}"
                }
            },
            "setup": {
                "configure_precommit_hooks": {
                    "template": (
                        "Configure pre-commit hooks for {language} " "project {project_name}"
                    )
                },
                "discover_tests": {
                    "template": (
                        "Discover test configuration for {language} "
                        "project {project_name} at {project_path}"
                    )
                },
            },
            "timeouts": {
                "fix_static_issue": 300,
                "fix_test_failure": 600,
                "create_tests": 900,
                "analyze_static": 300,
                "configure_hooks": 600,
                "discover_tests": 600,
            },
        }

    def build_error_prompt(self, issue: dict) -> str:
        """Build prompt for fixing an error."""
        template = self.prompts["static_issues"]["error"]["template"]
        return template.format(
            language=issue["language"], file=issue["file"], message=issue["message"]
        )

    def build_complexity_prompt(self, issue: dict) -> str:
        """Build prompt for fixing complexity."""
        template = self.prompts["static_issues"]["complexity"]["template"]
        return template.format(
            file=issue["file"], complexity=issue["complexity"], threshold=issue["threshold"]
        )

    def build_test_failure_prompt(self, test_info: dict) -> str:
        """Build prompt for fixing test failures."""
        template = self.prompts["tests"]["fix_failures"]["template"]
        return template.format(
            language=test_info["language"], failed=test_info["failed"], total=test_info["total"]
        )

    def build_create_tests_prompt(self, project_info: dict) -> str:
        """Build prompt for creating tests."""
        template = self.prompts["tests"]["create_tests"]["template"]
        prompt = template.format(language=project_info["language"])

        # Check for language-specific framework hints
        lang_overrides = self.prompts.get("language_overrides", {}).get(
            project_info["language"], {}
        )
        if "create_tests" in lang_overrides and "framework_hint" in lang_overrides["create_tests"]:
            prompt += f"\n\nFramework tip: {lang_overrides['create_tests']['framework_hint']}"

        return prompt

    def build_static_analysis_prompt(self, language: str, project_name: str) -> str:
        """Build prompt for static analysis."""
        template = self.prompts["analysis"]["static_analysis"]["template"]
        return template.format(
            language=language, project_name=project_name, timestamp="$(date -Iseconds)"
        )

    def build_configure_hooks_prompt(self, language: str, project_name: str) -> str:
        """Build prompt for configuring pre-commit hooks."""
        template = self.prompts["setup"]["configure_precommit_hooks"]["template"]
        return template.format(language=language, project_name=project_name)

    def build_discover_tests_prompt(
        self, language: str, project_name: str, project_path: str
    ) -> str:
        """Build prompt for discovering test configuration."""
        template = self.prompts["setup"]["discover_tests"]["template"]
        return template.format(
            language=language,
            project_name=project_name,
            project_path=project_path,
            timestamp="$(date -Iseconds)",
        )

    def get_timeout(self, operation: str) -> int:
        """Get timeout for a specific operation."""
        return self.prompts.get("timeouts", {}).get(operation, 300)
