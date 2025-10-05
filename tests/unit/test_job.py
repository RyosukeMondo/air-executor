"""Unit tests for Job domain model."""

import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from air_executor.core.job import Job, JobState


def test_job_creation():
    """Test job creation with valid data."""
    job = Job(id=str(uuid.uuid4()), name="test-job", state=JobState.WAITING)

    assert job.name == "test-job"
    assert job.state == JobState.WAITING
    assert isinstance(job.created_at, datetime)
    assert isinstance(job.updated_at, datetime)


def test_job_name_validation():
    """Test job name validation rules."""
    # Valid names
    Job(id=str(uuid.uuid4()), name="test-job-123")
    Job(id=str(uuid.uuid4()), name="test_job_123")
    Job(id=str(uuid.uuid4()), name="TestJob123")

    # Invalid names
    with pytest.raises(ValueError, match="alphanumeric"):
        Job(id=str(uuid.uuid4()), name="test job!")  # Space and special char

    with pytest.raises(ValueError, match="cannot be empty"):
        Job(id=str(uuid.uuid4()), name="")

    with pytest.raises(ValueError, match="100 characters"):
        Job(id=str(uuid.uuid4()), name="a" * 101)


def test_job_state_transitions():
    """Test valid and invalid state transitions."""
    job = Job(id=str(uuid.uuid4()), name="test-job")

    # Valid transitions
    job.transition_to(JobState.WORKING)
    assert job.state == JobState.WORKING

    job.transition_to(JobState.COMPLETED)
    assert job.state == JobState.COMPLETED

    # Invalid transition (completed is terminal)
    with pytest.raises(ValueError, match="Invalid state transition"):
        job.transition_to(JobState.WORKING)


def test_job_can_spawn_runner():
    """Test runner spawn eligibility."""
    job = Job(id=str(uuid.uuid4()), name="test-job", state=JobState.WAITING)
    assert job.can_spawn_runner() is True

    job.state = JobState.WORKING
    assert job.can_spawn_runner() is True

    job.state = JobState.COMPLETED
    assert job.can_spawn_runner() is False

    job.state = JobState.FAILED
    assert job.can_spawn_runner() is False


def test_job_file_serialization():
    """Test job to/from file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"

        # Create and save job
        original_job = Job(id=str(uuid.uuid4()), name="test-job", state=JobState.WORKING)
        original_job.to_file(path)

        # Load and verify
        loaded_job = Job.from_file(path)
        assert loaded_job.id == original_job.id
        assert loaded_job.name == original_job.name
        assert loaded_job.state == original_job.state


def test_job_atomic_write():
    """Test that job writes are atomic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"

        job = Job(id=str(uuid.uuid4()), name="test-job")
        job.to_file(path)

        # Verify no temp file left behind
        assert not (path.parent / f".{path.name}.tmp").exists()
        assert path.exists()
