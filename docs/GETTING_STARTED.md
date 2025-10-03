# Getting Started with Air Executor

Complete guide to install, configure, and run Air Executor in under 10 minutes.

## Prerequisites

Before installing Air Executor, ensure you have:

- **Python 3.10+** - Required for Air Executor core
- **Node.js 18+** - Required for Claude Code CLI
- **Git** - For repository management
- **Redis** (optional) - For autonomous fixing state management
- **Apache Airflow 2.0+** (optional) - For DAG orchestration

### Verify Prerequisites

```bash
# Check Python version
python --version  # Should be 3.10+

# Check Node.js version
node --version    # Should be 18+

# Check npm
npm --version

# Check Git
git --version
```

## Installation

### Step 1: Install Air Executor

```bash
# Clone the repository
git clone https://github.com/RyosukeMondo/air-executor.git
cd air-executor

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install Air Executor in development mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Step 2: Install Claude Code CLI

```bash
# Install globally via npm
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version

# Login to Claude (opens browser)
claude login
```

### Step 3: Install Language-Specific Tools

#### For Python Projects

```bash
# Install Python development tools
./scripts/setup_python.sh

# Verify installation
python -m pytest --version
pylint --version
mypy --version
```

#### For JavaScript/TypeScript Projects

```bash
# Install JavaScript development tools
./scripts/setup_javascript.sh

# Verify installation
npm list -g eslint
npx tsc --version
```

#### For Flutter Projects

```bash
# Install Flutter SDK
./scripts/setup_flutter.sh

# Verify installation
flutter --version
flutter doctor
```

#### For Go Projects

```bash
# Install Go development tools
./scripts/setup_go.sh

# Verify installation
go version
staticcheck -version
```

### Step 4: Install Optional Dependencies

#### Redis (for Autonomous Fixing)

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
redis-server &

# macOS
brew install redis
brew services start redis

# Verify Redis is running
redis-cli ping  # Should return PONG
```

#### Apache Airflow (for DAG Orchestration)

```bash
# Install Airflow
pip install apache-airflow==2.10.4

# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

# Start Airflow services
airflow webserver -p 8080 &
airflow scheduler &

# Access Airflow UI
open http://localhost:8080
```

## Verification

### Check All Tools

```bash
# Run comprehensive tool check
./scripts/check_tools.sh

# Expected output:
# ✅ Python 3.10+
# ✅ Claude CLI authenticated
# ✅ Pylint, mypy (if Python setup)
# ✅ ESLint, TypeScript (if JS setup)
# ✅ Flutter SDK (if Flutter setup)
# ✅ Go tools (if Go setup)
# ✅ Redis running (if installed)
# ✅ Airflow running (if installed)
```

### Verify Air Executor

```bash
# Verify Python package
python -c "import air_executor; print('Air Executor installed successfully')"

# Verify wrapper script
python scripts/claude_wrapper.py --help
```

## Quick Start Examples

### Example 1: Simple Job Execution

```python
# example_job.py
from air_executor import Job, Task, SubprocessRunner

# Create a job
job = Job(name="data_processing")

# Add tasks
job.add_task(Task(
    name="fetch_data",
    command=["python", "scripts/fetch_data.py"]
))

job.add_task(Task(
    name="process_data",
    command=["python", "scripts/process_data.py"],
    depends_on=["fetch_data"]
))

# Execute the job
runner = SubprocessRunner()
result = runner.run_job(job)
print(f"Job completed: {result}")
```

```bash
# Run the example
python example_job.py
```

### Example 2: Claude AI Query

```bash
# Using wrapper script directly
echo '{"action":"prompt","prompt":"Explain async/await in Python","options":{"cwd":"."}}' | \
  python scripts/claude_wrapper.py
```

### Example 3: Autonomous Fixing (Single Project)

```bash
# Run on a single project
./scripts/run_autonomous_fix.sh config/projects/air-executor.yaml

# Monitor progress
tail -f logs/orchestrator_run.log

# Check results
cd /path/to/project
git log --oneline -5
```

### Example 4: Autonomous Fixing (All Projects with PM2)

```bash
# Start all configured projects
pm2 start config/pm2.config.js

# Monitor logs
pm2 logs

# Check status
pm2 status

# Stop all
pm2 stop all
```

### Example 5: Airflow DAG Execution

```bash
# Sync DAGs to Airflow
./scripts/sync_dags_to_airflow.sh

# Trigger Claude query DAG
airflow dags trigger claude_query_sdk \
  --conf '{"prompt": "Review this code for improvements"}'

# Check DAG status
airflow dags list-runs -d claude_query_sdk

# View logs
airflow tasks logs claude_query_sdk run_claude_query_sdk <execution_date>
```

## Configuration

### Basic Configuration

Create a project configuration file:

```yaml
# config/projects/my-project.yaml
project_name: "my-project"
project_path: "/path/to/my-project"
language: "python"  # or javascript, flutter, go

# Tool validation
validate_tools: true
required_tools:
  - pylint
  - mypy
  - pytest

# Priority thresholds
priorities:
  p1_static:
    success_threshold: 0.90
  p2_tests:
    success_threshold: 0.85

# Execution settings
execution:
  max_iterations: 5
  max_duration_hours: 2
  auto_commit: true

# Logging
logging:
  level: "INFO"
  file: "logs/my-project.log"
```

### Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc

# Air Executor
export AIR_EXECUTOR_HOME="$HOME/repos/air-executor"
export AIR_EXECUTOR_VENV="$HOME/.venv/air-executor"

# Claude
export ANTHROPIC_API_KEY="your-api-key-here"  # If not using CLI auth

# Airflow (optional)
export AIRFLOW_HOME="$HOME/airflow"

# Redis (optional)
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
```

## Project Structure

After installation, your directory structure should look like:

```
air-executor/
├── .venv/                 # Virtual environment
├── src/air_executor/      # Core package
├── scripts/               # Utility scripts
│   ├── run_autonomous_fix.sh
│   ├── check_tools.sh
│   ├── claude_wrapper.py
│   └── setup_*.sh
├── config/                # Configuration files
│   ├── projects/          # Project-specific configs
│   └── pm2.config.js
├── logs/                  # Log files
├── airflow_dags/          # Airflow DAG definitions
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Common Workflows

### Workflow 1: Local Development

```bash
# 1. Activate environment
source ~/.venv/air-executor/bin/activate

# 2. Run checks on your project
./scripts/check_tools.sh

# 3. Configure project
vim config/projects/my-project.yaml

# 4. Run autonomous fixing
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# 5. Monitor progress
tail -f logs/orchestrator_run.log
```

### Workflow 2: PM2 Process Management

```bash
# 1. Configure all projects in config/projects/

# 2. Update PM2 config
vim config/pm2.config.js

# 3. Start all processes
pm2 start config/pm2.config.js

# 4. Monitor
pm2 logs
pm2 monit

# 5. Manage processes
pm2 restart all
pm2 stop all
pm2 delete all
```

### Workflow 3: Airflow Integration

```bash
# 1. Start Airflow services
airflow webserver -p 8080 &
airflow scheduler &

# 2. Sync DAGs
./scripts/sync_dags_to_airflow.sh

# 3. Access Airflow UI
open http://localhost:8080

# 4. Trigger DAGs via UI or CLI
airflow dags trigger claude_query_sdk

# 5. Monitor execution
# Use Airflow UI for visual monitoring
```

## Troubleshooting

### Claude CLI Not Found

```bash
# Issue: claude: command not found

# Solution 1: Reinstall globally
npm install -g @anthropic-ai/claude-code

# Solution 2: Add to PATH
export PATH="/usr/local/bin:$PATH"

# Solution 3: Verify npm global bin
npm config get prefix
# Add {prefix}/bin to PATH
```

### Python Version Issues

```bash
# Issue: Python 3.10+ required

# Solution 1: Use specific Python version
python3.10 -m venv .venv

# Solution 2: Install Python 3.10+ via pyenv
pyenv install 3.10.0
pyenv local 3.10.0
```

### Virtual Environment Issues

```bash
# Issue: Packages not found after install

# Solution 1: Ensure venv is activated
source .venv/bin/activate

# Solution 2: Verify Python path
which python  # Should show .venv/bin/python

# Solution 3: Reinstall in venv
pip install -e .
```

### Redis Connection Issues

```bash
# Issue: Could not connect to Redis

# Solution 1: Start Redis
redis-server &

# Solution 2: Verify Redis is running
redis-cli ping  # Should return PONG

# Solution 3: Check Redis configuration
redis-cli CONFIG GET port
redis-cli CONFIG GET bind
```

### Airflow DAGs Not Showing

```bash
# Issue: DAGs don't appear in Airflow UI

# Solution 1: Sync DAGs
./scripts/sync_dags_to_airflow.sh

# Solution 2: Verify DAG folder
airflow config get-value core dags_folder

# Solution 3: Restart Airflow
pkill -f "airflow webserver"
pkill -f "airflow scheduler"
airflow webserver -p 8080 &
airflow scheduler &
```

### Permission Errors

```bash
# Issue: Permission denied when running scripts

# Solution: Make scripts executable
chmod +x scripts/*.sh
```

## Performance Tips

### 1. Optimize Virtual Environment

```bash
# Use lightweight venv instead of conda
python -m venv .venv

# Install only required packages
pip install -e . --no-deps
pip install -r requirements.txt
```

### 2. Configure PM2 for Production

```javascript
// config/pm2.config.js
module.exports = {
  apps: [{
    name: 'air-executor-production',
    script: 'scripts/run_autonomous_fix.sh',
    args: 'config/projects/production.yaml',
    max_memory_restart: '2G',
    instances: 1,
    autorestart: false,
    watch: false,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
  }]
};
```

### 3. Optimize Redis for Performance

```bash
# Edit redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save ""  # Disable persistence if not needed
```

## Security Best Practices

### 1. Protect API Keys

```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use environment variables
export ANTHROPIC_API_KEY="your-key"

# Or use Claude CLI auth (recommended)
claude login
```

### 2. Restrict Redis Access

```bash
# Edit redis.conf
bind 127.0.0.1
requirepass your-secure-password
```

### 3. Secure Airflow

```bash
# Use strong admin password
airflow users create \
    --username admin \
    --password <strong-password> \
    --role Admin

# Enable authentication in airflow.cfg
[webserver]
authenticate = True
auth_backend = airflow.api.auth.backend.basic_auth
```

## Next Steps

Now that you have Air Executor installed and configured:

1. **For Autonomous Fixing**: See [Autonomous Fixing Guide](./AUTONOMOUS_FIXING.md)
2. **For Configuration**: See [Configuration Reference](./CONFIGURATION.md)
3. **For Architecture**: See [Architecture Guide](./ARCHITECTURE.md)
4. **For DAG Development**: See [guides/dag-development.md](./guides/dag-development.md)
5. **For Troubleshooting**: See [reference/troubleshooting.md](./reference/troubleshooting.md)

## Quick Reference Commands

```bash
# Installation
pip install -e .
npm install -g @anthropic-ai/claude-code

# Verification
./scripts/check_tools.sh

# Single project run
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# PM2 automation
pm2 start config/pm2.config.js
pm2 logs
pm2 status

# Airflow
airflow webserver -p 8080 &
airflow scheduler &
./scripts/sync_dags_to_airflow.sh

# Monitoring
tail -f logs/orchestrator_run.log
pm2 monit
redis-cli MONITOR
```

---

**Need Help?**
- Check [Troubleshooting Guide](./reference/troubleshooting.md)
- Report issues on [GitHub](https://github.com/RyosukeMondo/air-executor/issues)
- Review [Documentation](./README.md)
