/**
 * PM2 Configuration for Real Projects Multi-Language Autonomous Fixing
 *
 * Projects:
 * - air-executor (Python)
 * - cc-task-manager (JavaScript)
 * - mind-training (JavaScript)
 * - money-making-app (Flutter)
 * - warps (JavaScript)
 */

module.exports = {
  apps: [{
    name: 'real-projects-fixing',
    script: './airflow_dags/autonomous_fixing/multi_language_orchestrator.py',
    args: 'config/real_projects_fix.yaml',
    interpreter: process.env.HOME + '/.venv/air-executor/bin/python',

    // Working directory
    cwd: '/home/rmondo/repos/air-executor',

    // Logging
    out_file: './logs/real-projects-out.log',
    error_file: './logs/real-projects-error.log',
    log_file: './logs/real-projects-combined.log',
    merge_logs: true,
    time: true,  // Prefix logs with timestamp

    // Environment
    env: {
      PYTHONUNBUFFERED: '1',
      PATH: process.env.HOME + '/.venv/air-executor/bin:' + process.env.PATH
    },

    // Restart strategy
    autorestart: false,  // Don't auto-restart - run once then stop
    max_restarts: 0,

    // Resource limits
    max_memory_restart: '2G',  // Restart if memory exceeds 2GB

    // Execution
    instances: 1,
    exec_mode: 'fork',

    // Wait for app to be ready
    wait_ready: false,
    listen_timeout: 10000,

    // Stop behavior
    kill_timeout: 30000,  // Wait 30s for graceful shutdown

    // Error handling
    min_uptime: 10000,  // Must run at least 10s to be considered started
  }]
};
