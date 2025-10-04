#!/usr/bin/env python3
"""
State management system using Redis.
Manages task queue, session summaries, and run history.
"""

import json
import uuid
from datetime import datetime

import redis

from ...domain.interfaces import IStateStore, ITaskRepository

# Import domain models and interfaces
from ...domain.models import Task


class StateManager(IStateStore, ITaskRepository):
    """Manage state using Redis"""

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, db=redis_db, decode_responses=True
        )
        self.prefix = "autonomous_fix:"

    # Task Queue Management

    def queue_task(self, task: Task):
        """Add task to priority queue"""
        task_key = f"{self.prefix}task:{task.id}"
        queue_key = f"{self.prefix}task_queue"

        # Store task data
        self.redis.set(task_key, json.dumps(task.to_dict()))

        # Add to priority queue (sorted set, lower score = higher priority)
        self.redis.zadd(queue_key, {task.id: task.priority})

        print(f"📝 Queued task: {task.type} (priority {task.priority})")

    def get_next_tasks(self, count: int = 5) -> list[Task]:
        """Get highest priority tasks"""
        queue_key = f"{self.prefix}task_queue"

        # Get task IDs in priority order
        task_ids = self.redis.zrange(queue_key, 0, count - 1)

        tasks = []
        for task_id in task_ids:
            task_key = f"{self.prefix}task:{task_id}"
            task_data = self.redis.get(task_key)
            if task_data:
                tasks.append(Task.from_dict(json.loads(task_data)))

        return tasks

    def mark_task_complete(self, task_id: str):
        """Remove completed task from queue"""
        queue_key = f"{self.prefix}task_queue"
        task_key = f"{self.prefix}task:{task_id}"

        # Remove from queue
        self.redis.zrem(queue_key, task_id)

        # Move to completed set with TTL
        completed_key = f"{self.prefix}completed:{task_id}"
        task_data = self.redis.get(task_key)
        if task_data:
            self.redis.setex(completed_key, 3600, task_data)  # 1 hour TTL

        # Delete original task
        self.redis.delete(task_key)

        print(f"✅ Completed task: {task_id}")

    def mark_task_failed(self, task_id: str, error: str):
        """Mark task as failed and requeue with lower priority"""
        task_key = f"{self.prefix}task:{task_id}"
        task_data = self.redis.get(task_key)

        if task_data:
            task = Task.from_dict(json.loads(task_data))

            # Increment failure count
            failures_key = f"{self.prefix}failures:{task_id}"
            failures = int(self.redis.get(failures_key) or 0)
            failures += 1
            self.redis.setex(failures_key, 3600, failures)

            if failures >= 3:
                # Too many failures, remove from queue
                print(f"❌ Task failed {failures} times, removing: {task_id}")
                self.mark_task_complete(task_id)
            else:
                # Requeue with lower priority
                task.priority = min(10, task.priority + 2)
                self.queue_task(task)
                print(f"⚠️ Task failed, requeued with priority {task.priority}: {task_id}")

    def get_queue_size(self) -> int:
        """Get number of tasks in queue"""
        queue_key = f"{self.prefix}task_queue"
        return self.redis.zcard(queue_key)

    def clear_queue(self):
        """Clear all tasks from queue"""
        queue_key = f"{self.prefix}task_queue"
        task_ids = self.redis.zrange(queue_key, 0, -1)

        for task_id in task_ids:
            task_key = f"{self.prefix}task:{task_id}"
            self.redis.delete(task_key)

        self.redis.delete(queue_key)
        print("🗑️ Cleared task queue")

    # Session Summary Management

    def store_session_summary(self, phase: str, summary: dict):
        """Store summary of what was fixed in last session"""
        key = f"{self.prefix}summary:{phase}"
        summary["timestamp"] = datetime.now().isoformat()
        self.redis.setex(key, 3600, json.dumps(summary))  # 1 hour TTL
        print(f"💾 Stored session summary for phase: {phase}")

    def get_session_summary(self, phase: str) -> dict | None:
        """Get last session summary for context"""
        key = f"{self.prefix}summary:{phase}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    # Run History Management

    def record_run_result(self, run_id: str, metrics: dict):
        """Record results of orchestrator run"""
        key = f"{self.prefix}run_history"
        run_data = {"run_id": run_id, "timestamp": datetime.now().isoformat(), "metrics": metrics}

        # Add to list (newest first)
        self.redis.lpush(key, json.dumps(run_data))

        # Keep only last 10 runs
        self.redis.ltrim(key, 0, 9)

        print(f"📊 Recorded run: {run_id}")

    def get_run_history(self, count: int = 10) -> list[dict]:
        """Get recent run history"""
        key = f"{self.prefix}run_history"
        history = self.redis.lrange(key, 0, count - 1)
        return [json.loads(h) for h in history]

    def get_latest_run(self) -> dict | None:
        """Get most recent run"""
        history = self.get_run_history(count=1)
        return history[0] if history else None

    # Project State Management

    def set_project_state(self, key: str, value: any, ttl: int = None):
        """Set arbitrary project state"""
        state_key = f"{self.prefix}state:{key}"
        if ttl:
            self.redis.setex(state_key, ttl, json.dumps(value))
        else:
            self.redis.set(state_key, json.dumps(value))

    def get_project_state(self, key: str) -> any | None:
        """Get project state"""
        state_key = f"{self.prefix}state:{key}"
        data = self.redis.get(state_key)
        return json.loads(data) if data else None

    # Circuit Breaker State

    def increment_failure_count(self) -> int:
        """Increment consecutive failure count"""
        key = f"{self.prefix}circuit:failures"
        count = self.redis.incr(key)
        self.redis.expire(key, 3600)  # Reset after 1 hour
        return count

    def reset_failure_count(self):
        """Reset consecutive failure count"""
        key = f"{self.prefix}circuit:failures"
        self.redis.delete(key)

    def get_failure_count(self) -> int:
        """Get consecutive failure count"""
        key = f"{self.prefix}circuit:failures"
        return int(self.redis.get(key) or 0)

    def is_circuit_open(self, max_failures: int = 5) -> bool:
        """Check if circuit breaker should stop execution"""
        return self.get_failure_count() >= max_failures

    # Utility Methods

    def get_stats(self) -> dict:
        """Get overall state statistics"""
        return {
            "queue_size": self.get_queue_size(),
            "failure_count": self.get_failure_count(),
            "run_count": len(self.get_run_history()),
            "latest_run": self.get_latest_run(),
        }

    def clear_all(self):
        """Clear all state (use with caution!)"""
        pattern = f"{self.prefix}*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
        print("🗑️ Cleared all state")


def generate_task_id() -> str:
    """Generate unique task ID"""
    return f"task_{uuid.uuid4().hex[:8]}"


def main():
    """CLI entry point for testing"""
    import sys

    mgr = StateManager()

    if len(sys.argv) < 2:
        print("Usage: python state_manager.py [stats|clear|test]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "stats":
        stats = mgr.get_stats()
        print(json.dumps(stats, indent=2))

    elif command == "clear":
        mgr.clear_all()

    elif command == "test":
        # Test queue operations
        print("Testing state manager...")

        # Create test tasks
        task1 = Task(
            id=generate_task_id(),
            type="fix_build_error",
            priority=1,
            phase="build",
            file="lib/main.dart",
            message="Undefined name 'foo'",
            context="// code context here",
            created_at=datetime.now().isoformat(),
        )

        task2 = Task(
            id=generate_task_id(),
            type="fix_test_failure",
            priority=3,
            phase="test",
            message="Expected 5 but got 3",
            created_at=datetime.now().isoformat(),
        )

        # Queue tasks
        mgr.queue_task(task1)
        mgr.queue_task(task2)

        # Get tasks
        tasks = mgr.get_next_tasks(count=2)
        print(f"\n📋 Next tasks ({len(tasks)}):")
        for task in tasks:
            print(f"  - {task.type} (priority {task.priority})")

        # Store session summary
        mgr.store_session_summary("build", {"fixed_count": 5, "total_count": 10})

        # Record run
        mgr.record_run_result("test_run_1", {"build_status": "pass", "test_pass_rate": 0.9})

        # Show stats
        stats = mgr.get_stats()
        print("\n📊 Stats:")
        print(json.dumps(stats, indent=2))

        print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
