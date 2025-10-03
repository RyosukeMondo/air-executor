// PM2 ecosystem file for multi-language autonomous fixing
// Each project runs as a separate PM2 app with max_iterations=5

module.exports = {
  apps: [
    {
      name: 'fix-air-executor',
      script: '/home/rmondo/.venv/air-executor/bin/python',
      args: 'airflow_dags/autonomous_fixing/multi_language_orchestrator.py config/projects/air-executor.yaml',
      cwd: '/home/rmondo/repos/air-executor',
      interpreter: 'none',  // Don't wrap with another interpreter

      // Logging
      out_file: './logs/fix-air-executor-out.log',
      error_file: './logs/fix-air-executor-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Process management
      autorestart: false,  // Don't restart when it finishes
      max_restarts: 0,

      // Environment
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'fix-money-making-app',
      script: '/home/rmondo/.venv/air-executor/bin/python',
      args: 'airflow_dags/autonomous_fixing/multi_language_orchestrator.py config/projects/money-making-app.yaml',
      cwd: '/home/rmondo/repos/air-executor',
      interpreter: 'none',

      out_file: './logs/fix-money-making-app-out.log',
      error_file: './logs/fix-money-making-app-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      autorestart: false,
      max_restarts: 0,

      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'fix-cc-task-manager',
      script: '/home/rmondo/.venv/air-executor/bin/python',
      args: 'airflow_dags/autonomous_fixing/multi_language_orchestrator.py config/projects/cc-task-manager.yaml',
      cwd: '/home/rmondo/repos/air-executor',
      interpreter: 'none',

      out_file: './logs/fix-cc-task-manager-out.log',
      error_file: './logs/fix-cc-task-manager-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      autorestart: false,
      max_restarts: 0,

      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'fix-mind-training',
      script: '/home/rmondo/.venv/air-executor/bin/python',
      args: 'airflow_dags/autonomous_fixing/multi_language_orchestrator.py config/projects/mind-training.yaml',
      cwd: '/home/rmondo/repos/air-executor',
      interpreter: 'none',

      out_file: './logs/fix-mind-training-out.log',
      error_file: './logs/fix-mind-training-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      autorestart: false,
      max_restarts: 0,

      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'fix-warps',
      script: '/home/rmondo/.venv/air-executor/bin/python',
      args: 'airflow_dags/autonomous_fixing/multi_language_orchestrator.py config/projects/warps.yaml',
      cwd: '/home/rmondo/repos/air-executor',
      interpreter: 'none',

      out_file: './logs/fix-warps-out.log',
      error_file: './logs/fix-warps-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      autorestart: false,
      max_restarts: 0,

      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
