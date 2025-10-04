"""
Debug Logger - Structured logging for autonomous fixing.

Provides:
- Structured JSON logging for all operations
- Claude wrapper call tracking
- Iteration timing and metrics
- Fix success/failure tracking
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class WrapperCall:
    """Track a claude_wrapper invocation."""

    timestamp: str
    project: str
    prompt_type: str  # 'analysis', 'fix_error', 'fix_test', 'create_test'
    duration: float
    success: bool
    error: str | None = None


@dataclass
class IterationMetrics:
    """Track iteration timing and results."""

    iteration: int
    start_time: str
    end_time: str
    duration: float
    phase: str  # 'p1_analysis', 'p1_fix', 'p2_test', 'p2_fix', 'p2_create'
    success: bool
    fixes_applied: int = 0
    tests_created: int = 0


class DebugLogger:
    """
    Structured debug logger for autonomous fixing.

    Responsibilities:
    - Log all claude_wrapper calls with timing
    - Track iteration metrics
    - Log fix results with structured data
    - Provide JSON-formatted debug output
    - Track performance metrics

    Does NOT:
    - Control execution flow (that's IterationEngine's job)
    - Make decisions (just records what happens)
    """

    def __init__(self, config: dict, project_name: str):
        """
        Initialize debug logger.

        Args:
            config: Configuration dict with debug settings
            project_name: Name of project being fixed
        """
        self.config = config
        self.project_name = project_name
        self.debug_config = config.get("debug", {})
        self.enabled = self.debug_config.get("enabled", True)

        if not self.enabled:
            self.logger = None
            return

        # Setup logging directory
        log_dir = Path(self.debug_config.get("log_dir", "logs/debug"))
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create session log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{project_name}_{timestamp}.jsonl"

        # Configure logger
        self.logger = logging.getLogger(f"debug.{project_name}")
        self.logger.setLevel(logging.DEBUG)

        # JSON handler
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

        # Metrics tracking
        self.metrics = {
            "wrapper_calls": [],
            "iterations": [],
            "fixes": {"attempted": 0, "successful": 0},
            "tests": {"created": 0, "fixed": 0},
            "setup_skips": {"hooks": {}, "tests": {}},
        }

        self.log_event(
            "session_start",
            {
                "project": project_name,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "max_iterations": config.get("execution", {}).get("max_iterations"),
                    "debug_enabled": True,
                },
            },
        )

    def log_event(self, event_type: str, data: dict[str, Any]):
        """Log a structured event."""
        if not self.enabled or not self.logger:
            return

        event = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "project": self.project_name,
            **data,
        }

        self.logger.debug(json.dumps(event))

    def log_wrapper_call(
        self,
        prompt_type: str,
        project: str,
        duration: float,
        success: bool,
        error: str | None = None,
        response: dict | None = None,
    ):
        """Log a claude_wrapper call."""
        if not self.enabled:
            return

        call = WrapperCall(
            timestamp=datetime.now().isoformat(),
            project=project,
            prompt_type=prompt_type,
            duration=duration,
            success=success,
            error=error,
        )

        self.metrics["wrapper_calls"].append(asdict(call))

        event_data = asdict(call)
        if response and self.debug_config.get("log_levels", {}).get("wrapper_responses"):
            event_data["response"] = response

        self.log_event("wrapper_call", event_data)

    def log_iteration_start(self, iteration: int, phase: str):
        """Log iteration start."""
        if not self.enabled:
            return

        self.log_event(
            "iteration_start",
            {"iteration": iteration, "phase": phase, "timestamp": datetime.now().isoformat()},
        )

    def log_iteration_end(
        self, iteration: int, phase: str, duration: float, success: bool, **kwargs
    ):
        """Log iteration end with metrics."""
        if not self.enabled:
            return

        metrics = IterationMetrics(
            iteration=iteration,
            start_time=(datetime.now().timestamp() - duration).__str__(),
            end_time=datetime.now().isoformat(),
            duration=duration,
            phase=phase,
            success=success,
            **kwargs,
        )

        self.metrics["iterations"].append(asdict(metrics))

        self.log_event("iteration_end", asdict(metrics))

    def log_fix_result(
        self,
        fix_type: str,
        target: str,
        success: bool,
        duration: float,
        details: dict | None = None,
    ):
        """Log a fix attempt result."""
        if not self.enabled:
            return

        self.metrics["fixes"]["attempted"] += 1
        if success:
            self.metrics["fixes"]["successful"] += 1

        event_data = {
            "fix_type": fix_type,
            "target": target,
            "success": success,
            "duration": duration,
        }

        if details:
            event_data["details"] = details

        self.log_event("fix_result", event_data)

    def log_test_creation(self, project: str, success: bool, tests_created: int = 0):
        """Log test creation attempt."""
        if not self.enabled:
            return

        if success:
            self.metrics["tests"]["created"] += tests_created

        self.log_event(
            "test_creation",
            {"project": project, "success": success, "tests_created": tests_created},
        )

    def log_setup_skip_stats(
        self, phase: str, skipped: int, total: int, time_saved: float, cost_saved: float
    ):
        """
        Log setup skip statistics.

        Args:
            phase: Setup phase ('hooks' or 'tests')
            skipped: Number of projects skipped
            total: Total number of projects
            time_saved: Time saved in seconds
            cost_saved: Cost saved in dollars
        """
        if not self.enabled:
            return

        stats = {
            "skipped": skipped,
            "total": total,
            "time_saved": time_saved,
            "cost_saved": cost_saved,
            "skip_rate": skipped / total if total > 0 else 0.0,
        }

        self.metrics["setup_skips"][phase] = stats

        self.log_event("setup_skip_stats", {"phase": phase, **stats})

    def get_metrics(self) -> dict:
        """Get current metrics snapshot."""
        # Calculate total setup savings
        total_time_saved = sum(
            stats.get("time_saved", 0) for stats in self.metrics["setup_skips"].values()
        )
        total_cost_saved = sum(
            stats.get("cost_saved", 0) for stats in self.metrics["setup_skips"].values()
        )

        return {
            **self.metrics,
            "summary": {
                "total_wrapper_calls": len(self.metrics["wrapper_calls"]),
                "total_iterations": len(self.metrics["iterations"]),
                "fix_success_rate": (
                    self.metrics["fixes"]["successful"] / self.metrics["fixes"]["attempted"]
                    if self.metrics["fixes"]["attempted"] > 0
                    else 0.0
                ),
                "avg_wrapper_duration": (
                    sum(c["duration"] for c in self.metrics["wrapper_calls"])
                    / len(self.metrics["wrapper_calls"])
                    if self.metrics["wrapper_calls"]
                    else 0.0
                ),
                "total_time_saved": total_time_saved,
                "total_cost_saved": total_cost_saved,
            },
        }

    def log_session_end(self, reason: str):
        """Log session end with final metrics."""
        if not self.enabled:
            return

        self.log_event("session_end", {"reason": reason, "metrics": self.get_metrics()})
