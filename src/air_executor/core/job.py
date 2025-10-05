"""Job domain model and state management."""

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class JobState(str, Enum):
    """Job execution states."""

    WAITING = "waiting"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """
    Represents a job with tasks and execution state.

    A job is a collection of tasks that are executed by ephemeral runners.
    Jobs transition through states: waiting → working → completed/failed.
    """

    id: str = Field(..., description="Unique job identifier (UUID)")
    name: str = Field(..., description="Human-readable job name")
    state: JobState = Field(default=JobState.WAITING, description="Current job state")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Job creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last state update timestamp"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate job name (alphanumeric, dash, underscore only)."""
        if not v:
            raise ValueError("Job name cannot be empty")
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(
                "Job name must contain only alphanumeric characters, dashes, and underscores"
            )
        if len(v) > 100:
            raise ValueError("Job name must be 100 characters or less")
        return v

    def transition_to(self, new_state: JobState) -> None:
        """
        Transition job to new state with validation.

        Args:
            new_state: Target state to transition to

        Raises:
            ValueError: If state transition is invalid
        """
        # Validate state transitions
        valid_transitions = {
            JobState.WAITING: {JobState.WORKING, JobState.FAILED},
            JobState.WORKING: {JobState.WAITING, JobState.COMPLETED, JobState.FAILED},
            JobState.COMPLETED: set(),  # Terminal state
            JobState.FAILED: {JobState.WAITING},  # Can reset to waiting
        }

        if new_state not in valid_transitions.get(self.state, set()):
            raise ValueError(f"Invalid state transition: {self.state} → {new_state}")

        self.state = new_state
        self.updated_at = datetime.now(timezone.utc)

    def can_spawn_runner(self) -> bool:
        """
        Check if job is eligible for runner spawn.

        Returns:
            True if job can have a runner spawned, False otherwise
        """
        return self.state in {JobState.WAITING, JobState.WORKING}

    @classmethod
    def from_file(cls, path: Path) -> "Job":
        """
        Load job from state.json file.

        Args:
            path: Path to state.json file

        Returns:
            Job instance loaded from file

        Raises:
            FileNotFoundError: If state file doesn't exist
            ValueError: If state file is invalid JSON or missing required fields
        """
        if not path.exists():
            raise FileNotFoundError(f"Job state file not found: {path}")

        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in state file {path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load job from {path}: {e}")

    def to_file(self, path: Path) -> None:
        """
        Save job to state.json atomically.

        Uses temporary file + rename for atomic write to prevent corruption.

        Args:
            path: Path to state.json file (will be created/overwritten)

        Raises:
            OSError: If file write fails
        """

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file in same directory (for atomic rename)
        temp_path = path.parent / f".{path.name}.tmp"
        try:
            with open(temp_path, "w") as f:
                f.write(self.model_dump_json(indent=2))
                f.flush()
                # Ensure data is written to disk
                import os

                os.fsync(f.fileno())

            # Atomic rename
            temp_path.rename(path)
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to write job state to {path}: {e}")

    def to_dict(self) -> dict:
        """Convert job to dictionary representation."""
        return self.model_dump()

    def __str__(self) -> str:
        """String representation of job."""
        return f"Job(name={self.name}, state={self.state.value})"

    def __repr__(self) -> str:
        """Detailed representation of job."""
        return f"Job(id={self.id}, name={self.name}, state={self.state.value}, updated_at={self.updated_at})"
