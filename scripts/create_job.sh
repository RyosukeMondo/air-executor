#!/bin/bash
# Helper script to create jobs easily

JOB_NAME=$1
shift

mkdir -p .air-executor/jobs/${JOB_NAME}/logs

cat > .air-executor/jobs/${JOB_NAME}/state.json << STATEOF
{
  "id": "${JOB_NAME}-$(date +%s)",
  "name": "${JOB_NAME}",
  "state": "waiting",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
}
STATEOF

cat > .air-executor/jobs/${JOB_NAME}/tasks.json << TASKEOF
[
  {
    "id": "task-1",
    "job_name": "${JOB_NAME}",
    "command": "echo",
    "args": ["Starting job: ${JOB_NAME}"],
    "dependencies": [],
    "status": "pending",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "started_at": null,
    "completed_at": null,
    "error": null
  },
  {
    "id": "task-2",
    "job_name": "${JOB_NAME}",
    "command": "sleep",
    "args": ["1"],
    "dependencies": ["task-1"],
    "status": "pending",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "started_at": null,
    "completed_at": null,
    "error": null
  },
  {
    "id": "task-3",
    "job_name": "${JOB_NAME}",
    "command": "echo",
    "args": ["Job ${JOB_NAME} completed!"],
    "dependencies": ["task-2"],
    "status": "pending",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "started_at": null,
    "completed_at": null,
    "error": null
  }
]
TASKEOF

echo "✅ Created job: ${JOB_NAME}"
echo "   Watch it execute in the manager logs!"
