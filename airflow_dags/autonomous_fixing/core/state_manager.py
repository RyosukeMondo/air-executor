"""
Project State Manager - Project-based state persistence with smart invalidation.

Manages project setup state in .ai-state/ directory with intelligent cache
invalidation based on configuration file changes, deletions, and staleness.
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import yaml

from ..domain.enums import Phase


class ProjectStateManager:
    """
    Manage project-based state with smart invalidation logic.

    Responsibilities:
    - Save setup state to project's .ai-state/ directory
    - Check if reconfiguration needed (state missing/stale/invalidated)
    - Compute configuration hashes for change detection
    - Ensure .ai-state/ is gitignored
    - Support backward compatibility with external cache

    Does NOT:
    - Execute setup operations (that's IssueFixer's job)
    - Orchestrate setup flow (that's IterationEngine's job)
    """

    STATE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days
    EXTERNAL_HOOK_CACHE_DIR = Path("config/precommit-cache")
    EXTERNAL_TEST_CACHE_DIR = Path("config/test-cache")

    def __init__(self, project_path: Path):
        """
        Initialize state manager for a project.

        Args:
            project_path: Path to project directory
        """
        self.project_path = project_path
        self.state_dir = project_path / ".ai-state"
        self.logger = logging.getLogger(__name__)

    def save_state(self, phase: str, data: dict) -> None:
        """
        Save state with metadata and validation markers.

        Creates .ai-state/ directory if missing, ensures gitignored,
        writes Markdown state file with YAML frontmatter.

        Args:
            phase: Setup phase name ('hooks' or 'tests')
            data: State data to save (hook/test configuration)
        """
        # Ensure .ai-state/ directory exists and is gitignored
        self.state_dir.mkdir(exist_ok=True)
        self._ensure_gitignore()

        # Compute config hash
        config_hash = self._get_config_hash(phase)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build and write state file
        state_file = self.state_dir / f"{phase}_state.md"
        content = self._build_state_content(phase, config_hash, timestamp, data)
        self._write_state_file(state_file, content)

    def _build_state_content(self, phase: str, config_hash: str, timestamp: str, data: dict) -> str:
        """Build state file content with metadata and validation markers."""
        status = "CONFIGURED" if phase == str(Phase.HOOKS) else "DISCOVERED"
        validation_markers = self._get_validation_markers(phase, timestamp)
        invalidation_triggers = self._get_invalidation_triggers(phase)

        return f"""---
generated: {timestamp}
status: {status}
config_hash: {config_hash}
---

# {phase.title()} Configuration State
Generated: {timestamp}
Status: {status}

## Configuration Hash
config_hash: {config_hash}

## Validation Markers
{validation_markers}

## Cache Invalidation Triggers
{invalidation_triggers}

## State Data
```yaml
{yaml.dump(data, default_flow_style=False)}
```
"""

    def _get_validation_markers(self, phase: str, timestamp: str) -> str:
        """Get validation markers for phase."""
        if phase == str(Phase.HOOKS):
            precommit_config = self.project_path / ".pre-commit-config.yaml"
            git_hook = self.project_path / ".git" / "hooks" / "pre-commit"
            return f"""- Hook file exists: {git_hook.exists()}
- Config file exists: {precommit_config.exists()}
- Last verified: {timestamp}"""

        # tests
        package_json = self.project_path / "package.json"
        return f"""- Config file exists: {package_json.exists()}
- Last verified: {timestamp}"""

    def _get_invalidation_triggers(self, phase: str) -> str:
        """Get invalidation triggers for phase."""
        if phase == str(Phase.HOOKS):
            return """- .pre-commit-config.yaml modified
- .git/hooks/pre-commit deleted
- State age > 30 days"""

        # tests
        return """- package.json modified
- State age > 30 days"""

    def _write_state_file(self, state_file: Path, content: str) -> None:
        """Write state file atomically."""
        temp_file = state_file.with_suffix(".tmp")
        try:
            temp_file.write_text(content, encoding="utf-8")
            temp_file.chmod(0o644)  # User writable, others read
            temp_file.replace(state_file)
            self.logger.info(f"Saved state to {state_file}")
        except Exception as e:
            self.logger.error(f"Failed to save state to {state_file}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def should_reconfigure(self, phase: str) -> Tuple[bool, str]:
        """
        Check if reconfiguration needed (state missing/stale/invalidated).

        Checks in order:
        1. Does project state exist?
        2. Is state file valid (parsable)?
        3. Is state fresh (<30 days)?
        4. Has config been modified?
        5. Have required files been deleted?
        6. Fallback to external cache (backward compatibility)

        Args:
            phase: Setup phase name ('hooks' or 'tests')

        Returns:
            (should_reconfigure, reason) where should_reconfigure is True if
            reconfiguration needed, and reason explains the decision
        """
        state_file = self.state_dir / f"{phase}_state.md"

        # Check 0: For hooks, detect existing configuration in filesystem
        existing_config_check = self._check_existing_hooks_config(phase, state_file)
        if existing_config_check is not None:
            return existing_config_check

        # Check 1: Does project state exist?
        if not state_file.exists():
            self.logger.debug(f"Project state missing for {phase}: {state_file}")
            return self._check_external_cache(phase)

        # Check 2: Is state file valid?
        validation_result = self._validate_state_file(state_file)
        if validation_result is None:
            return (True, "state file corrupted (deleted)")

        stored_hash, generated = validation_result

        # Check 3: Is state fresh (<30 days)?
        staleness_check = self._check_staleness(phase, generated)
        if staleness_check is not None:
            return staleness_check

        # Check 4 & 5: Config changes
        config_check = self._check_config_changes(phase, state_file, stored_hash)
        if config_check is not None:
            return config_check

        # Check 6: Required files deleted
        deletion_check = self._check_file_deletions(phase)
        if deletion_check is not None:
            return deletion_check

        # All checks passed - no reconfiguration needed
        return self._build_success_message(phase, generated)

    def _check_existing_hooks_config(self, phase: str, state_file: Path) -> Tuple[bool, str] | None:
        """Check for existing hooks configuration in filesystem."""
        if phase != "hooks" or state_file.exists():
            return None

        husky_dir = self.project_path / ".husky"
        precommit_config = self.project_path / ".pre-commit-config.yaml"

        if not (husky_dir.exists() or precommit_config.exists()):
            return None

        framework = "husky" if husky_dir.exists() else "pre-commit"
        self.logger.debug(f"Detected existing {framework} hooks in filesystem, skipping setup")
        return (False, f"{framework} hooks already configured")

    def _build_success_message(self, phase: str, generated: str) -> Tuple[bool, str]:
        """Build success message with age information."""
        generated_time = self._parse_timestamp(generated)
        if generated_time is None:
            return (False, f"{phase} configured (cached)")

        days_old = int((time.time() - generated_time) / 86400)
        return (False, f"{phase} configured {days_old}d ago (cached)")

    def _validate_state_file(self, state_file):
        """Validate state file format and extract metadata."""
        try:
            state_content = state_file.read_text(encoding="utf-8")
            return self._parse_state_content(state_file, state_content)
        except Exception as e:
            self.logger.error(f"Failed to parse state file {state_file}: {e}")
            state_file.unlink()
            return None

    def _parse_state_content(self, state_file: Path, state_content: str):
        """Parse state content and extract metadata."""
        if not state_content.startswith("---"):
            self.logger.warning(f"State file corrupted (no frontmatter): {state_file}")
            state_file.unlink()
            return None

        parts = state_content.split("---", 2)
        if len(parts) < 3:
            self.logger.warning(f"State file corrupted (invalid frontmatter): {state_file}")
            state_file.unlink()
            return None

        metadata = yaml.safe_load(parts[1])
        return metadata.get("config_hash", ""), metadata.get("generated", "")

    def _check_staleness(self, phase, generated):
        """Check if state is stale (>30 days)."""
        generated_time = self._parse_timestamp(generated)
        if generated_time is None:
            return None

        state_age = time.time() - generated_time
        if state_age <= self.STATE_MAX_AGE_SECONDS:
            return None

        days_old = int(state_age / 86400)
        self.logger.debug(f"State stale ({days_old}d) for {phase}")
        return (True, f"state stale ({days_old}d old)")

    def _parse_timestamp(self, generated):
        """Parse timestamp from state metadata."""
        try:
            if isinstance(generated, str):
                return datetime.fromisoformat(generated).timestamp()
            if isinstance(generated, datetime):
                return generated.timestamp()
            raise ValueError(f"Invalid timestamp type: {type(generated)}")
        except Exception as e:
            self.logger.warning(f"Failed to parse state timestamp: {e}")
            return None

    def _check_config_changes(self, phase, state_file, stored_hash):
        """Check if config has been modified (mtime or hash)."""
        # Mtime check
        mtime_check = self._check_config_mtime(phase, state_file)
        if mtime_check is not None:
            return mtime_check

        # Hash check
        return self._check_config_hash(phase, stored_hash)

    def _check_config_mtime(self, phase: str, state_file: Path):
        """Check if config file has been modified based on mtime."""
        config_file = self._get_config_file(phase)
        if not (config_file and config_file.exists()):
            return None

        state_mtime = state_file.stat().st_mtime
        if config_file.stat().st_mtime <= state_mtime:
            return None

        self.logger.debug(f"Config file modified for {phase}: {config_file.name}")
        return (True, f"{config_file.name} modified")

    def _check_config_hash(self, phase: str, stored_hash: str):
        """Check if config hash has changed."""
        current_hash = self._get_config_hash(phase)
        if current_hash == stored_hash:
            return None

        self.logger.debug(
            f"Config hash changed for {phase}: {stored_hash[:8]} -> {current_hash[:8]}"
        )
        return (True, "config content changed")

    def _check_file_deletions(self, phase):
        """Check if required files have been deleted."""
        if phase == str(Phase.HOOKS):
            return self._check_hooks_file_deletions()
        return self._check_tests_file_deletions()

    def _check_hooks_file_deletions(self):
        """Check if required hooks files have been deleted."""
        precommit_config = self.project_path / ".pre-commit-config.yaml"
        if not precommit_config.exists():
            return (True, ".pre-commit-config.yaml deleted")

        git_hook = self.project_path / ".git" / "hooks" / "pre-commit"
        if not git_hook.exists():
            return (True, "git hook deleted")

        return None

    def _check_tests_file_deletions(self):
        """Check if required test files have been deleted."""
        package_json = self.project_path / "package.json"
        if not package_json.exists():
            return (True, "package.json deleted")
        return None

    def _get_config_file(self, phase):
        """Get config file path for phase."""
        if phase == str(Phase.HOOKS):
            return self.project_path / ".pre-commit-config.yaml"
        return self.project_path / "package.json"

    def _get_config_hash(self, phase: str) -> str:
        """
        Compute SHA256 hash of relevant config files.

        Args:
            phase: Setup phase name ('hooks' or 'tests')

        Returns:
            SHA256 hash as hexadecimal string
        """
        hasher = hashlib.sha256()

        if phase == str(Phase.HOOKS):
            # Hash .pre-commit-config.yaml
            config_file = self.project_path / ".pre-commit-config.yaml"
            if config_file.exists():
                hasher.update(config_file.read_bytes())
        else:  # tests
            # Hash package.json
            config_file = self.project_path / "package.json"
            if config_file.exists():
                hasher.update(config_file.read_bytes())

        return hasher.hexdigest()

    def _ensure_gitignore(self) -> None:
        """
        Add .ai-state/ to .gitignore if not present.

        Creates .gitignore if it doesn't exist.
        """
        gitignore = self.project_path / ".gitignore"
        lines = self._read_gitignore_lines(gitignore)

        # Check if .ai-state/ already gitignored
        if any(line.strip() == ".ai-state/" for line in lines):
            return  # Already gitignored

        # Add .ai-state/ to gitignore
        lines.append(".ai-state/")
        gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.logger.info(f"Added .ai-state/ to {gitignore}")

    def _read_gitignore_lines(self, gitignore: Path) -> list:
        """Read gitignore lines or return empty list."""
        if not gitignore.exists():
            return []

        content = gitignore.read_text(encoding="utf-8")
        return content.splitlines()

    def _check_external_cache(self, phase: str) -> Tuple[bool, str]:
        """
        Check external cache for backward compatibility.

        Fallback to config/*-cache/ if project state doesn't exist.

        Args:
            phase: Setup phase name ('hooks' or 'tests')

        Returns:
            (should_reconfigure, reason) tuple
        """
        external_cache = self._get_external_cache_path(phase)

        if not external_cache.exists():
            return (True, f"no {phase} state found")

        cache_age = time.time() - external_cache.stat().st_mtime
        if cache_age > self.STATE_MAX_AGE_SECONDS:
            days_old = int(cache_age / 86400)
            return (True, f"external cache stale ({days_old}d)")

        # Log migration notice
        self.logger.info(
            f"Migrating state from config/ to .ai-state/ for {phase} "
            f"(using external cache, will save to project on next run)"
        )
        days_old = int(cache_age / 86400)
        return (False, f"{phase} configured {days_old}d ago (external cache)")

    def _get_external_cache_path(self, phase: str) -> Path:
        """Get external cache file path for phase."""
        project_name = self.project_path.name
        if phase == str(Phase.HOOKS):
            return self.EXTERNAL_HOOK_CACHE_DIR / f"{project_name}-hooks.yaml"
        return self.EXTERNAL_TEST_CACHE_DIR / f"{project_name}-tests.yaml"
