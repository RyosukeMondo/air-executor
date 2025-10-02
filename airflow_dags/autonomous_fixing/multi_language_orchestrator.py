"""
Multi-language autonomous fixing orchestrator with priority-based execution.

Priority Strategy:
- P1 (High): Fast static analysis (errors, complexity, file size) - ALWAYS RUN
- P2 (Medium): Strategic unit tests (time-aware based on health) - ADAPTIVE
- P3 (Low): Coverage improvements - CONDITIONAL (P1 ≥ 90% AND P2 ≥ 85%)
- P4 (Final): E2E/runtime testing - CONDITIONAL (overall health ≥ 90%)
"""

import sys
import time
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Handle both module import and script execution
try:
    from .language_adapters import (
        LanguageAdapter,
        AnalysisResult,
        FlutterAdapter,
        PythonAdapter,
        JavaScriptAdapter,
        GoAdapter
    )
except ImportError:
    # Running as script - add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from language_adapters import (
        LanguageAdapter,
        AnalysisResult,
        FlutterAdapter,
        PythonAdapter,
        JavaScriptAdapter,
        GoAdapter
    )


@dataclass
class PriorityPhaseResult:
    """Result of a priority phase execution."""
    phase: str  # 'p1_static', 'p2_tests', 'p3_coverage', 'p4_e2e'
    language_results: Dict[str, AnalysisResult] = field(default_factory=dict)
    score: float = 0.0
    passed_gate: bool = False
    execution_time: float = 0.0
    gate_reason: Optional[str] = None


class MultiLanguageOrchestrator:
    """Orchestrate autonomous fixing across multiple languages with priority-based execution."""

    def __init__(self, config: Dict):
        self.config = config
        self.adapters = self._initialize_adapters()
        self.priority_config = config.get('priorities', {})

    def _initialize_adapters(self) -> Dict[str, LanguageAdapter]:
        """Initialize language adapters based on config."""
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

    def execute(self, monorepo_path: str = None) -> Dict[str, any]:
        """
        Execute priority-based autonomous fixing.

        Args:
            monorepo_path: Optional monorepo path for auto-detection (legacy)

        Returns:
            Execution summary with results from each phase
        """
        print(f"\n{'='*80}")
        print("🚀 Multi-Language Autonomous Fixing")
        print(f"{'='*80}")
        print(f"Languages enabled: {', '.join(self.adapters.keys())}")
        print(f"{'='*80}\n")

        # 1. Get projects (explicit list or auto-detect)
        if 'projects' in self.config:
            # Use explicit project list
            projects_by_language = self._get_explicit_projects()
            print("Using explicit project list from config\n")
        else:
            # Legacy: auto-detect from monorepo
            print(f"Auto-detecting projects in: {monorepo_path}\n")
            projects_by_language = self.detect_all_projects(monorepo_path)
        if not any(projects_by_language.values()):
            print("❌ No projects detected in monorepo")
            return {'success': False, 'error': 'No projects found'}

        self._print_project_summary(projects_by_language)

        # 2. PRIORITY 1: Static Analysis (ALWAYS RUN)
        print(f"\n{'='*80}")
        print("📍 PRIORITY 1: Fast Static Analysis")
        print(f"{'='*80}")
        p1_result = self.execute_priority_1(projects_by_language)
        self._print_phase_result(p1_result)

        # Check P1 gate
        p1_threshold = self.priority_config.get('p1_static', {}).get('success_threshold', 0.90)
        if p1_result.score < p1_threshold:
            print(f"\n⚠️  P1 score ({p1_result.score:.1%}) < threshold ({p1_threshold:.0%})")
            print("🔧 Fix P1 issues before proceeding to P2")
            return {
                'success': False,
                'phase_completed': 'p1_static',
                'p1_result': p1_result,
                'next_action': 'fix_p1_issues'
            }

        # 3. PRIORITY 2: Strategic Tests (ADAPTIVE)
        print(f"\n{'='*80}")
        print("📍 PRIORITY 2: Strategic Unit Tests (Time-Aware)")
        print(f"{'='*80}")
        p2_result = self.execute_priority_2(projects_by_language, p1_result)
        self._print_phase_result(p2_result)

        # Check P2 gate
        p2_threshold = self.priority_config.get('p2_tests', {}).get('success_threshold', 0.85)
        if p2_result.score < p2_threshold:
            print(f"\n⚠️  P2 score ({p2_result.score:.1%}) < threshold ({p2_threshold:.0%})")
            print("🔧 Fix P2 test failures before proceeding to P3")
            return {
                'success': False,
                'phase_completed': 'p2_tests',
                'p1_result': p1_result,
                'p2_result': p2_result,
                'next_action': 'fix_p2_issues'
            }

        # 4. PRIORITY 3: Coverage (CONDITIONAL)
        p3_enabled = self.priority_config.get('p3_coverage', {}).get('enabled', True)
        p3_result = None

        if p3_enabled and self._should_run_coverage(p1_result.score, p2_result.score):
            print(f"\n{'='*80}")
            print("📍 PRIORITY 3: Coverage Analysis & Test Generation")
            print(f"{'='*80}")
            print(f"✅ Gate passed: P1 = {p1_result.score:.1%}, P2 = {p2_result.score:.1%}")
            p3_result = self.execute_priority_3(projects_by_language)
            self._print_phase_result(p3_result)
        else:
            print(f"\n⏭️  Skipping P3 (Coverage) - Gate not met")
            print(f"   Requirements: P1 ≥ {self.priority_config.get('p3_coverage', {}).get('gate_requirements', {}).get('p1_score', 0.90):.0%}, P2 ≥ {self.priority_config.get('p3_coverage', {}).get('gate_requirements', {}).get('p2_score', 0.85):.0%}")

        # 5. PRIORITY 4: E2E Tests (CONDITIONAL)
        p4_enabled = self.priority_config.get('p4_e2e', {}).get('enabled', True)
        p4_result = None

        overall_health = self._calculate_overall_health(p1_result, p2_result, p3_result)
        if p4_enabled and self._should_run_e2e(overall_health):
            print(f"\n{'='*80}")
            print("📍 PRIORITY 4: E2E & Runtime Testing")
            print(f"{'='*80}")
            print(f"✅ Overall health: {overall_health:.1%}")
            p4_result = self.execute_priority_4(projects_by_language)
            self._print_phase_result(p4_result)
        else:
            print(f"\n⏭️  Skipping P4 (E2E) - Overall health ({overall_health:.1%}) < 90%")

        # Final summary
        print(f"\n{'='*80}")
        print("📊 Final Summary")
        print(f"{'='*80}")
        print(f"✅ P1 (Static): {p1_result.score:.1%}")
        print(f"✅ P2 (Tests): {p2_result.score:.1%}")
        if p3_result:
            print(f"✅ P3 (Coverage): {p3_result.score:.1%}")
        if p4_result:
            print(f"✅ P4 (E2E): {p4_result.score:.1%}")
        print(f"📈 Overall Health: {overall_health:.1%}")
        print(f"{'='*80}\n")

        return {
            'success': True,
            'overall_health': overall_health,
            'p1_result': p1_result,
            'p2_result': p2_result,
            'p3_result': p3_result,
            'p4_result': p4_result
        }

    def detect_all_projects(self, monorepo_path: str) -> Dict[str, List[str]]:
        """Detect all projects by language."""
        projects = {}

        for lang_name, adapter in self.adapters.items():
            lang_projects = adapter.detect_projects(monorepo_path)
            if lang_projects:
                projects[lang_name] = lang_projects

        return projects

    def _get_explicit_projects(self) -> Dict[str, List[str]]:
        """Get explicit project list from config, organized by language."""
        projects_by_language = {}

        for project in self.config.get('projects', []):
            project_path = project['path']
            language = project['language']

            # Only include if language adapter is enabled
            if language in self.adapters:
                if language not in projects_by_language:
                    projects_by_language[language] = []
                projects_by_language[language].append(project_path)

        return projects_by_language

    def execute_priority_1(self, projects_by_language: Dict[str, List[str]]) -> PriorityPhaseResult:
        """
        Priority 1: Fast static analysis.

        - Static analysis errors
        - File size violations
        - Cyclomatic complexity
        - Code smells

        Should complete in ~30 seconds per language (parallel).
        """
        start_time = time.time()
        result = PriorityPhaseResult(phase='p1_static')

        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            print(f"\n🔍 {lang_name.upper()}: Analyzing {len(projects)} project(s)...")

            for project_path in projects:
                print(f"   📁 {project_path}")
                analysis = adapter.static_analysis(project_path)
                result.language_results[f"{lang_name}:{project_path}"] = analysis

                # Print summary
                total_issues = (
                    len(analysis.errors) +
                    len(analysis.file_size_violations) +
                    len(analysis.complexity_violations)
                )
                print(f"      Issues: {total_issues} (errors: {len(analysis.errors)}, "
                      f"size: {len(analysis.file_size_violations)}, "
                      f"complexity: {len(analysis.complexity_violations)})")

        # Calculate score
        result.score = self._calculate_p1_score(result.language_results)
        result.execution_time = time.time() - start_time
        result.passed_gate = result.score >= self.priority_config.get('p1_static', {}).get('success_threshold', 0.90)

        return result

    def execute_priority_2(
        self,
        projects_by_language: Dict[str, List[str]],
        p1_result: PriorityPhaseResult
    ) -> PriorityPhaseResult:
        """
        Priority 2: Strategic unit tests (time-aware).

        Test strategy based on P1 health:
        - health < 30%: minimal tests (5 min)
        - health 30-60%: selective tests (15 min)
        - health > 60%: comprehensive tests (30 min)
        """
        start_time = time.time()
        result = PriorityPhaseResult(phase='p2_tests')

        # Determine test strategy based on P1 score
        strategy = self._determine_test_strategy(p1_result.score)
        print(f"📊 Test strategy: {strategy.upper()} (based on P1 health: {p1_result.score:.1%})")

        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            print(f"\n🧪 {lang_name.upper()}: Running {strategy} tests...")

            for project_path in projects:
                print(f"   📁 {project_path}")
                description = adapter.get_test_strategy_description(strategy)
                print(f"      {description}")

                analysis = adapter.run_tests(project_path, strategy)
                result.language_results[f"{lang_name}:{project_path}"] = analysis

                # Print summary
                total = analysis.tests_passed + analysis.tests_failed
                print(f"      Results: {analysis.tests_passed}/{total} passed")

        # Calculate score
        result.score = self._calculate_p2_score(result.language_results)
        result.execution_time = time.time() - start_time
        result.passed_gate = result.score >= self.priority_config.get('p2_tests', {}).get('success_threshold', 0.85)

        return result

    def execute_priority_3(self, projects_by_language: Dict[str, List[str]]) -> PriorityPhaseResult:
        """Priority 3: Coverage analysis and test generation."""
        start_time = time.time()
        result = PriorityPhaseResult(phase='p3_coverage')

        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            print(f"\n📈 {lang_name.upper()}: Analyzing coverage...")

            for project_path in projects:
                print(f"   📁 {project_path}")
                analysis = adapter.analyze_coverage(project_path)
                result.language_results[f"{lang_name}:{project_path}"] = analysis

                # Print summary
                print(f"      Coverage: {analysis.coverage_percentage:.1f}%")
                print(f"      Gaps: {len(analysis.coverage_gaps)} files with low coverage")

        # Calculate score
        result.score = self._calculate_p3_score(result.language_results)
        result.execution_time = time.time() - start_time

        return result

    def execute_priority_4(self, projects_by_language: Dict[str, List[str]]) -> PriorityPhaseResult:
        """Priority 4: E2E tests and runtime error capture."""
        start_time = time.time()
        result = PriorityPhaseResult(phase='p4_e2e')

        for lang_name, projects in projects_by_language.items():
            adapter = self.adapters[lang_name]
            print(f"\n🎭 {lang_name.upper()}: Running E2E tests...")

            for project_path in projects:
                print(f"   📁 {project_path}")
                analysis = adapter.run_e2e_tests(project_path)
                result.language_results[f"{lang_name}:{project_path}"] = analysis

                # Print summary
                if analysis.success:
                    print(f"      ✅ All E2E tests passed")
                else:
                    print(f"      ❌ {len(analysis.runtime_errors)} runtime errors")

        # Calculate score
        result.score = self._calculate_p4_score(result.language_results)
        result.execution_time = time.time() - start_time

        return result

    def _determine_test_strategy(self, health_score: float) -> str:
        """Determine test strategy based on health score."""
        if health_score < 0.30:
            return 'minimal'  # Only critical tests (5 min)
        elif health_score < 0.60:
            return 'selective'  # Changed files + smoke tests (15 min)
        else:
            return 'comprehensive'  # Full test suite (30 min)

    def _should_run_coverage(self, p1_score: float, p2_score: float) -> bool:
        """Check if coverage analysis should run."""
        requirements = self.priority_config.get('p3_coverage', {}).get('gate_requirements', {})
        p1_threshold = requirements.get('p1_score', 0.90)
        p2_threshold = requirements.get('p2_score', 0.85)

        return p1_score >= p1_threshold and p2_score >= p2_threshold

    def _should_run_e2e(self, overall_health: float) -> bool:
        """Check if E2E tests should run."""
        requirements = self.priority_config.get('p4_e2e', {}).get('gate_requirements', {})
        health_threshold = requirements.get('overall_health', 0.90)

        return overall_health >= health_threshold

    def _calculate_p1_score(self, results: Dict[str, AnalysisResult]) -> float:
        """Calculate P1 score (static analysis health)."""
        if not results:
            return 0.0

        total_projects = len(results)
        healthy_projects = sum(
            1 for r in results.values()
            if len(r.errors) == 0 and len(r.complexity_violations) < 5
        )

        return healthy_projects / total_projects

    def _calculate_p2_score(self, results: Dict[str, AnalysisResult]) -> float:
        """Calculate P2 score (test pass rate)."""
        if not results:
            return 0.0

        total_tests = sum(r.tests_passed + r.tests_failed for r in results.values())
        if total_tests == 0:
            return 1.0  # No tests = assume passing

        passed_tests = sum(r.tests_passed for r in results.values())
        return passed_tests / total_tests

    def _calculate_p3_score(self, results: Dict[str, AnalysisResult]) -> float:
        """Calculate P3 score (coverage percentage)."""
        if not results:
            return 0.0

        coverages = [r.coverage_percentage for r in results.values() if r.coverage_percentage > 0]
        if not coverages:
            return 0.0

        return sum(coverages) / len(coverages) / 100  # Normalize to 0-1

    def _calculate_p4_score(self, results: Dict[str, AnalysisResult]) -> float:
        """Calculate P4 score (E2E success rate)."""
        if not results:
            return 0.0

        total = len(results)
        successful = sum(1 for r in results.values() if r.success)

        return successful / total

    def _calculate_overall_health(
        self,
        p1: PriorityPhaseResult,
        p2: PriorityPhaseResult,
        p3: Optional[PriorityPhaseResult]
    ) -> float:
        """Calculate overall health score."""
        # Weighted average: P1 (40%), P2 (40%), P3 (20%)
        health = (p1.score * 0.4) + (p2.score * 0.4)

        if p3:
            health += (p3.score * 0.2)
        else:
            # If P3 not run, redistribute weight to P1/P2
            health = (p1.score * 0.5) + (p2.score * 0.5)

        return health

    def _print_project_summary(self, projects_by_language: Dict[str, List[str]]):
        """Print detected projects summary."""
        print(f"\n📦 Detected Projects:")
        for lang, projects in projects_by_language.items():
            print(f"   {lang.upper()}: {len(projects)} project(s)")
            for p in projects:
                print(f"      - {p}")

    def _print_phase_result(self, result: PriorityPhaseResult):
        """Print phase execution result."""
        print(f"\n📊 Phase Result:")
        print(f"   Score: {result.score:.1%}")
        print(f"   Time: {result.execution_time:.1f}s")
        if result.passed_gate:
            print(f"   ✅ Gate PASSED")
        elif result.gate_reason:
            print(f"   ⏭️  {result.gate_reason}")


def main():
    """Main entry point for command-line execution."""
    if len(sys.argv) < 2:
        print("Usage: python multi_language_orchestrator.py <config.yaml>")
        print("\nExample:")
        print("  python multi_language_orchestrator.py config/multi_language_fix.yaml")
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

    # Run orchestrator (supports both explicit project lists and legacy target_project)
    orchestrator = MultiLanguageOrchestrator(config)

    if 'projects' in config:
        # New format: explicit project list
        result = orchestrator.execute()
    else:
        # Legacy format: auto-detect from target_project
        target_project = config.get('target_project')
        if not target_project:
            print("❌ No 'projects' list or 'target_project' specified in config")
            sys.exit(1)
        result = orchestrator.execute(target_project)

    # Exit with appropriate code
    if result.get('success'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
