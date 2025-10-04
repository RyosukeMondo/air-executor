"""
Setup Tracker - Persistent state tracking for setup phases.

Tracks setup phase completion across sessions using Redis (primary) or
filesystem markers (fallback) to prevent redundant AI invocations.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union

from airflow_dags.autonomous_fixing.config.setup_tracker_config import SetupTrackerConfig

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class SetupTracker:
    """
    Track setup phase completion persistently across sessions.

    Responsibilities:
    - Store setup completion state in Redis (primary) or filesystem (fallback)
    - Query setup completion with TTL-based staleness detection (configurable)
    - Gracefully degrade when Redis unavailable
    - Prevent redundant AI invocations for already-completed setup

    Does NOT:
    - Execute setup operations (that's IssueFixer's job)
    - Validate cache integrity (that's PreflightValidator's job)
    - Orchestrate setup flow (that's IterationEngine's job)
    """

    def __init__(self, config: Optional[Union[SetupTrackerConfig, dict]] = None):
        """
        Initialize setup tracker with optional configuration.

        Args:
            config: Either SetupTrackerConfig object or dict (backward compatibility).
                   If dict, treated as redis_config.
                   If None, uses default configuration.

        Example:
            >>> # New style (recommended)
            >>> config = SetupTrackerConfig(state_dir=tmp_path / "state", ttl_days=1)
            >>> tracker = SetupTracker(config=config)

            >>> # Old style (backward compatible)
            >>> tracker = SetupTracker(redis_config={"redis_host": "localhost"})
        """
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.namespace = "autonomous_fix"

        # Handle backward compatibility: dict means old-style redis_config
        if isinstance(config, dict):
            self.config = SetupTrackerConfig(redis_config=config)
        elif config is None:
            self.config = SetupTrackerConfig()
        else:
            self.config = config

        self._initialize_redis(self.config.redis_config)
        self.config.state_dir.mkdir(parents=True, exist_ok=True)

    def _initialize_redis(self, redis_config: Optional[dict]) -> None:
        """Initialize Redis connection if config provided and library available."""
        if not redis_config:
            return

        if not REDIS_AVAILABLE:
            self.logger.warning(
                "SetupTracker: Redis library not installed, " "using filesystem fallback"
            )
            return

        self.redis_client = self._attempt_redis_connection(redis_config)

    def _attempt_redis_connection(self, redis_config: dict):
        """
        Attempt to establish Redis connection.

        Returns:
            Redis client on success, None on failure
        """
        try:
            client = redis.Redis(
                host=redis_config.get("redis_host", "localhost"),
                port=redis_config.get("redis_port", 6379),
                db=0,
                decode_responses=True,
                socket_connect_timeout=0.1,  # 100ms timeout
                socket_timeout=0.1,
            )
            self.namespace = redis_config.get("namespace", "autonomous_fix")
            client.ping()  # Test connection
            self.logger.info("SetupTracker: Redis connection established")
            return client
        except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
            self.logger.warning(
                "SetupTracker: Redis connection failed, " "using filesystem fallback: %s", e
            )
            return None
        except redis.RedisError as e:
            self.logger.warning("SetupTracker: Redis error, using filesystem fallback: %s", e)
            return None

    def mark_setup_complete(self, project: str, phase: str) -> None:
        """
        Mark setup phase as successfully completed.

        Stores completion marker in Redis (if available) and filesystem (always).
        Both storage mechanisms include timestamp for TTL validation.

        Args:
            project: Project path or identifier
            phase: Setup phase name ('hooks' or 'tests')
        """
        timestamp = datetime.now().isoformat()

        # Try Redis first (primary storage)
        if self._redis_store(project, phase):
            self.logger.debug(
                "SetupTracker: Marked %s complete in Redis for %s", phase, Path(project).name
            )

        # Always store filesystem marker (fallback + redundancy)
        self._filesystem_store(project, phase, timestamp)
        self.logger.debug(
            "SetupTracker: Marked %s complete in filesystem for %s", phase, Path(project).name
        )

    def is_setup_complete(self, project: str, phase: str) -> bool:
        """
        Check if setup phase was completed recently (<30 days).

        Queries Redis first, falls back to filesystem markers if Redis unavailable.
        Returns False if no marker found or marker is stale (>30 days).

        Args:
            project: Project path or identifier
            phase: Setup phase name ('hooks' or 'tests')

        Returns:
            True if setup completed recently, False otherwise
        """
        # Try Redis first (primary storage)
        if self._check_redis_completion(project, phase):
            return True

        # Fallback to filesystem
        return self._check_filesystem_completion(project, phase)

    def _check_redis_completion(self, project: str, phase: str) -> bool:
        """
        Check if setup completion exists in Redis.

        Returns:
            True if found in Redis, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = self._get_redis_key(project, phase)
            if self.redis_client.exists(key):
                self.logger.debug(
                    "SetupTracker: Found %s completion in Redis for %s", phase, Path(project).name
                )
                return True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            self.logger.warning("SetupTracker: Redis connection error, using filesystem: %s", e)
        except redis.RedisError as e:
            self.logger.warning("SetupTracker: Redis query failed, using filesystem: %s", e)

        return False

    def _check_filesystem_completion(self, project: str, phase: str) -> bool:
        """
        Check if setup completion exists in filesystem and is not stale.

        Returns:
            True if valid marker found, False otherwise
        """
        marker_path = self._get_marker_path(project, phase)
        if not marker_path.exists():
            return False

        return self._validate_marker_freshness(marker_path, project, phase)

    def _validate_marker_freshness(self, marker_path: Path, project: str, phase: str) -> bool:
        """
        Validate that marker file is fresh (not stale).

        Returns:
            True if marker is fresh, False if stale or invalid
        """
        try:
            timestamp_str = marker_path.read_text().strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp

            if age < timedelta(seconds=self.config.ttl_seconds):
                self.logger.debug(
                    "SetupTracker: Found valid %s marker (age: %dd) for %s",
                    phase,
                    age.days,
                    Path(project).name,
                )
                return True

            self.logger.debug(
                "SetupTracker: Found stale %s marker (age: %dd) for %s",
                phase,
                age.days,
                Path(project).name,
            )
            return False
        except (OSError, ValueError) as e:
            self.logger.warning("SetupTracker: Failed to read marker %s: %s", marker_path, e)
            return False

    def _get_redis_key(self, project: str, phase: str) -> str:
        """
        Generate Redis key for setup state.

        Uses project path hash to prevent cross-project leakage and handle
        long project paths that might exceed Redis key limits.

        Args:
            project: Project path or identifier
            phase: Setup phase name

        Returns:
            Redis key string (format: setup:{namespace}:{project_hash}:{phase})
        """
        # Hash project path for consistent, collision-resistant keys
        project_hash = hashlib.sha256(str(project).encode()).hexdigest()[:16]
        return f"setup:{self.namespace}:{project_hash}:{phase}"

    def _redis_store(self, project: str, phase: str) -> bool:
        """
        Store state in Redis with TTL.

        Args:
            project: Project path or identifier
            phase: Setup phase name

        Returns:
            True if stored successfully, False if Redis unavailable
        """
        if not self.redis_client:
            return False

        try:
            key = self._get_redis_key(project, phase)
            self.redis_client.setex(key, self.config.ttl_seconds, datetime.now().isoformat())
            return True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            self.logger.warning("SetupTracker: Redis connection error for %s: %s", phase, e)
            return False
        except redis.RedisError as e:
            self.logger.warning("SetupTracker: Redis store failed for %s: %s", phase, e)
            return False

    def _get_marker_path(self, project: str, phase: str) -> Path:
        """
        Get filesystem marker path for project and phase.

        Uses project path hash to create unique marker files.

        Args:
            project: Project path or identifier
            phase: Setup phase name

        Returns:
            Path to marker file
        """
        # Hash project path for unique marker files
        project_hash = hashlib.sha256(str(project).encode()).hexdigest()[:16]
        return self.config.state_dir / f"{project_hash}_{phase}_complete.marker"

    def _filesystem_store(self, project: str, phase: str, timestamp: str) -> None:
        """
        Store state as filesystem marker with timestamp.

        Uses atomic write operation and restrictive permissions (0o600).

        Args:
            project: Project path or identifier
            phase: Setup phase name
            timestamp: ISO format timestamp string
        """
        marker_path = self._get_marker_path(project, phase)

        try:
            # Atomic write with restrictive permissions
            marker_path.write_text(timestamp)
            marker_path.chmod(0o600)  # Owner read/write only
        except (OSError, PermissionError) as e:
            self.logger.warning("SetupTracker: Failed to write marker %s: %s", marker_path, e)
