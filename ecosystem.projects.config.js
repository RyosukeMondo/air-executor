// PM2 Ecosystem - One process per project for proper isolation
// Each project fixes independently until IT passes gates

const VENV_PYTHON = process.env.HOME + '/.venv/air-executor/bin/python';
const SCRIPT = './airflow_dags/autonomous_fixing/multi_language_orchestrator.py';

module.exports = {
  apps: [
    {
      name: 'fix-air-executor',
      script: SCRIPT,
      args: 'config/projects/air-executor.yaml',
      interpreter: VENV_PYTHON,
      autorestart: false,
      max_restarts: 0,
      out_file: './logs/fix-air-executor-out.log',
      error_file: './logs/fix-air-executor-error.log',
      env: {
        PROJECT_NAME: 'air-executor'
      }
    },
    {
      name: 'fix-cc-task-manager',
      script: SCRIPT,
      args: 'config/projects/cc-task-manager.yaml',
      interpreter: VENV_PYTHON,
      autorestart: false,
      max_restarts: 0,
      out_file: './logs/fix-cc-task-manager-out.log',
      error_file: './logs/fix-cc-task-manager-error.log',
      env: {
        PROJECT_NAME: 'cc-task-manager'
      }
    },
    {
      name: 'fix-mind-training',
      script: SCRIPT,
      args: 'config/projects/mind-training.yaml',
      interpreter: VENV_PYTHON,
      autorestart: false,
      max_restarts: 0,
      out_file: './logs/fix-mind-training-out.log',
      error_file: './logs/fix-mind-training-error.log',
      env: {
        PROJECT_NAME: 'mind-training'
      }
    },
    {
      name: 'fix-money-making-app',
      script: SCRIPT,
      args: 'config/projects/money-making-app.yaml',
      interpreter: VENV_PYTHON,
      autorestart: false,
      max_restarts: 0,
      out_file: './logs/fix-money-making-app-out.log',
      error_file: './logs/fix-money-making-app-error.log',
      env: {
        PROJECT_NAME: 'money-making-app'
      }
    },
    {
      name: 'fix-warps',
      script: SCRIPT,
      args: 'config/projects/warps.yaml',
      interpreter: VENV_PYTHON,
      autorestart: false,
      max_restarts: 0,
      out_file: './logs/fix-warps-out.log',
      error_file: './logs/fix-warps-error.log',
      env: {
        PROJECT_NAME: 'warps'
      }
    }
  ]
};
