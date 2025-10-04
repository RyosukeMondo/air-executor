"""
Multi-Language Autonomous Fixing Orchestrator - THIN COORDINATOR

Following SOLID principles - this orchestrator ONLY coordinates, no business logic.
All actual work is delegated to specialized modules:
- ProjectAnalyzer: runs analysis
- IssueFixer: fixes issues
- HealthScorer: calculates scores
- IterationEngine: manages iteration loop
"""

import sys
from pathlib import Path

import yaml

# Import configuration
try:
    from .config import OrchestratorConfig
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import OrchestratorConfig

# Import language adapters (from new location)
try:
    from .adapters.languages import FlutterAdapter, GoAdapter, JavaScriptAdapter, PythonAdapter
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from adapters.languages import FlutterAdapter, GoAdapter, JavaScriptAdapter, PythonAdapter

# Import clean core modules
try:
    from .core import HealthScorer, IssueFixer, IterationEngine, ProjectAnalyzer, ToolValidator
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from core import HealthScorer, IssueFixer, IterationEngine, ProjectAnalyzer
    from core.tool_validator import ToolValidator


class MultiLanguageOrchestrator:
    """
    Thin coordinator that delegates to specialized modules.

    Responsibilities (ONLY coordination, no business logic):
    - Initialize language adapters
    - Get project list from config
    - Create analyzer, fixer, scorer, iteration_engine
    - Start iteration_engine
    - Return results

    Does NOT:
    - Analyze code (delegates to ProjectAnalyzer)
    - Fix issues (delegates to IssueFixer)
    - Calculate scores (delegates to HealthScorer)
    - Manage iterations (delegates to IterationEngine)
    """

    def __init__(
        self,
        config: OrchestratorConfig | dict,
        project_name: str = "multi-project",
    ):
        """
        Args:
            config: Configuration (OrchestratorConfig or dict for backward compatibility)
            project_name: Project name for logging
        """
        # Support both OrchestratorConfig and dict (backward compatibility)
        if isinstance(config, dict):
            self.orchestrator_config = OrchestratorConfig.from_dict(config)
        else:
            self.orchestrator_config = config

        # Keep config as dict for now (until all components are updated)
        self.config = config if isinstance(config, dict) else self.orchestrator_config.to_dict()
        self.project_name = project_name

        # Initialize language adapters (SRP: each adapter handles one language)
        self.adapters = self._create_language_adapters()

        # Initialize core modules (SRP: each module has one job)
        # Use self.config (dict) for components until they're updated
        self.analyzer = ProjectAnalyzer(self.adapters, self.config)
        self.fixer = IssueFixer(self.config)
        self.scorer = HealthScorer(self.config)

        # Create iteration engine with dependency injection
        # Pass config first (new signature), then inject all dependencies
        self.iteration_engine = IterationEngine(
            config=self.config,
            analyzer=self.analyzer,
            fixer=self.fixer,
            scorer=self.scorer,
            hook_manager=None,  # Will use default HookLevelManager
            project_name=project_name,
        )

    def execute(self) -> dict:
        """
        Execute autonomous fixing - just coordinate, don't do the work.

        Returns: Results dict from iteration_engine
        """
        print(f"\n{'='*80}")
        print("🚀 Multi-Language Autonomous Fixing")
        print(f"{'='*80}")
        print(f"Languages enabled: {', '.join(self.adapters.keys())}")
        print(f"{'='*80}\n")

        # === PRE-FLIGHT: Tool Validation ===
        tool_validator = ToolValidator(self.adapters, self.config)
        validation_summary = tool_validator.validate_all_tools()

        if not validation_summary.can_proceed:
            print("\n❌ Cannot proceed - missing critical tools")
            print("   Please install required tools and try again\n")
            return {
                "success": False,
                "error": "Missing critical tools",
                "validation": validation_summary,
            }

        # Get projects (explicit list from config)
        if "projects" in self.config:
            print("Using explicit project list from config\n")
            projects_by_language = self._get_projects_from_config()
        else:
            print("❌ No projects list in config")
            return {"success": False, "error": "No projects configured"}

        if not any(projects_by_language.values()):
            print("❌ No projects detected")
            return {"success": False, "error": "No projects found"}

        self._print_project_summary(projects_by_language)

        # Delegate to iteration engine (it does all the work)
        return self.iteration_engine.run_improvement_loop(projects_by_language)

    def _create_language_adapters(self) -> dict:
        """Create language adapters from config."""
        adapters = {}
        languages = self.config.get("languages", {})

        if "flutter" in languages.get("enabled", []):
            adapters["flutter"] = FlutterAdapter(languages.get("flutter", {}))

        if "python" in languages.get("enabled", []):
            adapters["python"] = PythonAdapter(languages.get("python", {}))

        if "javascript" in languages.get("enabled", []):
            adapters["javascript"] = JavaScriptAdapter(languages.get("javascript", {}))

        if "go" in languages.get("enabled", []):
            adapters["go"] = GoAdapter(languages.get("go", {}))

        return adapters

    def _get_projects_from_config(self) -> dict[str, list[str]]:
        """Get explicit project list from config, organized by language."""
        projects_by_language = {}

        for project in self.config.get("projects", []):
            project_path = project["path"]
            language = project["language"]

            if language in self.adapters:
                if language not in projects_by_language:
                    projects_by_language[language] = []
                projects_by_language[language].append(project_path)

        return projects_by_language

    def _print_project_summary(self, projects_by_language: dict[str, list[str]]):
        """Print detected projects summary."""
        print("\n📦 Detected Projects:")
        for lang, projects in projects_by_language.items():
            print(f"   {lang.upper()}: {len(projects)} project(s)")
            for p in projects:
                print(f"      - {p}")


def main():
    """Main entry point - thin wrapper that loads config and runs orchestrator."""
    if len(sys.argv) < 2:
        print("Usage: python multi_language_orchestrator.py <config.yaml>")
        print("\nExample:")
        print("  python multi_language_orchestrator.py config/real_projects_fix.yaml")
        sys.exit(1)

    config_path = sys.argv[1]

    # Load configuration
    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config file: {e}")
        sys.exit(1)

    # Run orchestrator (it delegates everything)
    orchestrator = MultiLanguageOrchestrator(config)
    result = orchestrator.execute()

    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
