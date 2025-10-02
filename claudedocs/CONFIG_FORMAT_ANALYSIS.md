# Config Format Analysis for Air Executor

## Use Case Requirements

**What we need to configure:**
1. **Paths** - Project root, scripts directory, venv location
2. **Airflow settings** - DAGs folder, logs location
3. **Claude wrapper options** - Default timeout, permission mode
4. **Environment-specific values** - Development vs Production

**Key criteria:**
- ✅ Easy to read and edit
- ✅ Good Python ecosystem support
- ✅ Supports comments
- ✅ Environment variable substitution
- ✅ Validation support
- ✅ Already used in Python ecosystem

---

## Format Comparison

### 1. .env (Environment Variables)

**Example:**
```bash
# .env
AIR_EXECUTOR_ROOT=/home/rmondo/repos/air-executor
AIRFLOW_HOME=/home/rmondo/airflow
CLAUDE_WRAPPER_TIMEOUT=60
CLAUDE_PERMISSION_MODE=bypassPermissions
```

**Pros:**
- ✅ Simple key=value format
- ✅ Industry standard for secrets/env config
- ✅ Supported by many tools (docker, systemd, etc.)
- ✅ Easy environment variable integration
- ✅ Libraries: `python-dotenv`

**Cons:**
- ❌ No nested structure (flat only)
- ❌ No data types (everything is string)
- ❌ No lists/arrays support
- ❌ Limited to simple configs

**Best for:** Secrets, environment variables, simple key-value configs

**Score: 6/10** - Too simple for our needs

---

### 2. JSON

**Example:**
```json
{
  "project": {
    "root": "/home/rmondo/repos/air-executor",
    "scripts_dir": "scripts",
    "venv_path": ".venv/bin/python"
  },
  "airflow": {
    "home": "/home/rmondo/airflow",
    "dags_folder": "dags",
    "logs_folder": "logs"
  },
  "claude": {
    "wrapper_timeout": 60,
    "permission_mode": "bypassPermissions",
    "default_prompt": "hello, how old are you?"
  }
}
```

**Pros:**
- ✅ Built into Python (no dependencies)
- ✅ Structured/nested data
- ✅ Data types (string, number, boolean, null)
- ✅ Arrays/lists support
- ✅ Universal format (language-agnostic)

**Cons:**
- ❌ No comments (major pain point!)
- ❌ Strict syntax (trailing commas break it)
- ❌ Not human-friendly for editing
- ❌ No environment variable substitution

**Best for:** API configs, data interchange

**Score: 7/10** - Lack of comments is a dealbreaker

---

### 3. YAML

**Example:**
```yaml
# Air Executor Configuration

project:
  root: /home/rmondo/repos/air-executor
  scripts_dir: scripts
  venv_path: .venv/bin/python

airflow:
  home: /home/rmondo/airflow
  dags_folder: dags
  logs_folder: logs

claude:
  wrapper_timeout: 60
  permission_mode: bypassPermissions
  default_options:
    exit_on_complete: true
    resume_last_session: false

  # Common prompts
  prompts:
    - "hello, how old are you?"
    - "what is 2+2?"
```

**Pros:**
- ✅ **Comments supported!**
- ✅ Very readable and human-friendly
- ✅ Nested structures
- ✅ Data types (inferred)
- ✅ Lists/arrays/dicts
- ✅ Popular in DevOps (Docker Compose, Kubernetes, CI/CD)
- ✅ Libraries: `PyYAML`, `ruamel.yaml`

**Cons:**
- ⚠️ Whitespace-sensitive (can be error-prone)
- ⚠️ Complex spec (many features, hard to master)
- ❌ No built-in env var substitution (need library support)

**Best for:** Application configs, Docker Compose, Kubernetes manifests

**Score: 9/10** - Excellent for complex configs

---

### 4. TOML

**Example:**
```toml
# Air Executor Configuration

[project]
root = "/home/rmondo/repos/air-executor"
scripts_dir = "scripts"
venv_path = ".venv/bin/python"

[airflow]
home = "/home/rmondo/airflow"
dags_folder = "dags"
logs_folder = "logs"

[claude]
wrapper_timeout = 60
permission_mode = "bypassPermissions"

[claude.default_options]
exit_on_complete = true
resume_last_session = false

# Common prompts
[[claude.prompts]]
text = "hello, how old are you?"

[[claude.prompts]]
text = "what is 2+2?"
```

**Pros:**
- ✅ **Comments supported!**
- ✅ **Built into Python 3.11+** (`tomllib`)
- ✅ Explicit data types (strings need quotes)
- ✅ Nested structures with sections
- ✅ Lists/arrays/tables
- ✅ Used by Python ecosystem (`pyproject.toml`, `poetry`, `black`, `pytest`)
- ✅ Simple, unambiguous syntax
- ✅ Libraries: `tomli` (3.10 and below), `tomllib` (3.11+)

**Cons:**
- ⚠️ Slightly more verbose than YAML
- ⚠️ Less familiar than JSON/YAML for some users
- ❌ No built-in env var substitution (need custom logic)

**Best for:** Python project configs, application settings

**Score: 10/10** - **RECOMMENDED** ✅

---

## Recommendation: TOML

### Why TOML?

1. **Python Native (3.11+)**
   - Built-in `tomllib` module (read-only)
   - No external dependencies for reading config

2. **Python Ecosystem Standard**
   - `pyproject.toml` - Official Python project config
   - Used by: Poetry, Black, Pytest, Ruff, MyPy, etc.
   - Developers already familiar with it

3. **Clear Syntax**
   - Explicit types (strings have quotes)
   - Sections clearly marked with `[section]`
   - No ambiguity (unlike YAML's whitespace)

4. **Comments Support**
   - Critical for documenting config values
   - Explain defaults, provide examples

5. **Perfect for Our Use Case**
   - Mix of paths (strings)
   - Numbers (timeout, ports)
   - Booleans (flags)
   - Nested config (project, airflow, claude sections)
   - Lists (multiple prompts, multiple paths)

### Comparison for Air Executor

```toml
# config.toml - Clean, documented, type-safe

# === Project Paths ===
[project]
root = "/home/rmondo/repos/air-executor"  # Main project directory
scripts_dir = "scripts"                   # Relative to root
venv_python = ".venv/bin/python"          # Python executable

# === Airflow Configuration ===
[airflow]
home = "/home/rmondo/airflow"             # Airflow home directory
dags_folder = "dags"                      # Relative to airflow.home
logs_folder = "logs"                      # Relative to airflow.home

# === Claude Wrapper Settings ===
[claude]
wrapper_script = "claude_wrapper.py"      # Relative to scripts_dir
timeout_seconds = 60                      # Query timeout
permission_mode = "bypassPermissions"     # Auto-approve all operations

[claude.default_options]
exit_on_complete = true                   # Auto-shutdown after query
resume_last_session = false               # Start fresh session
```

**vs YAML:**
```yaml
# config.yaml - Good but less explicit types

project:
  root: /home/rmondo/repos/air-executor   # String? Need quotes?
  scripts_dir: scripts
  venv_python: .venv/bin/python

airflow:
  home: /home/rmondo/airflow
  dags_folder: dags

claude:
  wrapper_script: claude_wrapper.py
  timeout_seconds: 60                     # Number or string?
  permission_mode: bypassPermissions      # String? Boolean?
```

**vs JSON:**
```json
{
  "project": {
    "root": "/home/rmondo/repos/air-executor"
  },
  "_comment": "Can't add comments here!"
}
```

---

## Implementation Strategy

### Phase 1: TOML Config File ✅

```toml
# config/air-executor.toml

[project]
root = "/home/rmondo/repos/air-executor"
scripts_dir = "scripts"
venv_python = ".venv/bin/python"

[airflow]
home = "/home/rmondo/airflow"

[claude]
timeout_seconds = 60
permission_mode = "bypassPermissions"
```

### Phase 2: Config Loader

```python
# src/air_executor/config.py

import tomllib  # Python 3.11+
from pathlib import Path
from typing import TypedDict

class ProjectConfig(TypedDict):
    root: str
    scripts_dir: str
    venv_python: str

class Config:
    def __init__(self, config_path: Path):
        with open(config_path, "rb") as f:
            self._config = tomllib.load(f)

    @property
    def wrapper_path(self) -> Path:
        root = Path(self._config["project"]["root"])
        scripts = self._config["project"]["scripts_dir"]
        return root / scripts / "claude_wrapper.py"
```

### Phase 3: Environment Overrides (.env)

```python
# Support environment variables to override config
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

# Override config with env vars
project_root = os.getenv("AIR_EXECUTOR_ROOT") or config["project"]["root"]
```

### Phase 4: Validation with Pydantic

```python
from pydantic import BaseModel, Field

class ClaudeConfig(BaseModel):
    timeout_seconds: int = Field(gt=0, le=300)
    permission_mode: str = Field(pattern="^(bypassPermissions|ask)$")

# Validates on load
config = ClaudeConfig(**toml_data["claude"])
```

---

## Migration Path

### Step 1: Create config.toml
```bash
cp config/air-executor.example.toml config/air-executor.toml
# Edit with your paths
```

### Step 2: Update DAGs
```python
# OLD
wrapper_path = Path("/home/rmondo/repos/air-executor/scripts/claude_wrapper.py")

# NEW
from air_executor.config import load_config
config = load_config()
wrapper_path = config.wrapper_path
```

### Step 3: Environment Overrides (optional)
```bash
# .env (for secrets, environment-specific values)
AIR_EXECUTOR_ROOT=/custom/path
CLAUDE_API_KEY=sk-ant-...
```

---

## Final Decision

**Use TOML** for the following reasons:

1. ✅ **Python 3.11+ built-in** - No dependencies
2. ✅ **Python ecosystem standard** - Familiar to developers
3. ✅ **Comments supported** - Document config values
4. ✅ **Type clarity** - Explicit syntax, no ambiguity
5. ✅ **Perfect fit** - Paths, numbers, booleans, nested config

**Complement with .env** for:
- Secrets (API keys, passwords)
- Environment-specific overrides
- CI/CD variable injection

**Implementation:**
```
config/
├── air-executor.toml          # Main config (committed)
├── air-executor.example.toml  # Template (committed)
└── .env                        # Secrets (gitignored)
```

This gives us:
- **TOML** for structured, documented configuration
- **.env** for secrets and environment overrides
- **Pydantic** for validation (optional enhancement)

**Next:** Implement TOML-based configuration system! 🚀
