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
import yaml
from pathlib import Path
from typing import Dict, List

# Import language adapters
try:
    from .language_adapters import (
        FlutterAdapter,
        PythonAdapter,
        JavaScriptAdapter,
        GoAdapter
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from language_adapters import (
        FlutterAdapter,
        PythonAdapter,
        JavaScriptAdapter,
        GoAdapter
    )

# Import clean core modules
try:
    from .core import ProjectAnalyzer, IssueFixer, HealthScorer, IterationEngine
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from core import ProjectAnalyzer, IssueFixer, HealthScorer, IterationEngine


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

    def __init__(self, config: Dict):
        """
        Args:
            config: Full configuration dict
        """
        self.config = config

        # Initialize language adapters (SRP: each adapter handles one language)
        self.adapters = self._create_language_adapters()

        # Initialize core modules (SRP: each module has one job)
        self.analyzer = ProjectAnalyzer(self.adapters, config)
        self.fixer = IssueFixer(config)
        self.scorer = HealthScorer(config)
        self.iteration_engine = IterationEngine(
            self.analyzer,
            self.fixer,
            self.scorer,
            config
        )

    def execute(self) -> Dict:
        """
        Execute autonomous fixing - just coordinate, don't do the work.

        Returns: Results dict from iteration_engine
        """
        print(f"\n{'='*80}")
        print("🚀 Multi-Language Autonomous Fixing")
        print(f"{'='*80}")
        print(f"Languages enabled: {', '.join(self.adapters.keys())}")
        print(f"{'='*80}\n")

        # Get projects (explicit list from config)
        if 'projects' in self.config:
            print("Using explicit project list from config\n")
            projects_by_language = self._get_projects_from_config()
        else:
            print("❌ No projects list in config")
            return {'success': False, 'error': 'No projects configured'}

        if not any(projects_by_language.values()):
            print("❌ No projects detected")
            return {'success': False, 'error': 'No projects found'}

        self._print_project_summary(projects_by_language)

        # Delegate to iteration engine (it does all the work)
        return self.iteration_engine.run_improvement_loop(projects_by_language)

    def _create_language_adapters(self) -> Dict:
        """Create language adapters from config."""
        adapters = {}
        languages = self.config.get('languages', {})

        if 'flutter' in languages.get('enabled', []):
            adapters['flutter'] = FlutterAdapter(languages.get('flutter', {}))

        if 'python' in languages.get('enabled', []):
            adapters['python'] = PythonAdapter(languages.get('python', {}))

        if 'javascript' in languages.get('enabled', []):
            adapters['javascript'] = JavaScriptAdapter(languages.get('javascript', {}))

        if 'go' in languages.get('enabled', []):
            adapters['go'] = GoAdapter(languages.get('go', {}))

        return adapters

    def _get_projects_from_config(self) -> Dict[str, List[str]]:
        """Get explicit project list from config, organized by language."""
        projects_by_language = {}

        for project in self.config.get('projects', []):
            project_path = project['path']
            language = project['language']

            if language in self.adapters:
                if language not in projects_by_language:
                    projects_by_language[language] = []
                projects_by_language[language].append(project_path)

        return projects_by_language

    def _print_project_summary(self, projects_by_language: Dict[str, List[str]]):
        """Print detected projects summary."""
        print(f"\n📦 Detected Projects:")
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
        with open(config_path, 'r') as f:
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
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
