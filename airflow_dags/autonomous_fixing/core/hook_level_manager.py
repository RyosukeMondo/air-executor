"""
Hook Level Manager - Progressive Pre-Commit Hook Enforcement

Manages upgrading pre-commit hooks as quality gates pass:
- Level 0: Framework only (no enforcement)
- Level 1: Type checking + build (after P1 passes)
- Level 2: + Unit tests (after P2 passes)
- Level 3: + Coverage + lint (after P3 passes)

Philosophy: Only enforce what has been proven to pass.
"""

from pathlib import Path
from typing import Dict

import yaml


class HookLevelManager:
    """Manages progressive pre-commit hook enforcement."""

    def __init__(self, config_path: str = 'config/hook-levels.yaml'):
        """
        Initialize hook level manager.

        Args:
            config_path: Path to hook levels configuration
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load hook levels configuration."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        else:
            # Return minimal default config
            return {
                'levels': {
                    0: {'name': 'framework_only', 'checks': []},
                    1: {'name': 'type_safety', 'checks': ['type_check', 'build']},
                    2: {'name': 'tests', 'checks': ['type_check', 'build', 'unit_tests']},
                    3: {'name': 'full_quality', 'checks': ['type_check', 'build', 'unit_tests', 'coverage', 'lint']}
                }
            }

    def get_current_level(self, project_path: str, language: str) -> int:
        """
        Get current hook enforcement level for project.

        Args:
            project_path: Project directory
            language: Project language

        Returns: Current level (0-3)
        """
        project = Path(project_path)

        # Check language-specific level files
        level_files = {
            'javascript': project / '.husky' / '.level',
            'python': project / '.pre-commit-level',
            'go': project / '.git' / 'hooks' / '.level',
            'flutter': project / '.git' / 'hooks' / '.level'
        }

        level_file = level_files.get(language)
        if level_file and level_file.exists():
            try:
                return int(level_file.read_text().strip())
            except (ValueError, FileNotFoundError):
                return 0

        return 0

    def _validate_level_range(self, target_level: int, current_level: int) -> tuple[bool, str]:
        """Validate target level is in valid range (SRP)"""
        if target_level < 1 or target_level > 3:
            return False, f"Invalid target level: {target_level}"
        if target_level <= current_level:
            return False, f"Already at level {current_level}"
        return True, ""

    def _verify_type_check_and_build(self, project_path: str, adapter) -> tuple[bool, str]:
        """Verify type checking and build succeed (SRP for level 1)"""
        print("      🔍 Verifying type checking...")
        result = adapter.run_type_check(project_path)
        if not result.success or result.errors:
            return False, f"Type checking failed: {len(result.errors)} errors"

        print("      🔨 Verifying build...")
        build_result = adapter.run_build(project_path)
        if not build_result.success:
            return False, f"Build failed: {build_result.error_message}"

        return True, ""

    def _verify_tests(self, project_path: str, adapter) -> tuple[bool, str]:
        """Verify tests exist and pass (SRP for level 2)"""
        print("      🧪 Verifying tests...")
        test_result = adapter.run_tests(project_path, strategy='minimal')
        if not test_result.success:
            return False, f"Tests failed: {test_result.tests_failed} failing"
        if test_result.tests_passed == 0:
            return False, "No tests found"
        return True, ""

    def _verify_coverage_and_linting(self, project_path: str, adapter) -> tuple[bool, str]:
        """Verify coverage meets threshold and linting passes (SRP for level 3)"""
        print("      📈 Verifying coverage...")
        cov_result = adapter.analyze_coverage(project_path)
        if not hasattr(cov_result, 'coverage_percentage') or not cov_result.coverage_percentage:
            return False, "Coverage analysis unavailable"
        if cov_result.coverage_percentage < 60.0:
            return False, f"Coverage {cov_result.coverage_percentage:.1f}% < 60%"

        print("      🔧 Verifying linting...")
        lint_result = adapter.static_analysis(project_path)
        if lint_result.errors and len(lint_result.errors) > 0:
            return False, f"Linting failed: {len(lint_result.errors)} errors"

        return True, ""

    def can_upgrade_to_level(self, project_path: str, language: str,
                            target_level: int, adapter) -> tuple[bool, str]:
        """
        Check if project quality allows upgrading to target level.

        Args:
            project_path: Project directory
            language: Project language
            target_level: Target hook level (1-3)
            adapter: Language adapter for running checks

        Returns: (can_upgrade, reason)
        """
        current_level = self.get_current_level(project_path, language)
        valid, reason = self._validate_level_range(target_level, current_level)
        if not valid:
            return False, reason

        if target_level >= 1:
            valid, reason = self._verify_type_check_and_build(project_path, adapter)
            if not valid:
                return False, reason

        if target_level >= 2:
            valid, reason = self._verify_tests(project_path, adapter)
            if not valid:
                return False, reason

        if target_level >= 3:
            valid, reason = self._verify_coverage_and_linting(project_path, adapter)
            if not valid:
                return False, reason

        return True, "All verification checks passed"

    def upgrade_to_level(self, project_path: str, language: str, target_level: int) -> bool:
        """
        Upgrade hooks to target level.

        Args:
            project_path: Project directory
            language: Project language
            target_level: Target hook level (1-3)

        Returns: True if upgrade successful
        """
        project = Path(project_path)
        level_config = self.config['levels'][target_level]

        print(f"\n   🔒 Upgrading hooks to Level {target_level}: {level_config['name']}")

        # Update level file
        level_files = {
            'javascript': project / '.husky' / '.level',
            'python': project / '.pre-commit-level',
            'go': project / '.git' / 'hooks' / '.level',
            'flutter': project / '.git' / 'hooks' / '.level'
        }

        level_file = level_files.get(language)
        if level_file:
            level_file.parent.mkdir(parents=True, exist_ok=True)
            level_file.write_text(str(target_level))
            print(f"      ✅ Updated {level_file.relative_to(project)}")
        else:
            print(f"      ⚠️  Unknown language: {language}")
            return False

        # Update metadata cache
        self._update_metadata_cache(project_path, language, target_level, level_config)

        # Display what's now enforced
        print("\n   📋 Now enforcing:")
        for check in level_config.get('checks', []):
            print(f"      • {check['id']}" if isinstance(check, dict) else f"      • {check}")

        return True

    def _update_metadata_cache(self, project_path: str, language: str,
                               level: int, level_config: Dict):
        """Update hook metadata cache with new level."""
        from datetime import datetime

        project_name = Path(project_path).name
        cache_dir = Path('config/precommit-cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{project_name}-hooks.yaml'

        # Load existing cache or create new
        if cache_file.exists():
            with open(cache_file) as f:
                cache = yaml.safe_load(f) or {}
        else:
            cache = {
                'project_name': project_name,
                'language': language,
                'levels': {},
                'progression_history': []
            }

        # Update current level
        cache['current_level'] = level

        # Record level activation
        cache['levels'][level] = {
            'enabled_at': datetime.now().isoformat(),
            'status': 'active',
            'checks': level_config.get('checks', [])
        }

        # Add to progression history
        cache['progression_history'].append({
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'reason': f"Phase {self._level_to_phase(level)} gate passed"
        })

        # Save cache
        with open(cache_file, 'w') as f:
            yaml.dump(cache, f, default_flow_style=False, sort_keys=False)

    def _level_to_phase(self, level: int) -> str:
        """Map hook level to phase name."""
        return {0: 'SETUP', 1: 'P1', 2: 'P2', 3: 'P3'}.get(level, 'UNKNOWN')

    def upgrade_after_gate_passed(self, project_path: str, language: str,
                                 phase: str, gate_passed: bool, score: float,
                                 adapter) -> bool:
        """
        Attempt to upgrade hooks after phase gate passes.

        Args:
            project_path: Project directory
            language: Project language
            phase: Phase name ('p1', 'p2', 'p3')
            gate_passed: Whether gate passed
            score: Phase score (0.0-1.0)
            adapter: Language adapter for verification

        Returns: True if upgrade successful
        """
        if not gate_passed:
            return False

        # Determine target level based on phase
        target_level = {
            'p1': 1,  # Type safety
            'p2': 2,  # + Tests
            'p3': 3   # + Coverage + lint
        }.get(phase.lower())

        if target_level is None:
            return False

        current_level = self.get_current_level(project_path, language)

        if target_level <= current_level:
            # Already at this level or higher
            return False

        print(f"\n{'='*80}")
        print(f"🎉 {phase.upper()} gate passed (score: {score:.1%})!")
        print(f"   Attempting to upgrade hooks: Level {current_level} → Level {target_level}")
        print(f"{'='*80}")

        # Verify quality before upgrading
        can_upgrade, reason = self.can_upgrade_to_level(
            project_path, language, target_level, adapter
        )

        if not can_upgrade:
            print(f"\n   ⚠️  Cannot upgrade to Level {target_level}: {reason}")
            print(f"   Staying at Level {current_level}")
            print("   Fix these issues to enable higher enforcement.")
            return False

        # Perform upgrade
        success = self.upgrade_to_level(project_path, language, target_level)

        if success:
            print("\n   ✅ Hooks upgraded successfully!")
            print("   Quality cannot regress below this level.")
            print(f"   Future commits must pass Level {target_level} checks.")

        return success

    def detect_regression(self, project_path: str, language: str, adapter) -> bool:
        """
        Detect if quality has regressed below current hook level.

        Args:
            project_path: Project directory
            language: Project language
            adapter: Language adapter for checks

        Returns: True if regression detected
        """
        current_level = self.get_current_level(project_path, language)

        if current_level == 0:
            return False  # No enforcement, no regression

        # Run checks for current level
        can_pass, reason = self.can_upgrade_to_level(
            project_path, language, current_level, adapter
        )

        if not can_pass:
            print("\n⚠️  QUALITY REGRESSION DETECTED!")
            print(f"   Current Level {current_level} checks no longer pass:")
            print(f"   {reason}")
            print("\n   Action required:")
            print("   1. Fix the quality issues immediately")
            print(f"   2. Or consider rolling back to Level {current_level - 1}")
            return True

        return False

    def get_level_info(self, level: int) -> Dict:
        """Get configuration info for a hook level."""
        return self.config['levels'].get(level, {})

    def get_enforcement_summary(self, project_path: str, language: str) -> str:
        """
        Get human-readable summary of current enforcement.

        Args:
            project_path: Project directory
            language: Project language

        Returns: Formatted summary string
        """
        current_level = self.get_current_level(project_path, language)
        level_info = self.get_level_info(current_level)

        summary = "\n📊 Pre-Commit Hook Enforcement Status\n"
        summary += f"{'='*60}\n"
        summary += f"Current Level: {current_level} ({level_info.get('name', 'unknown')})\n"
        summary += f"Description: {level_info.get('description', 'N/A')}\n\n"

        if current_level == 0:
            summary += "⏭️  No enforcement yet (learning mode)\n"
            summary += "   Hooks will be enabled as quality gates pass\n"
        else:
            summary += "Enforced Checks:\n"
            for check in level_info.get('checks', []):
                check_id = check['id'] if isinstance(check, dict) else check
                summary += f"  ✅ {check_id}\n"

        summary += f"{'='*60}\n"

        return summary
