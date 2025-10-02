# Installation Guide

Complete installation guide for Air Executor and its dependencies.

## Prerequisites

- Python 3.10 or higher
- Node.js 18+ (for Claude Code CLI)
- Git
- (Optional) Apache Airflow 2.0+
- (Optional) Redis (for autonomous fixing)

## Quick Installation

### 1. Install Air Executor

```bash
# Clone the repository
git clone https://github.com/RyosukeMondo/air-executor.git
cd air-executor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### 2. Install Claude Code CLI

```bash
# Install globally via npm
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### 3. Configure Authentication

```bash
# Login to Claude Code (opens browser)
claude login

# Or set API key (if using SDK mode)
export ANTHROPIC_API_KEY=your-api-key-here
```

### 4. Install Optional Dependencies

#### For Airflow Integration

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
    --email admin@example.com
```

#### For Autonomous Fixing

```bash
# Install Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

## Verification

```bash
# Verify Python installation
python --version

# Verify virtual environment
which python  # Should point to .venv/bin/python

# Verify Air Executor
python -c "import air_executor; print(air_executor.__version__)"

# Verify Claude Code
claude --version

# Verify Airflow (if installed)
airflow version

# Verify Redis (if installed)
redis-cli ping  # Should return PONG
```

## Configuration

See [Configuration Guide](./configuration.md) for detailed configuration options.

## Troubleshooting

If you encounter issues, check:
- Python version: `python --version` (must be 3.10+)
- Virtual environment is activated
- All prerequisites are installed

For more help, see [Troubleshooting Guide](../reference/troubleshooting.md).

## Next Steps

- [Quick Start Guide](./quickstart.md) - Get started in 5 minutes
- [Configuration Guide](./configuration.md) - Set up your environment
- [Airflow Integration](../guides/airflow-integration.md) - Integrate with Airflow
