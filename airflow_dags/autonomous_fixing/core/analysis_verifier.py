"""
Analysis Verifier - Ensures analysis results are trustworthy.

Single Responsibility: Verify analysis results and detect silent failures.
Follows SOLID principles - focused, testable, composable.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VerificationResult:
    """Result of verifying an analysis."""
    is_valid: bool
    issues_found: List[str] = None
    warnings: List[str] = None
    error_count: int = 0
    execution_time: float = 0.0

    def __post_init__(self):
        if self.issues_found is None:
            self.issues_found = []
        if self.warnings is None:
            self.warnings = []


class AnalysisVerifier:
    """
    Verifies analysis results to detect silent failures.

    Responsibilities:
    - Detect impossible results (0 errors in 0.0s)
    - Verify analysis actually ran
    - Compare before/after to prove improvement
    - Provide actionable feedback on failures

    Does NOT:
    - Run analysis (that's ProjectAnalyzer's job)
    - Fix issues (that's IssueFixer's job)
    - Score results (that's HealthScorer's job)
    """

    def __init__(self, config: Dict):
        """
        Args:
            config: Configuration dict with verification settings
        """
        self.config = config
        # Minimum realistic execution time (seconds)
        # Note: Modern tools like ruff (Rust) can be legitimately fast (<0.05s)
        self.min_execution_time = 0.01  # Lowered for fast tools like ruff

    def verify_analysis_result(self, result, project_path: str) -> VerificationResult:
        """
        Verify a single analysis result for validity.

        Args:
            result: AnalysisResult from language adapter
            project_path: Path to project being analyzed

        Returns:
            VerificationResult indicating if analysis is trustworthy
        """
        verification = VerificationResult(
            is_valid=True,
            error_count=len(getattr(result, 'errors', []))
        )

        # Check 1: Execution time sanity
        exec_time = getattr(result, 'execution_time', 0.0)
        verification.execution_time = exec_time

        if exec_time < self.min_execution_time:
            verification.is_valid = False
            verification.issues_found.append(
                f"⚠️  SILENT FAILURE: Analysis completed in {exec_time:.3f}s "
                f"(< {self.min_execution_time}s threshold)"
            )
            verification.issues_found.append(
                "   This indicates the analysis didn't actually run"
            )

        # Check 2: Zero errors with zero time (classic silent failure)
        # BUT: Count complexity and file size violations too - they prove analysis ran
        error_count = len(getattr(result, 'errors', []))
        complexity_count = len(getattr(result, 'complexity_violations', []))
        file_size_count = len(getattr(result, 'file_size_violations', []))
        total_findings = error_count + complexity_count + file_size_count

        if total_findings == 0 and exec_time < self.min_execution_time:
            verification.is_valid = False
            verification.issues_found.append(
                "⚠️  SUSPICIOUS: 0 issues found in near-zero time"
            )
            verification.issues_found.append(
                "   Real analysis should find something or take time - looks cached/skipped"
            )

        # Check 3: Result has required fields
        required_fields = ['errors', 'success', 'execution_time']
        missing_fields = [f for f in required_fields if not hasattr(result, f)]
        if missing_fields:
            verification.is_valid = False
            verification.issues_found.append(
                f"⚠️  MALFORMED RESULT: Missing fields: {missing_fields}"
            )

        # Check 4: Execution error
        if hasattr(result, 'error_message') and result.error_message:
            verification.warnings.append(
                f"⚠️  Analysis reported error: {result.error_message}"
            )

        return verification

    def compare_results(
        self,
        before: any,
        after: any,
        project_path: str
    ) -> Dict:
        """
        Compare analysis results before and after fixing.

        Args:
            before: AnalysisResult before fixes
            after: AnalysisResult after fixes
            project_path: Path to project

        Returns:
            Dict with comparison metrics and improvement verification
        """
        before_errors = len(getattr(before, 'errors', []))
        after_errors = len(getattr(after, 'errors', []))

        errors_fixed = before_errors - after_errors
        improvement_pct = (errors_fixed / before_errors * 100) if before_errors > 0 else 0

        comparison = {
            'project': project_path,
            'before_errors': before_errors,
            'after_errors': after_errors,
            'errors_fixed': errors_fixed,
            'improvement_pct': improvement_pct,
            'actually_improved': errors_fixed > 0,
            'got_worse': errors_fixed < 0,
            'no_change': errors_fixed == 0
        }

        # Detect false claims of success
        if errors_fixed <= 0 and before_errors > 0:
            comparison['false_success'] = True
            comparison['message'] = (
                f"⚠️  VERIFICATION FAILED: "
                f"Claimed fixes but errors unchanged ({before_errors} → {after_errors})"
            )
        elif errors_fixed > 0:
            comparison['false_success'] = False
            comparison['message'] = (
                f"✅ VERIFIED: Fixed {errors_fixed} errors "
                f"({improvement_pct:.1f}% improvement)"
            )
        else:
            comparison['false_success'] = False
            comparison['message'] = "✓ No errors before or after (already clean)"

        return comparison

    def verify_batch_results(
        self,
        results_by_project: Dict[str, any]
    ) -> Dict:
        """
        Verify a batch of analysis results (from ProjectAnalysisResult).

        Args:
            results_by_project: Dict mapping "lang:path" -> AnalysisResult

        Returns:
            Dict with overall verification status and per-project details
        """
        batch_verification = {
            'all_valid': True,
            'total_projects': len(results_by_project),
            'valid_projects': 0,
            'invalid_projects': 0,
            'silent_failures': [],
            'warnings': [],
            'per_project': {}
        }

        for key, result in results_by_project.items():
            project_path = key.split(':', 1)[1]  # Extract path from "lang:path"
            verification = self.verify_analysis_result(result, project_path)

            batch_verification['per_project'][key] = verification

            if verification.is_valid:
                batch_verification['valid_projects'] += 1
            else:
                batch_verification['invalid_projects'] += 1
                batch_verification['all_valid'] = False
                batch_verification['silent_failures'].append({
                    'project': key,
                    'issues': verification.issues_found
                })

            if verification.warnings:
                batch_verification['warnings'].extend([
                    f"{key}: {w}" for w in verification.warnings
                ])

        return batch_verification

    def print_verification_report(self, verification: Dict):
        """Print a human-readable verification report."""
        if verification['all_valid']:
            print(f"\n✅ VERIFICATION: All {verification['total_projects']} analysis results are valid")
        else:
            print(f"\n❌ VERIFICATION FAILED: {verification['invalid_projects']}/{verification['total_projects']} projects have issues")

            for failure in verification['silent_failures']:
                print(f"\n⚠️  {failure['project']}:")
                for issue in failure['issues']:
                    print(f"   {issue}")

        if verification['warnings']:
            print(f"\n⚠️  Warnings ({len(verification['warnings'])}):")
            for warning in verification['warnings'][:5]:  # Limit to 5
                print(f"   {warning}")
