"""
Prompt generation for executor_runner.py

Extracted to reduce file size and improve maintainability.
"""

from typing import Dict, Optional


class PromptGenerator:
    """Generates prompts for different types of fix tasks"""

    @staticmethod
    def _categorize_issue(message: str) -> str:
        """Categorize issue based on message content"""
        msg_lower = message.lower()
        if "import" in msg_lower and "unused" in msg_lower:
            return "Unused Imports"
        if "type" in msg_lower:
            return "Type Errors"
        if "null" in msg_lower:
            return "Null Safety"
        if "override" in msg_lower:
            return "Missing Overrides"
        return "Other Issues"

    @staticmethod
    def _group_issues_by_category(issues: list) -> dict:
        """Group issues by category"""
        by_category = {}
        for issue in issues:
            category = PromptGenerator._categorize_issue(issue.get("message", ""))
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)
        return by_category

    @staticmethod
    def _format_categorized_issues(by_category: dict) -> list:
        """Format categorized issues for display"""
        formatted = []
        for category, issues in sorted(by_category.items()):
            formatted.append(f"\n**{category}** ({len(issues)} issues):")
            for i, issue in enumerate(issues[:10], 1):
                formatted.append(
                    f"  {i}. {issue['file']}:{issue['line']} - {issue['message'][:70]}"
                )
            if len(issues) > 10:
                formatted.append(f"  ... and {len(issues) - 10} more")
        return formatted

    @staticmethod
    def batch_fix_prompt(task, summary: Optional[Dict]) -> str:
        """Generate prompt for batch fix"""
        batch_type = task.batch_type if hasattr(task, "batch_type") else "issues"
        related_issues = task.related_issues if hasattr(task, "related_issues") else []

        # Check if this is a mega batch
        is_mega = batch_type == "mega_comprehensive"

        if is_mega:
            return PromptGenerator.mega_batch_prompt(task, summary)

        # Regular batch: focused on one type or location
        issue_list = []
        for i, issue in enumerate(related_issues[:20], 1):
            issue_list.append(f"{i}. {issue['file']}:{issue['line']} - {issue['message'][:80]}")

        if len(related_issues) > 20:
            issue_list.append(f"... and {len(related_issues) - 20} more similar issues")

        issues_text = "\n".join(issue_list)

        # Get unique files
        files = list(set(issue["file"] for issue in related_issues if issue.get("file")))
        files_text = "\n".join([f"  - {f}" for f in files[:15]])
        if len(files) > 15:
            files_text += f"\n  ... and {len(files) - 15} more files"

        # Determine commit message based on batch type
        if "cleanup" in str(task.type):
            commit_prefix = "chore"
            commit_desc = f"remove all {batch_type}"
        elif "location" in str(task.type):
            commit_prefix = "fix"
            commit_desc = batch_type.replace("_", " ")
        else:
            commit_prefix = "fix"
            commit_desc = f"{batch_type} across {len(files)} files"

        prompt = f"""Fix ALL {len(related_issues)} {batch_type} issues in Flutter project.

**Scope**: {batch_type}
**Files Affected** ({len(files)} total):
{files_text}

**All Issues to Fix**:
{issues_text}

**Your Task**:
1. Fix ALL {len(related_issues)} issues listed above
2. Work through files systematically
3. Apply consistent patterns across similar issues
4. Look for root causes that affect multiple issues
5. Run `flutter analyze --no-pub` to verify all fixes
6. **IMPORTANT**: Create ONE commit with all changes:
   ```bash
   git add -A
   git commit -m "{commit_prefix}: {commit_desc}"
   ```

This is a focused batch fix. Handle all {len(related_issues)} issues comprehensively in one session.
DO NOT skip any issues. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} batches\n"

        return prompt

    @staticmethod
    def mega_batch_prompt(task, summary: Optional[Dict]) -> str:
        """Generate prompt for mega batch (all issues in phase)"""
        related_issues = task.related_issues if hasattr(task, "related_issues") else []

        by_category = PromptGenerator._group_issues_by_category(related_issues)
        issues_by_category = PromptGenerator._format_categorized_issues(by_category)
        files = list(set(issue["file"] for issue in related_issues if issue.get("file")))

        prompt = f"""COMPREHENSIVE FIX: Fix ALL {len(related_issues)} issues in Flutter project.

**Scope**: Complete phase fix (all discovered issues)
**Total Issues**: {len(related_issues)}
**Affected Files**: {len(files)}

**Issues Organized by Category**:
{chr(10).join(issues_by_category)}

**Your Mission**:
1. Fix ALL {len(related_issues)} issues across all categories
2. Start with cleanup issues (unused imports, formatting)
3. Then fix type errors and null safety systematically
4. Work through files logically (by directory/module)
5. Run `flutter analyze --no-pub` frequently to track progress
6. **IMPORTANT**: Create ONE comprehensive commit:
   ```bash
   git add -A
   git commit -m "fix: comprehensive cleanup of {len(related_issues)} issues"
   ```

This is a COMPREHENSIVE fix session. Take your time, be systematic, and fix everything.
You can modify as many files as needed. This is your opportunity to clean up the entire codebase.

DO NOT skip any issues. DO NOT skip the commit step.
"""

        if summary:
            fixed_count = summary.get("fixed_count", 0)
            prompt += f"\n\n**Previous session**: Fixed {fixed_count} comprehensive batches\n"

        return prompt

    @staticmethod
    def build_fix_prompt(task, summary: Optional[Dict]) -> str:
        """Generate prompt for build error fix"""
        commit_msg = task.message[:60].replace('"', "'").replace("\n", " ")

        prompt = f"""Fix this Flutter build error:

**File**: {task.file or 'Unknown'}
**Line**: {task.line or '?'}
**Error**: {task.message}

**Code Context**:
```
{task.context}
```

**Instructions**:
1. Analyze the error carefully
2. Implement a proper fix (make necessary changes, don't be overly minimal)
3. Consider if related code needs updates for consistency
4. Run `flutter analyze --no-pub` to verify the fix
5. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "fix: {commit_msg}"
   ```

DO NOT skip the commit step. Changes must be committed before finishing.
"""

        if summary:
            fixed = summary.get("fixed_count", 0)
            total = summary.get("total_count", 0)
            prompt += f"\n\n**Previous session**: Fixed {fixed} of {total} issues\n"

        return prompt

    @staticmethod
    def test_fix_prompt(task, summary: Optional[Dict]) -> str:
        """Generate prompt for test failure fix"""
        commit_msg = task.message[:60].replace('"', "'").replace("\n", " ")

        prompt = f"""Fix this failing Flutter test:

**Test**: {task.message}
**File**: {task.file or 'Unknown'}

**Test Context**:
```
{task.context}
```

**Instructions**:
1. Understand why the test is failing
2. Fix the implementation (NOT the test unless it's clearly wrong)
3. Make comprehensive changes if needed across related files
4. Run `flutter test` to verify
5. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "fix(test): {commit_msg}"
   ```

Fix the root cause, not the symptoms. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} tests\n"

        return prompt

    @staticmethod
    def lint_fix_prompt(task, summary: Optional[Dict]) -> str:
        """Generate prompt for lint issue fix"""
        commit_msg = task.message[:60].replace('"', "'").replace("\n", " ")

        prompt = f"""Fix this Flutter lint issue:

**File**: {task.file or 'Unknown'}
**Issue**: {task.message}

**Code Context**:
```
{task.context}
```

**Instructions**:
1. Understand the lint rule violation
2. Fix according to Dart/Flutter best practices
3. Apply similar fixes to related code if applicable
4. Run `flutter analyze --no-pub` to verify
5. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "style: {commit_msg}"
   ```

Follow Flutter style guide exactly. DO NOT skip the commit step.
"""

        if summary:
            prompt += (
                f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} lint issues\n"
            )

        return prompt

    @staticmethod
    def generic_fix_prompt(task, summary: Optional[Dict]) -> str:
        """Generic fix prompt"""
        commit_msg = task.message[:60].replace('"', "'").replace("\n", " ")

        prompt = f"""Fix this issue in the Flutter project:

**Type**: {task.type}
**Description**: {task.message}
**Location**: {task.file}:{task.line if task.line else '?'}

**Context**:
```
{task.context}
```

**Instructions**:
1. Analyze and understand the issue
2. Implement a targeted fix
3. Verify the fix works
4. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "fix: {commit_msg}"
   ```

Focus on quality over speed. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session summary**: {summary}\n"

        return prompt
