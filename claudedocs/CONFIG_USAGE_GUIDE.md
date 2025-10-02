# Configuration Usage Guide

## Overview

Air Executor now uses **TOML configuration** instead of hardcoded paths, making it:
- ✅ **Environment-independent** - Works on any machine
- ✅ **Easy to customize** - Edit one config file
- ✅ **Version controlled** - Track config changes in git
- ✅ **Environment overrides** - Use `.env` for secrets

---

## Quick Start

### 1. Create Config File

```bash
# Copy template
cp config/air-executor.example.toml config/air-executor.toml

# Edit for your environment
vim config/air-executor.toml
```

### 2. Customize Paths

```toml
# config/air-executor.toml

[project]
root = "/home/YOUR_USERNAME/repos/air-executor"  # ← Change this

[airflow]
home = "/home/YOUR_USERNAME/airflow"              # ← Change this
```

### 3. Verify Config

```bash
source .venv/bin/activate
python -c "from air_executor.config import load_config; print(load_config())"
```

**Expected output:**
```
Config(
  project_root=/home/YOUR_USERNAME/repos/air-executor,
  wrapper_path=/home/YOUR_USERNAME/repos/air-executor/scripts/claude_wrapper.py,
  airflow_home=/home/YOUR_USERNAME/airflow,
  claude_timeout=60s
)
```

---

## Configuration File Structure

### Full Example

```toml
# config/air-executor.toml

# === Project Paths ===
[project]
root = "/home/rmondo/repos/air-executor"
scripts_dir = "scripts"
venv_python = ".venv/bin/python"

# === Airflow Configuration ===
[airflow]
home = "/home/rmondo/airflow"
dags_folder = "dags"
logs_folder = "logs"
scripts_folder = "scripts"

# === Claude Wrapper Settings ===
[claude]
wrapper_script = "claude_wrapper.py"
timeout_seconds = 60
permission_mode = "bypassPermissions"

[claude.default_options]
exit_on_complete = true
resume_last_session = false

# === Development Settings ===
[development]
debug = false
validate_config = true
```

### Section Breakdown

#### [project]
Defines project structure and paths.

```toml
[project]
root = "/absolute/path/to/air-executor"  # Main project directory
scripts_dir = "scripts"                   # Relative to root
venv_python = ".venv/bin/python"          # Relative to root
```

**Computed paths:**
- `config.project_root` → `/absolute/path/to/air-executor`
- `config.scripts_dir` → `/absolute/path/to/air-executor/scripts`
- `config.venv_python` → `/absolute/path/to/air-executor/.venv/bin/python`

#### [airflow]
Airflow installation paths.

```toml
[airflow]
home = "/home/user/airflow"     # Airflow home directory
dags_folder = "dags"             # Relative to home
logs_folder = "logs"             # Relative to home
scripts_folder = "scripts"       # Relative to home
```

**Computed paths:**
- `config.airflow_home` → `/home/user/airflow`
- `config.airflow_dags` → `/home/user/airflow/dags`
- `config.airflow_logs` → `/home/user/airflow/logs`

#### [claude]
Claude wrapper execution settings.

```toml
[claude]
wrapper_script = "claude_wrapper.py"      # Script name (in scripts_dir)
timeout_seconds = 60                       # Query timeout
permission_mode = "bypassPermissions"      # Auto-approve or "ask"
```

**Values:**
- `config.wrapper_path` → Full path to wrapper script
- `config.claude_timeout` → Timeout in seconds
- `config.claude_permission_mode` → Permission handling mode

#### [claude.default_options]
Default options passed to Claude queries.

```toml
[claude.default_options]
exit_on_complete = true           # Auto-shutdown after query
resume_last_session = false       # Start fresh session each time
```

These are passed directly to the wrapper's `options` field.

#### [development]
Development and debugging settings.

```toml
[development]
debug = false              # Enable debug logging
validate_config = true     # Validate config on load
```

---

## Using Config in Code

### Load Config

```python
from air_executor.config import load_config

# Load and validate
config = load_config()

# Access paths
print(config.wrapper_path)      # Path object
print(config.venv_python)        # Path object
print(config.claude_timeout)     # int (60)
```

### Config Properties

```python
# Project paths
config.project_root        # Path: /home/user/repos/air-executor
config.scripts_dir         # Path: /home/user/repos/air-executor/scripts
config.wrapper_path        # Path: /home/user/repos/air-executor/scripts/claude_wrapper.py
config.venv_python         # Path: /home/user/repos/air-executor/.venv/bin/python

# Airflow paths
config.airflow_home        # Path: /home/user/airflow
config.airflow_dags        # Path: /home/user/airflow/dags
config.airflow_logs        # Path: /home/user/airflow/logs
config.airflow_scripts     # Path: /home/user/airflow/scripts

# Claude settings
config.claude_timeout              # int: 60
config.claude_permission_mode      # str: "bypassPermissions"
config.claude_default_options      # dict: {"exit_on_complete": true, ...}

# Development
config.debug               # bool: false
```

### Cached Config

For performance, use cached config:

```python
from air_executor.config import get_config

# Loads once, reuses thereafter
config = get_config()
```

---

## Environment Variable Overrides

Override config values with environment variables:

### Supported Variables

```bash
# Override project root
export AIR_EXECUTOR_ROOT="/custom/path/to/air-executor"

# Override Airflow home
export AIRFLOW_HOME="/custom/airflow"

# Override Claude settings
export CLAUDE_TIMEOUT=300
export CLAUDE_PERMISSION_MODE="ask"

# Specify custom config file
export AIR_EXECUTOR_CONFIG="/path/to/custom-config.toml"
```

### Using .env File

```bash
# .env (in project root)
AIR_EXECUTOR_ROOT=/home/production/air-executor
AIRFLOW_HOME=/opt/airflow
CLAUDE_TIMEOUT=120
```

Load automatically:

```python
from dotenv import load_dotenv
from air_executor.config import load_config

load_dotenv()  # Load .env
config = load_config()  # Environment vars override config.toml
```

---

## Config File Locations

Config is searched in order:

1. **Environment variable**: `$AIR_EXECUTOR_CONFIG`
2. **Project root**: `./config/air-executor.toml`
3. **User home**: `~/.air-executor/config.toml`
4. **System-wide**: `/etc/air-executor/config.toml`

### Example Setup

**Development:**
```bash
# Use project config
./config/air-executor.toml
```

**Production:**
```bash
# Use system config
/etc/air-executor/config.toml

# Or environment variable
export AIR_EXECUTOR_CONFIG=/opt/air-executor/config.toml
```

---

## DAG Usage

DAGs automatically use config (no hardcoded paths!):

```python
# airflow_dags/claude_query_sdk.py

from air_executor.config import load_config

def run_claude_query_sdk(**context):
    # Load config (paths adapt to environment)
    config = load_config()

    # Use config values
    wrapper_path = config.wrapper_path
    venv_python = config.venv_python
    timeout = config.claude_timeout

    # Start wrapper
    process = subprocess.Popen(
        [str(venv_python), str(wrapper_path)],
        ...
    )
```

**No more hardcoded paths! Works on any machine with correct config.toml!**

---

## Validation

Config is automatically validated on load:

```python
config = load_config()  # Validates automatically
```

**Checks:**
- ✅ Project root exists
- ✅ Wrapper script exists
- ✅ Python venv exists
- ✅ Airflow home exists
- ✅ Timeout > 0
- ✅ Permission mode is valid

**Disable validation:**

```toml
[development]
validate_config = false  # Skip validation
```

Or in code:

```python
config = Config.load()  # Load without validation
config.validate()        # Validate manually
```

---

## Troubleshooting

### Error: Config file not found

```
FileNotFoundError: Config file not found: /path/to/config/air-executor.toml
Create one from: config/air-executor.example.toml
```

**Solution:**
```bash
cp config/air-executor.example.toml config/air-executor.toml
vim config/air-executor.toml  # Edit paths
```

### Error: Invalid TOML

```
ValueError: Invalid TOML in config/air-executor.toml: ...
```

**Solution:**
- Check TOML syntax
- Ensure strings have quotes: `root = "/path"` not `root = /path`
- Validate with: `python -c "import tomllib; tomllib.load(open('config/air-executor.toml', 'rb'))"`

### Error: Validation failed

```
ValueError: Wrapper script not found: /path/to/claude_wrapper.py
```

**Solution:**
- Check paths in config are correct
- Ensure files exist
- Run: `ls -la $(python -c "from air_executor.config import load_config; print(load_config().wrapper_path)")`

### Error: Module not found (tomli)

```
ModuleNotFoundError: No module named 'tomli'
```

**Solution (Python < 3.11 only):**
```bash
pip install tomli
```

Python 3.11+ has built-in `tomllib`.

---

## Migration from Hardcoded Paths

### Before (Hardcoded)

```python
# ❌ OLD: Hardcoded paths
wrapper_path = Path("/home/rmondo/repos/air-executor/scripts/claude_wrapper.py")
venv_python = Path("/home/rmondo/repos/air-executor/.venv/bin/python")
timeout = 60
```

### After (Config-Driven)

```python
# ✅ NEW: Config-driven
from air_executor.config import load_config

config = load_config()
wrapper_path = config.wrapper_path
venv_python = config.venv_python
timeout = config.claude_timeout
```

**Benefits:**
- Works on any machine (just update config.toml)
- Easy to change timeout/settings
- Can override with environment variables
- Validated automatically

---

## Best Practices

### 1. Use Example Template

```bash
# Always start from example
cp config/air-executor.example.toml config/air-executor.toml
```

### 2. Document Custom Values

```toml
# Custom timeout for long-running queries
timeout_seconds = 300  # 5 minutes for complex analysis
```

### 3. Environment-Specific Configs

**Development:**
```toml
# config/air-executor.dev.toml
[development]
debug = true
```

**Production:**
```toml
# config/air-executor.prod.toml
[development]
debug = false
validate_config = true
```

Load with:
```bash
export AIR_EXECUTOR_CONFIG=config/air-executor.prod.toml
```

### 4. Keep Secrets in .env

```toml
# config/air-executor.toml - Public settings
[claude]
timeout_seconds = 60
```

```bash
# .env - Secrets (gitignored)
CLAUDE_API_KEY=sk-ant-...
DATABASE_PASSWORD=secret
```

### 5. Version Control

```bash
# Commit example, ignore actual config
git add config/air-executor.example.toml
git add .gitignore  # Ignores config/air-executor.toml
```

---

## Summary

✅ **Created:** TOML config system
✅ **Benefits:** Environment-independent, easy customization
✅ **Updated:** DAGs now use config (no hardcoded paths)
✅ **Flexible:** Environment variable overrides
✅ **Validated:** Automatic path validation

**Next steps:**
1. Copy `config/air-executor.example.toml` → `config/air-executor.toml`
2. Edit paths for your environment
3. Test: `python -c "from air_executor.config import load_config; print(load_config())"`
4. Deploy DAGs: They automatically use your config!

**Your Airflow DAGs now work on any machine with the correct config.toml! 🎉**
