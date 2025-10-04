"""
Issue Extractor - Extracts issues from analysis results.

Separates issue extraction logic from fixing logic.
"""


class IssueExtractor:
    """Extracts and prioritizes issues from analysis results."""

    @staticmethod
    def extract_static_issues(results_by_project: dict, max_issues: int) -> list[dict]:
        """Extract top static issues from analysis results."""
        all_issues = []

        for project_key, analysis in results_by_project.items():
            lang_name, project_path = project_key.split(":", 1)

            # Add errors (top 5 per project)
            for error in analysis.errors[:5]:
                all_issues.append(
                    {
                        "project": project_path,
                        "language": lang_name,
                        "type": "error",
                        "file": error.get("file", ""),
                        "line": error.get("line", 0),
                        "message": error.get("message", ""),
                    }
                )

            # Add complexity violations (top 3 per project)
            for violation in analysis.complexity_violations[:3]:
                all_issues.append(
                    {
                        "project": project_path,
                        "language": lang_name,
                        "type": "complexity",
                        "file": violation.get("file", ""),
                        "complexity": violation.get("complexity", 0),
                        "threshold": violation.get("threshold", 0),
                    }
                )

        return all_issues[:max_issues]

    @staticmethod
    def extract_test_failures(results_by_project: dict, max_projects: int) -> list[dict]:
        """Extract failing tests from analysis results."""
        failing_tests = []

        for project_key, analysis in results_by_project.items():
            lang_name, project_path = project_key.split(":", 1)

            if analysis.tests_failed > 0:
                failing_tests.append(
                    {
                        "project": project_path,
                        "language": lang_name,
                        "failed": analysis.tests_failed,
                        "total": analysis.tests_passed + analysis.tests_failed,
                    }
                )

        return failing_tests[:max_projects]

    @staticmethod
    def extract_projects_needing_tests(results_by_project: dict) -> list[dict]:
        """Find projects with no tests or low coverage."""
        projects_needing_tests = []

        for project_key, analysis in results_by_project.items():
            lang_name, project_path = project_key.split(":", 1)
            total_tests = analysis.tests_passed + analysis.tests_failed

            # Check if project needs tests
            needs_tests = False
            reason = ""

            if total_tests == 0:
                needs_tests = True
                reason = "no tests"
            elif hasattr(analysis, "coverage_percentage") and analysis.coverage_percentage:
                # If coverage exists and is below threshold (e.g., 60%)
                if analysis.coverage_percentage < 60.0:
                    needs_tests = True
                    reason = f"low coverage ({analysis.coverage_percentage:.1f}%)"

            if needs_tests:
                projects_needing_tests.append(
                    {"project": project_path, "language": lang_name, "reason": reason}
                )

        return projects_needing_tests
