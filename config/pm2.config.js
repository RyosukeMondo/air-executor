/**
 * PM2 Ecosystem Configuration - Single Source of Truth
 *
 * Manages autonomous fixing processes for multi-language projects.
 *
 * Usage:
 *   pm2 start config/pm2.config.js                          # All projects
 *   pm2 start config/pm2.config.js --only fix-air-executor  # Specific project
 *   pm2 logs                                                # View all logs
 */

const VENV_PYTHON = process.env.HOME + '/.venv/air-executor/bin/python';
const ORCHESTRATOR = './airflow_dags/autonomous_fixing/multi_language_orchestrator.py';
const CWD = '/home/rmondo/repos/air-executor';

// Common PM2 process settings
const commonConfig = {
  interpreter: VENV_PYTHON,
  cwd: CWD,
  autorestart: false,
  max_restarts: 0,
  merge_logs: true,
  time: true,
  env: {
    PYTHONUNBUFFERED: '1',
    PATH: `${process.env.HOME}/.venv/air-executor/bin:${process.env.PATH}`
  },
  max_memory_restart: '2G',
  instances: 1,
  exec_mode: 'fork',
  wait_ready: false,
  listen_timeout: 10000,
  kill_timeout: 30000,
  min_uptime: 10000
};

module.exports = {
  apps: [
    {
      name: 'fix-air-executor',
      script: ORCHESTRATOR,
      args: 'config/projects/air-executor.yaml',
      out_file: './logs/fix-air-executor-out.log',
      error_file: './logs/fix-air-executor-error.log',
      env: { ...commonConfig.env, PROJECT_NAME: 'air-executor' },
      ...commonConfig
    },
    {
      name: 'fix-cc-task-manager',
      script: ORCHESTRATOR,
      args: 'config/projects/cc-task-manager.yaml',
      out_file: './logs/fix-cc-task-manager-out.log',
      error_file: './logs/fix-cc-task-manager-error.log',
      env: { ...commonConfig.env, PROJECT_NAME: 'cc-task-manager' },
      ...commonConfig
    },
    {
      name: 'fix-mind-training',
      script: ORCHESTRATOR,
      args: 'config/projects/mind-training.yaml',
      out_file: './logs/fix-mind-training-out.log',
      error_file: './logs/fix-mind-training-error.log',
      env: { ...commonConfig.env, PROJECT_NAME: 'mind-training' },
      ...commonConfig
    },
    {
      name: 'fix-money-making-app',
      script: ORCHESTRATOR,
      args: 'config/projects/money-making-app.yaml',
      out_file: './logs/fix-money-making-app-out.log',
      error_file: './logs/fix-money-making-app-error.log',
      env: { ...commonConfig.env, PROJECT_NAME: 'money-making-app' },
      ...commonConfig
    },
    {
      name: 'fix-warps',
      script: ORCHESTRATOR,
      args: 'config/projects/warps.yaml',
      out_file: './logs/fix-warps-out.log',
      error_file: './logs/fix-warps-error.log',
      env: { ...commonConfig.env, PROJECT_NAME: 'warps' },
      ...commonConfig
    }
  ]
};
