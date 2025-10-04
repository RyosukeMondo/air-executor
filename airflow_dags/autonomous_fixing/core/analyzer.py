"""
Project Analyzer - Single Responsibility: Run analysis across projects.

Clean, focused module that ONLY handles analysis orchestration.
No fixing, no scoring, no iteration logic - just analysis.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ProjectAnalysisResult:
    """Result from analyzing multiple projects (collection of results)."""

    phase: str  # 'p1_static', 'p2_tests', etc.
    results_by_project: Dict[str, any] = field(
        default_factory=dict
    )  # Maps "lang:path" -> AnalysisResult
    execution_time: float = 0.0


class ProjectAnalyzer:
    """
    Analyzes projects in parallel using language adapters.

    Responsibilities:
    - Run P1 (static) analysis across all projects in parallel
    - Run P2 (tests) analysis across all projects in parallel
    - Coordinate parallel execution for performance
    - Return structured results

    Does NOT:
    - Fix issues (that's IssueFixer's job)
    - Calculate scores (that's HealthScorer's job)
    - Manage iterations (that's IterationEngine's job)
    """

    def __init__(self, language_adapters: Dict, config: Dict):
        """
        Args:
            language_adapters: Dict of {language_name: adapter_instance}
            config: Configuration dict with execution settings
        """
        self.adapters = language_adapters
        self.config = config

    def analyze_static(self, projects_by_language: Dict[str, List[str]]) -> ProjectAnalysisResult:
        """
        Run P1 static analysis on all projects sequentially (for real-time logging and Ctrl+C).

        Returns: AnalysisResult with results_by_project keyed by "language:path"
        """
        start_time = time.time()
        result = ProjectAnalysisResult(phase="p1_static")

        # Count total projects
        total_projects = sum(len(projects) for projects in projects_by_language.values())
        print(f"\n🚀 Analyzing {total_projects} project(s) sequentially...\n")

        # Execute sequentially (no threads - immediate logging and Ctrl+C)
        project_num = 0
        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            for project_path in projects:
                project_num += 1
                project_name = project_path.split("/")[-1]

                print(
                    f"[{project_num}/{total_projects}] Analyzing {lang_name.upper()}: {project_name}..."
                )

                try:
                    analysis = adapter.static_analysis(project_path)
                    key = f"{lang_name}:{project_path}"
                    result.results_by_project[key] = analysis

                    # Print summary
                    total_issues = (
                        len(analysis.errors)
                        + len(analysis.file_size_violations)
                        + len(analysis.complexity_violations)
                    )
                    print(f"✓ {lang_name.upper()}: {project_name}")
                    print(
                        f"   Issues: {total_issues} (errors: {len(analysis.errors)}, "
                        f"size: {len(analysis.file_size_violations)}, "
                        f"complexity: {len(analysis.complexity_violations)})\n"
                    )
                except Exception as e:
                    print(f"✗ {lang_name.upper()}: {project_name} - Error: {e}\n")

        result.execution_time = time.time() - start_time
        print(f"\n⏱️  Completed in {result.execution_time:.1f}s")
        return result

    def analyze_tests(
        self, projects_by_language: Dict[str, List[str]], strategy: str
    ) -> ProjectAnalysisResult:
        """
        Run P2 test analysis on all projects sequentially (for real-time logging and Ctrl+C).

        Args:
            strategy: 'minimal', 'selective', or 'comprehensive'

        Returns: AnalysisResult with test results
        """
        start_time = time.time()
        result = ProjectAnalysisResult(phase="p2_tests")

        # Count total projects
        total_projects = sum(len(projects) for projects in projects_by_language.values())
        print(f"\n🚀 Running tests on {total_projects} project(s) sequentially...\n")

        # Execute sequentially (no threads - immediate logging and Ctrl+C)
        project_num = 0
        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            for project_path in projects:
                project_num += 1
                project_name = project_path.split("/")[-1]

                print(
                    f"[{project_num}/{total_projects}] Running tests for {lang_name.upper()}: {project_name}..."
                )

                try:
                    analysis = adapter.run_tests(project_path, strategy)
                    key = f"{lang_name}:{project_path}"
                    result.results_by_project[key] = analysis

                    # Print summary
                    total = analysis.tests_passed + analysis.tests_failed
                    print(f"✓ {lang_name.upper()}: {project_name}")
                    print(f"   Tests: {analysis.tests_passed}/{total} passed\n")
                except Exception as e:
                    print(f"✗ {lang_name.upper()}: {project_name} - Error: {e}\n")

        result.execution_time = time.time() - start_time
        print(f"\n⏱️  Completed in {result.execution_time:.1f}s")
        return result
