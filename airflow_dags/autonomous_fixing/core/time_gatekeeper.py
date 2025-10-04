"""
Time Gatekeeper - Prevents wasteful rapid iterations.

Prevents:
- Too-fast iterations that accomplish nothing
- Infinite loops from quick failures
- API waste from rapid-fire calls

Tracks:
- Iteration timing
- Rapid iteration detection
- Early abort triggers
"""

import time
from dataclasses import dataclass


@dataclass
class IterationTiming:
    """Track iteration timing data."""

    iteration: int
    start_time: float
    end_time: float | None = None
    duration: float | None = None


class TimeGatekeeper:
    """
    Time gate keeper for iteration management.

    Responsibilities:
    - Enforce minimum iteration duration
    - Detect rapid iteration loops
    - Prevent API waste
    - Log timing anomalies

    Does NOT:
    - Control what happens in iterations (that's IterationEngine)
    - Make fixing decisions (just timing enforcement)
    """

    def __init__(self, config: dict):
        """
        Initialize time gatekeeper.

        Args:
            config: Configuration dict with time_gates settings
        """
        self.config = config

        # Configuration
        self.min_iteration_duration = self.gates.get("min_iteration_duration", 30)
        self.rapid_threshold = self.gates.get("rapid_iteration_threshold", 3)
        self.rapid_window = self.gates.get("rapid_iteration_window", 90)
        self.wrapper_min_duration = self.gates.get("wrapper_call_min_duration", 20)

        # Tracking
        self.iteration_history: list[IterationTiming] = []
        self.rapid_iterations: list[int] = []

    @property
    def gates(self) -> dict:
        """Get time gates configuration from config."""
        return self.config.get("time_gates", {})

    def start_iteration(self, iteration: int) -> float:
        """
        Mark iteration start and return start time.

        Args:
            iteration: Iteration number

        Returns:
            Start timestamp
        """
        start_time = time.time()

        self.iteration_history.append(IterationTiming(iteration=iteration, start_time=start_time))

        return start_time

    def end_iteration(self, iteration: int) -> dict:
        """
        Mark iteration end and check if gate passed.

        Args:
            iteration: Iteration number

        Returns:
            Dict with timing info and gate status
        """
        end_time = time.time()

        # Find this iteration's timing
        timing = next((t for t in self.iteration_history if t.iteration == iteration), None)

        if not timing:
            return {"error": "No start time found for iteration"}

        # Calculate duration
        timing.end_time = end_time
        timing.duration = end_time - timing.start_time

        # Check if too fast
        too_fast = timing.duration < self.min_iteration_duration

        if too_fast:
            self.rapid_iterations.append(iteration)

        # Build result
        result = {
            "iteration": iteration,
            "duration": timing.duration,
            "too_fast": too_fast,
            "wait_needed": max(0, self.min_iteration_duration - timing.duration) if too_fast else 0,
            "should_abort": self._check_should_abort(),
        }

        return result

    def _check_should_abort(self) -> bool:
        """
        Check if we should abort due to rapid iterations.

        Returns:
            True if should abort, False otherwise
        """
        # Need at least rapid_threshold rapid iterations
        if len(self.rapid_iterations) < self.rapid_threshold:
            return False

        # Check if recent rapid iterations within window
        recent_rapid = self.rapid_iterations[-self.rapid_threshold :]

        # Get timing for these iterations
        recent_timings = [
            t for t in self.iteration_history if t.iteration in recent_rapid and t.end_time
        ]

        if len(recent_timings) < self.rapid_threshold:
            return False

        # Check if all within rapid_window
        first_start = recent_timings[0].start_time
        last_end = recent_timings[-1].end_time

        window_duration = last_end - first_start

        return window_duration < self.rapid_window

    def wait_if_needed(self, iteration_result: dict):
        """
        Wait if iteration was too fast.

        Args:
            iteration_result: Result from end_iteration()
        """
        wait_time = iteration_result.get("wait_needed", 0)

        if wait_time > 0:
            print(f"   ⏸️  Iteration completed too quickly ({iteration_result['duration']:.1f}s)")
            print(f"      Waiting {wait_time:.1f}s to prevent rapid iteration waste...")
            time.sleep(wait_time)

    def get_timing_summary(self) -> dict:
        """
        Get timing summary for all iterations.

        Returns:
            Dict with timing statistics
        """
        completed = [t for t in self.iteration_history if t.duration is not None]

        if not completed:
            return {
                "total_iterations": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "rapid_count": 0,
            }

        durations = [t.duration for t in completed]

        return {
            "total_iterations": len(completed),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "rapid_count": len(self.rapid_iterations),
            "rapid_iterations": self.rapid_iterations,
        }

    def check_wrapper_call_duration(self, duration: float) -> dict:
        """
        Check if wrapper call duration is suspicious.

        Args:
            duration: Call duration in seconds

        Returns:
            Dict with validation result
        """
        is_suspicious = duration < self.wrapper_min_duration

        return {
            "duration": duration,
            "min_expected": self.wrapper_min_duration,
            "suspicious": is_suspicious,
            "reason": "Call completed too quickly - may have failed" if is_suspicious else None,
        }
