"""
Health Scorer - Single Responsibility: Calculate health scores.

Clean, focused module that ONLY handles scoring logic.
No analysis, no fixing, no iteration logic - just scoring.
"""

from typing import Dict


class HealthScorer:
    """
    Calculates health scores from analysis results.

    Responsibilities:
    - Calculate P1 (static) scores
    - Calculate P2 (test) scores
    - Calculate overall health scores
    - Determine if gates are passed

    Does NOT:
    - Analyze code (that's ProjectAnalyzer's job)
    - Fix issues (that's IssueFixer's job)
    - Manage iterations (that's IterationEngine's job)
    """

    def __init__(self, config: Dict):
        """
        Args:
            config: Configuration dict with priority thresholds
        """
        self.config = config
        self.priority_config = config.get('priorities', {})

    def score_static_analysis(self, analysis_result) -> Dict:
        """
        Calculate P1 score from static analysis results.

        Score = (projects_with_no_errors / total_projects)

        Returns: Dict with score, passed_gate, threshold
        """
        results = analysis_result.results_by_project

        total_projects = len(results)
        if total_projects == 0:
            return {'score': 0.0, 'passed_gate': False, 'threshold': 0.90}

        # Count projects with no critical errors
        projects_with_no_errors = sum(
            1 for analysis in results.values()
            if len(analysis.errors) == 0
        )

        score = projects_with_no_errors / total_projects
        threshold = self.priority_config.get('p1_static', {}).get('success_threshold', 0.90)

        return {
            'score': score,
            'passed_gate': score >= threshold,
            'threshold': threshold,
            'phase': 'p1_static'
        }

    def score_tests(self, analysis_result) -> Dict:
        """
        Calculate P2 score from test results.

        Score = (total_passed / total_tests)

        Returns: Dict with score, passed_gate, threshold
        """
        results = analysis_result.results_by_project

        total_passed = 0
        total_tests = 0

        for analysis in results.values():
            total_passed += analysis.tests_passed
            total_tests += (analysis.tests_passed + analysis.tests_failed)

        threshold = self.priority_config.get('p2_tests', {}).get('success_threshold', 0.85)

        # If no tests exist, treat as CRITICAL FAILURE (0%)
        # Can't verify health without tests - must create them
        if total_tests == 0:
            return {
                'score': 0.0,  # 0% - no tests means no way to verify health
                'passed_gate': False,  # FAIL the gate - must create tests
                'threshold': threshold,
                'phase': 'p2_tests',
                'needs_test_creation': True  # Signal to create tests
            }

        score = total_passed / total_tests

        return {
            'score': score,
            'passed_gate': score >= threshold,
            'threshold': threshold,
            'phase': 'p2_tests'
        }

    def calculate_overall_health(self, p1_score: float, p2_score: float) -> float:
        """
        Calculate overall health from P1 and P2 scores.

        Weighted average: P1 (50%) + P2 (50%)

        Returns: Overall health score (0.0 to 1.0)
        """
        return (p1_score * 0.5) + (p2_score * 0.5)

    def determine_test_strategy(self, p1_score: float) -> str:
        """
        Determine test strategy based on P1 health.

        - < 30%: minimal (fast tests only)
        - 30-60%: selective (skip integration tests)
        - > 60%: comprehensive (all tests)

        Returns: 'minimal', 'selective', or 'comprehensive'
        """
        if p1_score < 0.30:
            return 'minimal'
        elif p1_score < 0.60:
            return 'selective'
        else:
            return 'comprehensive'
