# Configuration Reference

Complete reference for Air Executor configuration options.

## Configuration File

Air Executor uses TOML format for configuration: `config/air-executor.toml`

### Example Configuration

```toml
[project]
name = "air-executor"
root = "/home/user/repos/air-executor"

[paths]
wrapper_script = "scripts/claude_wrapper.py"
venv_python = "${HOME}/.venv/air-executor/bin/python"

[claude]
timeout = 300
permission_mode = "bypassPermissions"

[airflow]
dags_folder = "${HOME}/airflow/dags"
```

## Configuration Sections

### `[project]`

Project-level settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | - | Project name |
| `root` | path | - | Project root directory |

### `[paths]`

File path configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `wrapper_script` | path | `scripts/claude_wrapper.py` | Claude wrapper script path |
| `venv_python` | path | - | Python interpreter in virtual environment |

### `[claude]`

Claude AI configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `timeout` | integer | 300 | Task timeout in seconds |
| `permission_mode` | string | `default` | Permission mode (`default`, `bypassPermissions`) |

### `[airflow]`

Airflow integration settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dags_folder` | path | `~/airflow/dags` | Airflow DAGs directory |

### `[autonomous_fixing]`

Autonomous code fixing configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `target_project` | path | - | Target project to fix |
| `batch_size` | integer | 3 | Number of fixes per iteration |
| `max_iterations` | integer | 20 | Maximum fixing iterations |

## Environment Variables

Air Executor supports environment variable expansion in configuration:

```toml
venv_python = "${HOME}/.venv/air-executor/bin/python"
project_root = "${PROJECT_ROOT}/src"
```

## Configuration Loading

```python
from air_executor.config import load_config

# Load configuration
config = load_config()

# Access values
wrapper_path = config.wrapper_path
timeout = config.claude_timeout
```

## Configuration Validation

```bash
# Validate configuration
python -c "from air_executor.config import load_config; load_config()"
```

## See Also

- [Getting Started](../getting-started/configuration.md) - Configuration guide
- [Troubleshooting](./troubleshooting.md) - Common configuration issues
