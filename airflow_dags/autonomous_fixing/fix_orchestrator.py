#!/usr/bin/env python3
"""
Autonomous code fixing orchestrator.
Coordinates health monitoring, issue discovery, task execution, and completion detection.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from airflow_dags.autonomous_fixing.adapters.state.state_manager import StateManager
from airflow_dags.autonomous_fixing.domain.models.tasks import Task
from airflow_dags.autonomous_fixing.executor_runner import AirExecutorRunner
from airflow_dags.autonomous_fixing.issue_discovery import IssueDiscovery
from airflow_dags.autonomous_fixing.issue_grouping import IssueGrouper
from airflow_dags.autonomous_fixing.smart_health_monitor import SmartHealthMonitor


class FixOrchestrator:
    """Orchestrate autonomous code fixing with smart health monitoring"""

    def __init__(self, config_path: str):
        # Load configuration
        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Initialize components
        self.project_path = Path(self.config["target_project"]["path"])

        # Smart health monitor with tiered checks
        health_config = self.config.get("health_check", {})
        self.health_monitor = SmartHealthMonitor(
            str(self.project_path),
            file_size_threshold=health_config.get("file_size_threshold", 300),
            static_pass_threshold=health_config.get("static_pass_threshold", 0.6),
        )

        self.state_manager = StateManager(
            redis_host=self.config["redis"]["host"],
            redis_port=self.config["redis"]["port"],
            redis_db=self.config["redis"]["db"],
        )
        self.issue_discovery = IssueDiscovery(str(self.project_path))

        # Issue grouper for batch processing
        grouping_config = self.config.get("issue_grouping", {})
        self.issue_grouper = IssueGrouper(
            max_cleanup_batch_size=grouping_config.get("max_cleanup_batch_size", 50),
            max_location_batch_size=grouping_config.get("max_location_batch_size", 20),
            mega_batch_mode=grouping_config.get("mega_batch_mode", False),
        )

        self.executor = AirExecutorRunner(
            wrapper_path=self.config["air_executor"]["wrapper_path"],
            working_dir=str(self.project_path),
            timeout=self.config["air_executor"]["timeout"],
            auto_commit=self.config["air_executor"]["auto_commit"],
        )

        # Configuration
        self.completion_criteria = self.config["completion_criteria"]
        self.circuit_breaker = self.config["circuit_breaker"]
        self.batch_sizes = self.config["batch_sizes"]

        # State
        self.run_count = 0
        self.start_time = time.time()
        self.force_dynamic_check = False  # Flag to force dynamic checks

    def run(self, max_iterations: int = None, simulation: bool = False):
        """Run autonomous fixing orchestration"""
        print("🚀 Starting Autonomous Code Fixing Orchestrator")
        print("=" * 60)
        print(f"Project: {self.project_path.name}")
        print(f"Mode: {'SIMULATION' if simulation else 'LIVE'}")
        print("=" * 60)

        max_iter = max_iterations or self.circuit_breaker["max_total_runs"]

        while self.run_count < max_iter:
            self.run_count += 1
            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            print(f"\n{'='*60}")
            print(f"🔄 Run #{self.run_count} - {run_id}")
            print(f"{'='*60}")

            # Step 1: Smart Health check (tiered: static → dynamic if needed)
            smart_metrics = self.health_monitor.check_health(force_dynamic=self.force_dynamic_check)
            self.state_manager.record_run_result(run_id, smart_metrics.to_dict())

            # Step 2: Check completion (force dynamic check for accurate assessment)
            if smart_metrics.static.passes_static and not smart_metrics.dynamic:
                print("\n🔍 Static passed, running dynamic check for completion assessment...")
                smart_metrics = self.health_monitor.check_health(force_dynamic=True)

            if self._is_complete(smart_metrics):
                print("\n🎉 ALL COMPLETION CRITERIA MET!")
                self._print_final_summary()
                return 0

            # Step 3: Check circuit breaker
            if self._should_stop():
                print("\n⚠️ Circuit breaker triggered - stopping")
                self._print_final_summary()
                return 1

            # Step 4: Route to appropriate phase based on static metrics
            phase = self._determine_phase(smart_metrics)
            print(f"\n📍 Phase: {phase}")

            # Step 5: Discover issues
            tasks = self._discover_issues(phase)

            if not tasks:
                print("  ℹ️ No issues discovered in this phase")
                # If no issues but still unhealthy, might be a different phase
                continue

            # Step 6: Queue tasks
            self._queue_tasks(tasks, phase)

            # Step 7: Execute batch
            if simulation:
                batch_size = self.batch_sizes.get(f"{phase}_fixes", 5)
                print(f"\n🎭 SIMULATION: Would execute " f"{len(tasks[:batch_size])} tasks")
                time.sleep(2)  # Simulate execution time
            else:
                self._execute_batch(phase)

            # Step 8: Brief pause between runs
            time.sleep(1)

        print("\n⚠️ Maximum iterations reached")
        self._print_final_summary()
        return 1

    def _is_complete(self, smart_metrics) -> bool:
        """Check if all completion criteria are met"""
        criteria = self.completion_criteria
        static = smart_metrics.static
        dynamic = smart_metrics.dynamic

        # Check all criteria - return False if any fail, True if all pass
        return (
            self._check_static_criteria(criteria, static)
            and self._check_dynamic_criteria(criteria, dynamic)
            and self._check_stability_criteria(criteria)
        )

    def _check_static_criteria(self, criteria: dict, static) -> bool:
        """Check static analysis criteria"""
        # Build must pass
        if criteria.get("build_passes") and static.analysis_status != "pass":
            return False
        # Errors must be below threshold
        return static.analysis_errors <= criteria.get("max_lint_errors", 0)

    def _check_dynamic_criteria(self, criteria: dict, dynamic) -> bool:
        """Check dynamic test criteria"""
        if not dynamic or dynamic.total_tests == 0:
            return True
        # Test pass rate must meet threshold
        return dynamic.test_pass_rate >= criteria.get("min_test_pass_rate", 0.95)

    def _check_stability_criteria(self, criteria: dict) -> bool:
        """Check stability across recent runs"""
        stability_runs = criteria.get("stability_runs", 3)
        history = self.state_manager.get_run_history(count=stability_runs)

        # Need enough history
        if len(history) < stability_runs:
            return False

        # All recent runs must be healthy
        return all(self._is_run_healthy(run) for run in history)

    def _is_run_healthy(self, run: dict) -> bool:
        """Check if a single run is healthy"""
        run_metrics = run.get("metrics", {})
        static_data = run_metrics.get("static", {})
        return (
            static_data.get("analysis_status") == "pass"
            and static_data.get("analysis_errors", 0) == 0
        )

    def _should_stop(self) -> bool:
        """Check circuit breaker conditions"""
        # Check consecutive failures
        if self.state_manager.is_circuit_open(self.circuit_breaker["max_consecutive_failures"]):
            return True

        # Check maximum duration
        duration_hours = (time.time() - self.start_time) / 3600
        if duration_hours > self.circuit_breaker["max_duration_hours"]:
            return True

        # Check if no progress in last N runs
        history = self.state_manager.get_run_history(count=5)
        if len(history) >= 5:
            health_scores = [h["metrics"].get("overall_health_score", 0) for h in history]
            if len(set(health_scores)) == 1:  # No change
                print("  ⚠️ No progress in last 5 runs")
                return True

        return False

    def _determine_phase(self, smart_metrics) -> str:
        """Determine which phase to work on based on static metrics (priority order)"""
        # Priority: build/analysis > test > lint
        static = smart_metrics.static
        dynamic = smart_metrics.dynamic

        # Check static issues first
        if static.analysis_status == "fail" or static.analysis_errors > 0:
            return "build"

        # If static passes and we have dynamic data, check tests
        if dynamic:
            # Calculate failures from pass rate
            if dynamic.total_tests > 0:
                test_failed = dynamic.total_tests - int(
                    dynamic.total_tests * dynamic.test_pass_rate
                )
                if test_failed > 0:
                    return "test"

        # Check warnings
        if static.analysis_warnings > 0:
            return "lint"

        return "build"  # Default

    def _discover_issues(self, phase: str) -> list[Task]:
        """Discover issues for the given phase and group them"""
        # Discover raw issues
        if phase == "build":
            raw_tasks = self.issue_discovery.discover_build_issues()
        elif phase == "test":
            raw_tasks = self.issue_discovery.discover_test_failures()
        elif phase == "lint":
            raw_tasks = self.issue_discovery.discover_lint_issues()
        else:
            return []

        # Group similar issues for batch processing
        if raw_tasks:
            return self.issue_grouper.group_tasks(raw_tasks)

        return raw_tasks

    def _queue_tasks(self, tasks: list[Task], phase: str):
        """Queue discovered tasks"""
        # Limit batch size
        batch_size = self.batch_sizes.get(f"{phase}_fixes", 5)
        tasks_to_queue = tasks[:batch_size]

        print(f"\n📝 Queueing {len(tasks_to_queue)} tasks (found {len(tasks)} total)")

        for task in tasks_to_queue:
            self.state_manager.queue_task(task)

    def _execute_batch(self, phase: str):
        """Execute batch of tasks via air-executor"""
        batch_size = self.batch_sizes.get(f"{phase}_fixes", 5)
        tasks = self.state_manager.get_next_tasks(count=batch_size)

        if not tasks:
            return

        print(f"\n🔨 Executing {len(tasks)} tasks...")

        # Get session summary for context
        summary = self.state_manager.get_session_summary(phase)

        fixed_count = 0
        total_count = len(tasks)

        for i, task in enumerate(tasks, 1):
            print(f"\n  [{i}/{total_count}] {task.type}...")

            try:
                result = self.executor.run_task(task, summary)

                if result.success:
                    self.state_manager.mark_task_complete(task.id)
                    self.state_manager.reset_failure_count()
                    fixed_count += 1
                else:
                    self.state_manager.mark_task_failed(task.id, result.stderr)
                    self.state_manager.increment_failure_count()

            except Exception as e:
                print(f"    ❌ Exception: {e}")
                self.state_manager.mark_task_failed(task.id, str(e))
                self.state_manager.increment_failure_count()

        # Store session summary
        self.state_manager.store_session_summary(
            phase,
            {
                "fixed_count": fixed_count,
                "total_count": total_count,
                "success_rate": fixed_count / total_count if total_count > 0 else 0,
            },
        )

        print(f"\n  ✅ Fixed {fixed_count}/{total_count} tasks")

        # Force dynamic check on next iteration if we made fixes
        if fixed_count > 0:
            self.force_dynamic_check = True
            print("  📊 Will run full health check next iteration to verify fixes")

    def _print_final_summary(self):
        """Print final summary"""
        duration = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"Total runs: {self.run_count}")
        print(f"Duration: {duration/60:.1f} minutes")

        # Final health check (force dynamic for accurate final state)
        final_metrics = self.health_monitor.check_health(force_dynamic=False)
        print(f"\nFinal health: {final_metrics.overall_health_score:.0%}")
        print(f"  Static: {final_metrics.static.static_health_score:.0%}")
        if final_metrics.dynamic:
            print(f"  Dynamic: {final_metrics.dynamic.dynamic_health_score:.0%}")

        stats = self.state_manager.get_stats()
        print("\nQueue status:")
        print(f"  Remaining tasks: {stats['queue_size']}")
        print(f"  Failure count: {stats['failure_count']}")

        print("\nRun history:")
        for run in self.state_manager.get_run_history(count=3):
            m = run["metrics"]
            print(f"  - {run['run_id']}: health={m.get('overall_health_score', 0):.0%}")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python fix_orchestrator.py <config_file> [--simulation] [--max-iterations=N]")
        sys.exit(1)

    config_file = sys.argv[1]

    if not Path(config_file).exists():
        print(f"❌ Config file not found: {config_file}")
        sys.exit(1)

    simulation = "--simulation" in sys.argv

    max_iterations = None
    for arg in sys.argv:
        if arg.startswith("--max-iterations="):
            max_iterations = int(arg.split("=")[1])

    orchestrator = FixOrchestrator(config_file)
    exit_code = orchestrator.run(max_iterations=max_iterations, simulation=simulation)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
