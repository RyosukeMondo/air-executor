#!/usr/bin/env python3
"""
Simple example: Using Airflow to orchestrate Air-Executor jobs
This is Option 2 from AIRFLOW_INTEGRATION.md
"""

from pathlib import Path
import json
from datetime import datetime
import time


class SimpleAirflowDemo:
    """Simulates what Airflow would do when orchestrating Air-Executor"""
    
    def __init__(self):
        self.client = self._load_client()
    
    def _load_client(self):
        """Load Air-Executor client"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from example_python_usage import AirExecutorClient
        return AirExecutorClient()
    
    def run_dag(self, dag_name: str):
        """Simulate running an Airflow DAG"""
        print(f"\n{'='*60}")
        print(f"🚀 Airflow DAG: {dag_name}")
        print(f"{'='*60}\n")
        
        # Task 1: Create Air-Executor job
        print("📋 [Task 1/3] Creating Air-Executor job...")
        job_name = f"{dag_name}-run-{int(datetime.now().timestamp())}"
        
        self.client.create_job(job_name, [
            {
                "id": "extract",
                "command": "echo",
                "args": ["Extracting data from source..."],
                "dependencies": []
            },
            {
                "id": "transform",
                "command": "echo",
                "args": ["Transforming data..."],
                "dependencies": ["extract"]
            },
            {
                "id": "load",
                "command": "echo",
                "args": ["Loading into destination..."],
                "dependencies": ["transform"]
            }
        ])
        print(f"   ✅ Job created: {job_name}")
        
        # Task 2: Wait for completion (sensor)
        print("\n⏳ [Task 2/3] Waiting for job completion...")
        print("   (Airflow PythonSensor would poll every 5 seconds)")
        
        max_wait = 30
        elapsed = 0
        while elapsed < max_wait:
            status = self.client.get_job_status(job_name)
            state = status.get('error') or self._get_state(job_name)
            
            print(f"   [{elapsed}s] State: {state}, Completed: {status.get('completed', 0)}/3")
            
            if state in ['completed', 'failed']:
                break
            
            time.sleep(5)
            elapsed += 5
        
        # Task 3: Process result
        print("\n📊 [Task 3/3] Processing job result...")
        final_status = self.client.get_job_status(job_name)
        
        if final_status.get('error'):
            print(f"   ❌ Job not found: {final_status['error']}")
        elif final_status.get('completed', 0) == 3:
            print(f"   ✅ Job succeeded!")
            print(f"      Total tasks: {final_status['total_tasks']}")
            print(f"      Completed: {final_status['completed']}")
        else:
            print(f"   ⚠️  Job incomplete")
        
        print(f"\n{'='*60}")
        print(f"✨ Airflow DAG completed!")
        print(f"{'='*60}\n")
        
        return final_status
    
    def _get_state(self, job_name: str) -> str:
        """Get job state from file"""
        try:
            state_file = Path(f".air-executor/jobs/{job_name}/state.json")
            with open(state_file) as f:
                return json.load(f)['state']
        except:
            return "unknown"


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║  Airflow + Air-Executor Integration Demo                    ║
║                                                              ║
║  This simulates what Airflow would do:                      ║
║  1. Create Air-Executor job (via PythonOperator)            ║
║  2. Wait for completion (via PythonSensor)                  ║
║  3. Process result (via PythonOperator)                     ║
║                                                              ║
║  In real Airflow, you'd see this in the web UI at          ║
║  http://localhost:8080 with beautiful graphs!               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    demo = SimpleAirflowDemo()
    demo.run_dag("etl-pipeline")
    
    print("\n💡 To see this in real Airflow UI:")
    print("   1. pip install apache-airflow")
    print("   2. See AIRFLOW_INTEGRATION.md for setup")
    print("   3. Access http://localhost:8080")
