"""
Iteration Engine - Single Responsibility: Manage improvement iterations.

Clean, focused module that ONLY handles the iteration loop logic.
No analysis, no fixing, no scoring - just iteration coordination.
"""

from typing import Dict


class IterationEngine:
    """
    Manages the iterative improvement loop.

    Responsibilities:
    - Loop up to max_iterations
    - Track iteration progress
    - Determine when to stop (gates passed or max reached)
    - Coordinate analyzer, fixer, scorer

    Does NOT:
    - Analyze code (delegates to ProjectAnalyzer)
    - Fix issues (delegates to IssueFixer)
    - Calculate scores (delegates to HealthScorer)
    """

    def __init__(self, analyzer, fixer, scorer, config: Dict):
        """
        Args:
            analyzer: ProjectAnalyzer instance
            fixer: IssueFixer instance
            scorer: HealthScorer instance
            config: Configuration dict with max_iterations
        """
        self.analyzer = analyzer
        self.fixer = fixer
        self.scorer = scorer
        self.config = config
        self.max_iterations = config.get('execution', {}).get('max_iterations', 5)

    def run_improvement_loop(self, projects_by_language: Dict) -> Dict:
        """
        Run the improvement loop until gates pass or max iterations reached.

        Algorithm:
        0. SETUP: Discover test configuration (runs once, cached)
        1. Analyze (P1 static)
        2. Score
        3. If score < threshold: Fix → repeat
        4. If score >= threshold: Analyze (P2 tests)
        5. If score < threshold: Fix → repeat
        6. If both gates passed: Success!

        Returns: Dict with final results and iteration stats
        """
        # === SETUP PHASE: Test Discovery (runs once) ===
        print(f"\n{'='*80}")
        print("🔧 SETUP PHASE: Test Configuration Discovery")
        print(f"{'='*80}")

        for lang_name, project_list in projects_by_language.items():
            for project_path in project_list:
                self.fixer.discover_test_config(project_path, lang_name)

        print(f"\n🔄 Starting improvement iterations (max: {self.max_iterations})")

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*80}")
            print(f"🔁 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'='*80}")

            # === PHASE 1: Static Analysis ===
            print(f"\n{'='*80}")
            print("📍 PRIORITY 1: Fast Static Analysis")
            print(f"{'='*80}")

            p1_result = self.analyzer.analyze_static(projects_by_language)
            p1_score_data = self.scorer.score_static_analysis(p1_result)

            self._print_score(p1_score_data, p1_result.execution_time)

            # Check P1 gate
            if not p1_score_data['passed_gate']:
                print(f"\n⚠️  P1 score ({p1_score_data['score']:.1%}) < threshold ({p1_score_data['threshold']:.0%})")

                # Fix P1 issues
                fix_result = self.fixer.fix_static_issues(p1_result, iteration)

                if fix_result.success:
                    print(f"\n✅ Fixes applied, re-running analysis in next iteration...")
                else:
                    print(f"\n⚠️  No fixes could be applied")

                continue  # Re-run analysis in next iteration

            # P1 gate passed!
            print(f"\n✅ P1 gate PASSED ({p1_score_data['score']:.1%} >= {p1_score_data['threshold']:.0%})")

            # === PHASE 2: Tests ===
            print(f"\n{'='*80}")
            print("📍 PRIORITY 2: Strategic Unit Tests (Time-Aware)")
            print(f"{'='*80}")

            # Determine test strategy based on P1 health
            strategy = self.scorer.determine_test_strategy(p1_score_data['score'])
            print(f"📊 Test strategy: {strategy.upper()} (based on P1 health: {p1_score_data['score']:.1%})")

            p2_result = self.analyzer.analyze_tests(projects_by_language, strategy)
            p2_score_data = self.scorer.score_tests(p2_result)

            self._print_score(p2_score_data, p2_result.execution_time)

            # Check P2 gate
            if not p2_score_data['passed_gate']:
                print(f"\n⚠️  P2 score ({p2_score_data['score']:.1%}) < threshold ({p2_score_data['threshold']:.0%})")

                # Check if this is a "no tests" situation (critical failure)
                if p2_score_data.get('needs_test_creation', False):
                    print("\n⚠️  CRITICAL: No tests found - delegating test creation to claude_wrapper")

                    # Create tests using LLM-as-a-judge
                    fix_result = self.fixer.create_tests(p2_result, iteration)

                    if fix_result.success:
                        print(f"\n✅ Tests created, re-running analysis in next iteration...")
                    else:
                        print(f"\n⚠️  Test creation failed")

                else:
                    # Fix P2 issues (failing tests)
                    fix_result = self.fixer.fix_test_failures(p2_result, iteration)

                    if fix_result.success:
                        print(f"\n✅ Fixes applied, re-running analysis in next iteration...")
                    else:
                        print(f"\n⚠️  No fixes could be applied")

                continue  # Re-run analysis in next iteration

            # Both gates passed!
            print(f"\n✅ P2 gate PASSED ({p2_score_data['score']:.1%} >= {p2_score_data['threshold']:.0%})")
            print(f"\n🎉 All priority gates passed in iteration {iteration}!")

            return {
                'success': True,
                'iterations_completed': iteration,
                'p1_score': p1_score_data['score'],
                'p2_score': p2_score_data['score'],
                'overall_health': self.scorer.calculate_overall_health(
                    p1_score_data['score'],
                    p2_score_data['score']
                )
            }

        # Max iterations reached without passing gates
        print(f"\n⚠️  Reached maximum iterations ({self.max_iterations}) without passing all gates")

        return {
            'success': False,
            'reason': 'max_iterations_reached',
            'iterations_completed': self.max_iterations
        }

    def _print_score(self, score_data: Dict, execution_time: float):
        """Print score summary."""
        print(f"\n📊 Phase Result:")
        print(f"   Score: {score_data['score']:.1%}")
        print(f"   Time: {execution_time:.1f}s")
