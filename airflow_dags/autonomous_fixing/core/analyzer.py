"""
Project Analyzer - Single Responsibility: Run analysis across projects.

Clean, focused module that ONLY handles analysis orchestration.
No fixing, no scoring, no iteration logic - just analysis.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ProjectAnalysisResult:
    """Result from analyzing multiple projects (collection of results)."""
    phase: str  # 'p1_static', 'p2_tests', etc.
    results_by_project: Dict[str, any] = field(default_factory=dict)  # Maps "lang:path" -> AnalysisResult
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
        self.max_workers = config.get('execution', {}).get('max_concurrent_projects', 5)

    def analyze_static(self, projects_by_language: Dict[str, List[str]]) -> ProjectAnalysisResult:
        """
        Run P1 static analysis on all projects in parallel.

        Returns: AnalysisResult with results_by_project keyed by "language:path"
        """
        start_time = time.time()
        result = ProjectAnalysisResult(phase='p1_static')

        # Prepare tasks for parallel execution
        tasks = []
        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            for project_path in projects:
                tasks.append((lang_name, adapter, project_path))

        print(f"\n🚀 Analyzing {len(tasks)} project(s) in parallel (max {self.max_workers} concurrent)...\n")

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_project = {
                executor.submit(adapter.static_analysis, project_path): (lang_name, project_path)
                for lang_name, adapter, project_path in tasks
            }

            for future in as_completed(future_to_project):
                lang_name, project_path = future_to_project[future]
                try:
                    analysis = future.result()
                    key = f"{lang_name}:{project_path}"
                    result.results_by_project[key] = analysis

                    # Print summary
                    total_issues = (
                        len(analysis.errors) +
                        len(analysis.file_size_violations) +
                        len(analysis.complexity_violations)
                    )
                    print(f"✓ {lang_name.upper()}: {project_path.split('/')[-1]}")
                    print(f"   Issues: {total_issues} (errors: {len(analysis.errors)}, "
                          f"size: {len(analysis.file_size_violations)}, "
                          f"complexity: {len(analysis.complexity_violations)})")
                except Exception as e:
                    print(f"✗ {lang_name.upper()}: {project_path.split('/')[-1]} - Error: {e}")

        result.execution_time = time.time() - start_time
        print(f"\n⏱️  Completed in {result.execution_time:.1f}s")
        return result

    def analyze_tests(self, projects_by_language: Dict[str, List[str]], strategy: str) -> ProjectAnalysisResult:
        """
        Run P2 test analysis on all projects in parallel.

        Args:
            strategy: 'minimal', 'selective', or 'comprehensive'

        Returns: AnalysisResult with test results
        """
        start_time = time.time()
        result = ProjectAnalysisResult(phase='p2_tests')

        # Prepare tasks
        tasks = []
        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            for project_path in projects:
                tasks.append((lang_name, adapter, project_path, strategy))

        print(f"\n🚀 Running tests on {len(tasks)} project(s) in parallel (max {self.max_workers} concurrent)...\n")

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_project = {
                executor.submit(adapter.run_tests, project_path, strategy): (lang_name, project_path)
                for lang_name, adapter, project_path, strategy in tasks
            }

            for future in as_completed(future_to_project):
                lang_name, project_path = future_to_project[future]
                try:
                    analysis = future.result()
                    key = f"{lang_name}:{project_path}"
                    result.results_by_project[key] = analysis

                    # Print summary
                    total = analysis.tests_passed + analysis.tests_failed
                    print(f"✓ {lang_name.upper()}: {project_path.split('/')[-1]}")
                    print(f"   Tests: {analysis.tests_passed}/{total} passed")
                except Exception as e:
                    print(f"✗ {lang_name.upper()}: {project_path.split('/')[-1]} - Error: {e}")

        result.execution_time = time.time() - start_time
        print(f"\n⏱️  Completed in {result.execution_time:.1f}s")
        return result
