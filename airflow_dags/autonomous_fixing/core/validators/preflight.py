"""
Pre-flight Validator - Fast computational checks before AI invocation.

Validates setup completion state and cache integrity to determine if
setup phases can be skipped, preventing redundant AI calls.
"""

import logging
import time
import yaml
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Tuple, Iterator

from ..setup_tracker import SetupTracker


class PreflightValidator:
    """
    Perform fast computational checks to determine if setup phases can be skipped.

    Responsibilities:
    - Validate hook configuration cache and setup state
    - Validate test discovery cache and setup state
    - Check cache file integrity (YAML parsability, required fields)
    - Return skip decisions with explanatory reasons

    Does NOT:
    - Execute setup operations (that's IssueFixer's job)
    - Store setup state (that's SetupTracker's job)
    - Orchestrate setup flow (that's IterationEngine's job)
    """

    CACHE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 days
    HOOK_CACHE_DIR = Path('config/precommit-cache')
    TEST_CACHE_DIR = Path('config/test-cache')

    def __init__(self, setup_tracker: SetupTracker):
        """
        Initialize validator with setup state tracker.

        Args:
            setup_tracker: SetupTracker instance for querying setup completion
        """
        self.logger = logging.getLogger(__name__)
        self.setup_tracker = setup_tracker

    @contextmanager
    def _measure_validation(self, project_name: str, phase: str, start_time: float) -> Iterator[None]:
        """
        Context manager for validation timing measurement.

        Args:
            project_name: Name of project being validated
            phase: Phase name ('hooks' or 'tests')
            start_time: Validation start timestamp

        Yields:
            None
        """
        try:
            yield
        finally:
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(f"PreflightValidator: {phase.title()} validation for {project_name} ({elapsed:.0f}ms)")

    def _check_setup_state(
        self,
        project_path: Path,
        phase: str,
        start_time: float
    ) -> Optional[Tuple[bool, str]]:
        """
        Check if setup state is tracked as complete.

        Args:
            project_path: Path to project directory
            phase: Setup phase name ('hooks' or 'tests')
            start_time: Validation start timestamp for elapsed calculation

        Returns:
            (False, reason) if setup not complete, None if setup complete (continue checks)
        """
        if not self.setup_tracker.is_setup_complete(str(project_path), phase):
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: {phase.title()} setup not tracked as complete "
                f"for {project_path.name} ({elapsed:.0f}ms)"
            )
            return (False, "setup state not tracked")
        return None

    def _check_cache_freshness(
        self,
        cache_path: Path,
        project_name: str,
        phase: str,
        start_time: float
    ) -> Optional[Tuple[bool, str]]:
        """
        Check if cache file exists and is fresh (<7 days).

        Args:
            cache_path: Path to cache file
            project_name: Name of project for logging
            phase: Phase name ('hooks' or 'tests') for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if cache missing or stale, None if cache fresh (continue checks)
        """
        # Check existence
        if not cache_path.exists():
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(f"PreflightValidator: {phase.title()} cache missing for {project_name} ({elapsed:.0f}ms)")
            return (False, "cache file missing")

        # Check freshness
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age > self.CACHE_MAX_AGE_SECONDS:
            days_old = int(cache_age / 86400)
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: {phase.title()} cache stale ({days_old}d) "
                f"for {project_name} ({elapsed:.0f}ms)"
            )
            return (False, f"cache stale ({days_old}d old)")

        return None

    def _get_cache_age_days(self, cache_path: Path) -> int:
        """
        Get cache file age in days.

        Args:
            cache_path: Path to cache file

        Returns:
            Age in days (integer)
        """
        cache_age = time.time() - cache_path.stat().st_mtime
        return int(cache_age / 86400)

    def _check_hook_cache_validity(
        self,
        cache_path: Path,
        project_name: str,
        start_time: float
    ) -> Optional[Tuple[bool, str]]:
        """
        Check if hook cache is valid and complete.

        Args:
            cache_path: Path to cache file
            project_name: Name of project for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if cache invalid, None if cache valid (continue checks)
        """
        is_valid, reason = self._validate_hook_cache(cache_path)
        if not is_valid:
            elapsed = (time.time() - start_time) * 1000
            self.logger.warning(
                f"PreflightValidator: Hook cache invalid for {project_name}: {reason} ({elapsed:.0f}ms)"
            )
            return (False, f"cache invalid: {reason}")
        return None

    def _check_hook_files_exist(
        self,
        project_path: Path,
        project_name: str,
        start_time: float
    ) -> Optional[Tuple[bool, str]]:
        """
        Check if hook files exist on filesystem.

        Args:
            project_path: Path to project directory
            project_name: Name of project for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if files missing, None if files exist (continue checks)
        """
        precommit_config = project_path / '.pre-commit-config.yaml'
        git_hook = project_path / '.git' / 'hooks' / 'pre-commit'

        if not precommit_config.exists():
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: .pre-commit-config.yaml missing for {project_name} ({elapsed:.0f}ms)"
            )
            return (False, ".pre-commit-config.yaml not found")

        if not git_hook.exists():
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: .git/hooks/pre-commit missing for {project_name} ({elapsed:.0f}ms)"
            )
            return (False, "git hook not installed")

        return None

    def _check_test_cache_validity(
        self,
        cache_path: Path,
        project_name: str,
        start_time: float
    ) -> Optional[Tuple[bool, str]]:
        """
        Check if test cache is valid and complete.

        Args:
            cache_path: Path to cache file
            project_name: Name of project for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if cache invalid, None if cache valid (continue checks)
        """
        is_valid, reason = self._validate_test_cache(cache_path)
        if not is_valid:
            elapsed = (time.time() - start_time) * 1000
            self.logger.warning(
                f"PreflightValidator: Test cache invalid for {project_name}: {reason} ({elapsed:.0f}ms)"
            )
            return (False, f"cache invalid: {reason}")
        return None

    def can_skip_hook_config(self, project_path: Path) -> Tuple[bool, str]:
        """
        Check if pre-commit hooks setup can be skipped.

        Validates:
        1. Setup state tracked as complete (via SetupTracker)
        2. Hook cache file exists and is valid (<7 days)
        3. Hook cache integrity (YAML parsability, required fields)
        4. Actual hook files exist (.pre-commit-config.yaml, .git/hooks/pre-commit)

        Args:
            project_path: Path to project directory

        Returns:
            (can_skip, reason) where can_skip is True if setup can be skipped,
            and reason explains the decision
        """
        start_time = time.time()
        project_name = project_path.name
        cache_path = self.HOOK_CACHE_DIR / f'{project_name}-hooks.yaml'

        # Check 1: Is setup tracked as complete?
        if result := self._check_setup_state(project_path, 'hooks', start_time):
            return result

        # Check 2: Does cache file exist and is it fresh?
        if result := self._check_cache_freshness(cache_path, project_name, 'hooks', start_time):
            return result

        # Check 3: Is cache valid and complete?
        if result := self._check_hook_cache_validity(cache_path, project_name, start_time):
            return result

        # Check 4: Do actual hook files exist?
        if result := self._check_hook_files_exist(project_path, project_name, start_time):
            return result

        # All checks passed - setup can be skipped
        with self._measure_validation(project_name, 'hooks', start_time):
            cache_age_days = self._get_cache_age_days(cache_path)
            return (True, f"hooks configured {cache_age_days}d ago (saved 60s + $0.50)")

    def can_skip_test_discovery(self, project_path: Path) -> Tuple[bool, str]:
        """
        Check if test discovery can be skipped.

        Validates:
        1. Setup state tracked as complete (via SetupTracker)
        2. Test cache file exists and is valid (<7 days)
        3. Test cache integrity (YAML parsability, required fields)

        Args:
            project_path: Path to project directory

        Returns:
            (can_skip, reason) where can_skip is True if discovery can be skipped,
            and reason explains the decision
        """
        start_time = time.time()
        project_name = project_path.name
        cache_path = self.TEST_CACHE_DIR / f'{project_name}-tests.yaml'

        # Check 1: Is setup tracked as complete?
        if result := self._check_setup_state(project_path, 'tests', start_time):
            return result

        # Check 2: Does cache file exist and is it fresh?
        if result := self._check_cache_freshness(cache_path, project_name, 'tests', start_time):
            return result

        # Check 3: Is cache valid and complete?
        if result := self._check_test_cache_validity(cache_path, project_name, start_time):
            return result

        # All checks passed - discovery can be skipped
        with self._measure_validation(project_name, 'tests', start_time):
            cache_age_days = self._get_cache_age_days(cache_path)
            return (True, f"tests discovered {cache_age_days}d ago (saved 90s + $0.60)")

    def _validate_hook_cache(self, cache_path: Path) -> Tuple[bool, str]:
        """
        Validate hook configuration cache integrity.

        Checks:
        - YAML parsability
        - Presence of hook_framework.installed: true

        Args:
            cache_path: Path to cache file

        Returns:
            (is_valid, reason) where is_valid is True if cache is valid,
            and reason explains validation result
        """
        try:
            with open(cache_path) as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                return (False, "cache is not a YAML dict")

            # Check required field: hook_framework.installed
            hook_framework = data.get('hook_framework', {})
            if not isinstance(hook_framework, dict):
                return (False, "hook_framework is not a dict")

            if not hook_framework.get('installed'):
                return (False, "hook_framework.installed != true")

            return (True, "cache valid and complete")

        except yaml.YAMLError as e:
            return (False, f"YAML parse error: {e}")
        except (PermissionError, OSError) as e:
            return (False, f"cache file unreadable: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error validating hook cache {cache_path}: {e}")
            return (False, f"unexpected error: {e}")

    def _validate_test_cache(self, cache_path: Path) -> Tuple[bool, str]:
        """
        Validate test discovery cache integrity.

        Checks:
        - YAML parsability
        - Presence of required fields: test_framework, test_command, test_patterns

        Args:
            cache_path: Path to cache file

        Returns:
            (is_valid, reason) where is_valid is True if cache is valid,
            and reason explains validation result
        """
        try:
            with open(cache_path) as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                return (False, "cache is not a YAML dict")

            # Check required fields
            required_fields = ['test_framework', 'test_command', 'test_patterns']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                return (False, f"missing fields: {', '.join(missing_fields)}")

            # Validate non-empty values
            for field in required_fields:
                if not data[field]:
                    return (False, f"{field} is empty")

            return (True, "cache valid and complete")

        except yaml.YAMLError as e:
            return (False, f"YAML parse error: {e}")
        except (PermissionError, OSError) as e:
            return (False, f"cache file unreadable: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error validating test cache {cache_path}: {e}")
            return (False, f"unexpected error: {e}")
