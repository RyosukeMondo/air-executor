# Troubleshooting Guide

Common issues and solutions for Air Executor.

## Installation Issues

### Claude Code Not Found

**Symptom:** `claude: command not found`

**Solution:**
```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version

# If still not found, add to PATH
export PATH="/usr/local/bin:$PATH"
```

### Python Version Mismatch

**Symptom:** `Python 3.10+ required`

**Solution:**
```bash
# Check Python version
python --version

# Use specific Python version
python3.10 -m venv .venv
```

### Virtual Environment Issues

**Symptom:** Packages not found after installation

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Verify correct python
which python  # Should show .venv/bin/python
```

## Airflow Issues

### DAGs Not Showing Up

**Symptom:** DAGs don't appear in Airflow UI

**Solution:**
```bash
# Check DAG folder
airflow config get-value core dags_folder

# Sync DAGs
./scripts/sync_dags_to_airflow.sh

# Verify DAG files
airflow dags list

# Restart scheduler
airflow scheduler
```

### Task Execution Failures

**Symptom:** Tasks fail with import errors

**Solution:**
```bash
# Verify Python path in DAG
import sys
print(sys.path)

# Add project to path in DAG
sys.path.insert(0, '/home/rmondo/repos/air-executor/src')
```

## Claude SDK Issues

### Authentication Errors

**Symptom:** `Authentication failed` or `API key invalid`

**Solution:**
```bash
# Login via CLI
claude login

# Verify authentication
claude --version

# Check API key source
# SDK uses Claude CLI authentication, not ANTHROPIC_API_KEY
```

### Wrapper Hanging

**Symptom:** `claude_wrapper.py` doesn't respond

**Solution:**
- Ensure `/usr/local/bin` is in PATH
- Check that `claude` CLI is accessible
- Verify stdin/stdout protocol is correct
- Increase timeout in configuration

### No Stream Events

**Symptom:** Wrapper completes but no output

**Solution:**
- Ensure stdout is read line-by-line
- Don't close stdin immediately
- Check for `exit_on_complete` option

## Autonomous Fixing Issues

### Redis Connection Failed

**Symptom:** `Could not connect to Redis`

**Solution:**
```bash
# Start Redis
redis-server

# Verify Redis is running
redis-cli ping  # Should return PONG

# Check Redis configuration
redis-cli CONFIG GET port
```

### No Issues Discovered

**Symptom:** Issue discovery returns 0 errors

**Solution:**
- Check flutter analyze output format
- Verify parser regex patterns
- Run `flutter analyze` manually to see format

### Tasks Execute But No Changes

**Symptom:** Tasks complete successfully but no commits

**Solution:**
- Verify `/usr/local/bin` in PATH for `claude` CLI
- Check wrapper stdout reading (must read line-by-line)
- Ensure commit instructions in prompts
- Verify git configuration in target repository

## Configuration Issues

### Config File Not Found

**Symptom:** `config/air-executor.toml not found`

**Solution:**
```bash
# Copy example config
cp config/air-executor.example.toml config/air-executor.toml

# Edit configuration
vim config/air-executor.toml
```

### Invalid Config Format

**Symptom:** `TOML parsing error`

**Solution:**
- Verify TOML syntax (use TOML validator)
- Check for missing quotes around strings
- Verify path separators (use forward slashes)

## General Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System Requirements

```bash
# Verify all prerequisites
python --version  # 3.10+
node --version    # 18+
npm --version
claude --version
airflow version   # If using Airflow
redis-cli ping    # If using Redis
```

### Get Help

- **GitHub Issues**: [Report a bug](https://github.com/RyosukeMondo/air-executor/issues)
- **Documentation**: [Full documentation](../README.md)
- **Examples**: Check `examples/` directory

## Known Issues

### Issue: Wrapper Process Hangs
**Status:** Fixed in v0.2.0
**Workaround:** Read stdout line-by-line instead of using `communicate()`

### Issue: Path Not Including /usr/local/bin
**Status:** Fixed in v0.2.0
**Workaround:** Manually add to PATH in wrapper execution

## Performance Issues

### Slow Task Execution

**Symptom:** Tasks take > 5 minutes

**Solution:**
- Increase timeout in configuration
- Check network connectivity
- Verify Claude API is responsive
- Reduce batch size for autonomous fixing

### High Memory Usage

**Symptom:** Process uses > 2GB RAM

**Solution:**
- Reduce concurrent task count
- Clear Redis database periodically
- Check for memory leaks in custom DAGs

For additional help, please open an issue on GitHub.
