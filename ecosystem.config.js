// PM2 ecosystem file for autonomous fixing
module.exports = {
  apps: [{
    name: 'autonomous-fixing',
    script: './scripts/run_autonomous_fixing.sh',
    args: '--max-iterations=50',
    interpreter: '/bin/bash',
    cwd: '/home/rmondo/repos/air-executor',

    // Logging
    out_file: './logs/autonomous-fixing-out.log',
    error_file: './logs/autonomous-fixing-error.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    merge_logs: true,

    // Process management
    autorestart: false,  // Don't restart when it finishes normally
    max_restarts: 3,
    min_uptime: '10s',

    // Environment
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'  // Ensure Python output is not buffered
    }
  }]
};
