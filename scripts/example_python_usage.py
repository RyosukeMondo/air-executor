#!/usr/bin/env python3
"""
Example: How to create and submit jobs to Air-Executor from Python code
"""

import json
import uuid
from datetime import datetime
from pathlib import Path


class AirExecutorClient:
    """Simple client to create jobs for Air-Executor"""
    
    def __init__(self, base_path: str = ".air-executor"):
        self.base_path = Path(base_path)
        self.jobs_path = self.base_path / "jobs"
        
    def create_job(self, job_name: str, tasks: list) -> str:
        """
        Create a new job with tasks.
        
        Args:
            job_name: Name of the job
            tasks: List of task dictionaries with 'command', 'args', 'dependencies'
            
        Returns:
            Job ID
            
        Example:
            client = AirExecutorClient()
            client.create_job("my-job", [
                {"command": "echo", "args": ["Hello"], "dependencies": []},
                {"command": "sleep", "args": ["2"], "dependencies": ["task-1"]},
            ])
        """
        job_id = f"{job_name}-{int(datetime.now().timestamp())}"
        job_dir = self.jobs_path / job_name
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "logs").mkdir(exist_ok=True)
        
        # Create state.json
        state = {
            "id": job_id,
            "name": job_name,
            "state": "waiting",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        with open(job_dir / "state.json", "w") as f:
            json.dump(state, f, indent=2)
        
        # Create tasks.json
        task_objects = []
        for i, task in enumerate(tasks, 1):
            task_id = task.get("id", f"task-{i}")
            task_objects.append({
                "id": task_id,
                "job_name": job_name,
                "command": task["command"],
                "args": task.get("args", []),
                "dependencies": task.get("dependencies", []),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "started_at": None,
                "completed_at": None,
                "error": None
            })
        
        with open(job_dir / "tasks.json", "w") as f:
            json.dump(task_objects, f, indent=2)
        
        print(f"✅ Created job: {job_name} (ID: {job_id})")
        return job_id
    
    def get_job_status(self, job_name: str) -> dict:
        """Get current status of a job"""
        state_file = self.jobs_path / job_name / "state.json"
        tasks_file = self.jobs_path / job_name / "tasks.json"
        
        if not state_file.exists():
            return {"error": "Job not found"}
        
        with open(state_file) as f:
            state = json.load(f)
        
        with open(tasks_file) as f:
            tasks = json.load(f)
        
        return {
            "job_name": job_name,
            "state": state["state"],
            "total_tasks": len(tasks),
            "completed": sum(1 for t in tasks if t["status"] == "completed"),
            "failed": sum(1 for t in tasks if t["status"] == "failed"),
            "pending": sum(1 for t in tasks if t["status"] == "pending"),
            "running": sum(1 for t in tasks if t["status"] == "running"),
        }


# Example usage
if __name__ == "__main__":
    client = AirExecutorClient()
    
    # Example 1: Simple sequential pipeline
    print("📝 Creating data processing pipeline...")
    client.create_job("data-pipeline", [
        {
            "id": "download",
            "command": "echo",
            "args": ["Downloading data..."],
            "dependencies": []
        },
        {
            "id": "process",
            "command": "echo",
            "args": ["Processing data..."],
            "dependencies": ["download"]
        },
        {
            "id": "upload",
            "command": "echo",
            "args": ["Uploading results..."],
            "dependencies": ["process"]
        }
    ])
    
    # Example 2: Parallel data processing
    print("\n📝 Creating parallel processing job...")
    client.create_job("parallel-work", [
        {
            "id": "prepare",
            "command": "echo",
            "args": ["Preparing workspace"],
            "dependencies": []
        },
        {
            "id": "process-batch-1",
            "command": "echo",
            "args": ["Processing batch 1"],
            "dependencies": ["prepare"]
        },
        {
            "id": "process-batch-2",
            "command": "echo",
            "args": ["Processing batch 2"],
            "dependencies": ["prepare"]
        },
        {
            "id": "process-batch-3",
            "command": "echo",
            "args": ["Processing batch 3"],
            "dependencies": ["prepare"]
        },
        {
            "id": "merge",
            "command": "echo",
            "args": ["Merging results"],
            "dependencies": ["process-batch-1", "process-batch-2", "process-batch-3"]
        }
    ])
    
    # Example 3: Real Python script execution
    print("\n📝 Creating Python script job...")
    client.create_job("python-job", [
        {
            "id": "run-script",
            "command": "python",
            "args": ["-c", "print('Hello from Python!'); import time; time.sleep(1)"],
            "dependencies": []
        }
    ])
    
    print("\n✅ All jobs created! Check status with:")
    print("   watch -n 2 ./status.sh")
