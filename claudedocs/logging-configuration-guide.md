# Logging Configuration Guide

## Overview

The Air-Executor project now supports **YAML-driven logging configuration** across all components:
- `claude_wrapper.py` (wrapper process stderr logging)
- `ClaudeClient` (autonomous fixing debug output)
- `claude_query_sdk.py` (Airflow DAG execution)
- `DebugLogger` (structured JSON logging)

## Configuration Structure

All logging configuration is defined in your project YAML file (e.g., `config/projects/warps.yaml`):

```yaml
logging:
  level: "INFO"  # Global log level: DEBUG, INFO, WARNING, ERROR
  file: "logs/fix-warps.log"

  # Wrapper-specific logging (passed to claude_wrapper.py)
  wrapper:
    level: "DEBUG"  # Controls claude_wrapper.py stderr logging (INFO or DEBUG)
    show_events: true  # Show [WRAPPER DEBUG] event logs from ClaudeClient

  # Debug logger configuration (DebugLogger component)
  debug:
    enabled: true
    log_dir: "logs/debug"
    log_levels:
      wrapper_responses: false  # Include full wrapper responses in debug logs (verbose)
      wrapper_calls: true       # Log all wrapper calls with timing
```

## Configuration Options

### Global Logging

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | string | `"INFO"` | Global log level (DEBUG, INFO, WARNING, ERROR) |
| `file` | string | `"logs/fix-warps.log"` | Main log file path |

### Wrapper Logging (`logging.wrapper`)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | string | `"INFO"` | Controls `claude_wrapper.py` stderr logging verbosity |
| `show_events` | boolean | `false` | Show `[WRAPPER DEBUG]` event logs from `ClaudeClient` |

**How it works:**
- `level` is passed to `claude_wrapper.py` via `CLAUDE_WRAPPER_LOG_LEVEL` environment variable
- `show_events` controls whether `ClaudeClient` prints event logs to stdout during execution

### Debug Logger (`logging.debug`)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable structured JSON debug logging |
| `log_dir` | string | `"logs/debug"` | Directory for debug log files |
| `log_levels.wrapper_responses` | boolean | `false` | Include full wrapper responses (very verbose) |
| `log_levels.wrapper_calls` | boolean | `true` | Log all wrapper calls with timing |

## Usage Scenarios

### Scenario 1: Quiet Production Mode
```yaml
logging:
  level: "WARNING"
  wrapper:
    level: "WARNING"
    show_events: false
  debug:
    enabled: false
```

**Result:**
- ❌ No `[WRAPPER DEBUG]` output
- ❌ No debug logs
- ✅ Only warnings/errors in stderr

---

### Scenario 2: Development/Debugging Mode (Your Current Config)
```yaml
logging:
  level: "INFO"
  wrapper:
    level: "DEBUG"
    show_events: true
  debug:
    enabled: true
    log_dir: "logs/debug"
    log_levels:
      wrapper_responses: false
      wrapper_calls: true
```

**Result:**
- ✅ `[WRAPPER DEBUG]` output visible (e.g., `[WRAPPER DEBUG] [02:52.73] ready`)
- ✅ Structured JSON logs in `logs/debug/`
- ✅ Wrapper call timing and success/failure tracking
- ❌ Full responses not logged (keeps logs readable)

---

### Scenario 3: Maximum Verbosity (Troubleshooting)
```yaml
logging:
  level: "DEBUG"
  wrapper:
    level: "DEBUG"
    show_events: true
  debug:
    enabled: true
    log_dir: "logs/debug"
    log_levels:
      wrapper_responses: true  # ⚠️ Very verbose!
      wrapper_calls: true
```

**Result:**
- ✅ All debug information
- ✅ Full wrapper responses in JSON logs
- ⚠️ **Warning:** Large log files, use only for critical debugging

---

## Component Flow

### Autonomous Fixing (ClaudeClient)

```
config/projects/warps.yaml
    ↓ (loaded by IterationEngine)
    ↓
IssueFixer.__init__(config)
    ↓
ClaudeClient.__init__(wrapper_path, python_exec, debug_logger, config)
    ↓ (query() method)
    ↓
_setup_environment()
    ├─ Sets env["CLAUDE_WRAPPER_LOG_LEVEL"] = config.logging.wrapper.level
    └─ debug_mode = debug_logger is not None AND config.logging.wrapper.show_events
    ↓
subprocess.Popen([python_exec, wrapper_path], env=env)
    ↓
claude_wrapper.py starts with CLAUDE_WRAPPER_LOG_LEVEL from environment
```

### Airflow DAG Execution (claude_query_sdk)

```
config/air-executor.toml
    ↓ (loaded via load_config())
    ↓
run_claude_query_sdk(**context)
    ↓
env["CLAUDE_WRAPPER_LOG_LEVEL"] = config.logging.wrapper.level
    ↓
subprocess.Popen([venv_python, wrapper_path], env=env)
    ↓
claude_wrapper.py starts with log level from config
```

## Log Output Examples

### With `show_events: true` (Current Behavior)
```
🔧 Fixing P2 test failures (iteration 1)...
   Found 1 projects with test failures
   Fixing 28 failing tests in warps

[WRAPPER DEBUG] Starting claude_wrapper
[WRAPPER DEBUG] Wrapper: /home/rmondo/repos/air-executor/scripts/claude_wrapper.py
[WRAPPER DEBUG] CWD: /home/rmondo/repos/warps
[WRAPPER DEBUG] Prompt type: fix_test
[WRAPPER DEBUG] PATH: /home/rmondo/.nvm/...
[WRAPPER DEBUG] Process started (PID: 608948)
[WRAPPER DEBUG] [02:52.73] ready
[WRAPPER DEBUG] [02:52.73] run_started
[WRAPPER DEBUG] [02:58.61] stream (text: I'll help you fix...)
```

### With `show_events: false` (Quiet Mode)
```
🔧 Fixing P2 test failures (iteration 1)...
   Found 1 projects with test failures
   Fixing 28 failing tests in warps

      ✓ Fixed successfully
```

## Environment Variable Override

You can also override the log level via environment variable (takes precedence over YAML):

```bash
# Override for single execution
CLAUDE_WRAPPER_LOG_LEVEL=DEBUG .venv/bin/python3 run_orchestrator.py

# Or export for session
export CLAUDE_WRAPPER_LOG_LEVEL=WARNING
.venv/bin/python3 run_orchestrator.py
```

## Troubleshooting

### Issue: No `[WRAPPER DEBUG]` logs appearing

**Check:**
1. `logging.wrapper.show_events` is set to `true` in YAML
2. `debug_logger` is being passed to `ClaudeClient` (check `IssueFixer.__init__`)
3. `DebugLogger` is enabled: `logging.debug.enabled: true`

### Issue: Too much log output

**Solution:**
```yaml
logging:
  wrapper:
    show_events: false  # Disable [WRAPPER DEBUG] output
  debug:
    log_levels:
      wrapper_responses: false  # Don't log full responses
```

### Issue: Wrapper stderr logs too verbose

**Solution:**
```yaml
logging:
  wrapper:
    level: "WARNING"  # Only show warnings/errors in wrapper stderr
```

## Best Practices

1. **Production:** Use `level: "WARNING"`, `show_events: false`, `debug.enabled: false`
2. **Development:** Use `level: "INFO"`, `show_events: true`, `debug.enabled: true`
3. **Debugging:** Use `level: "DEBUG"`, `wrapper_responses: true` temporarily
4. **CI/CD:** Use `show_events: false` to keep logs clean

## Related Files

- **Config:** `config/projects/warps.yaml`
- **Wrapper:** `scripts/claude_wrapper.py` (reads `CLAUDE_WRAPPER_LOG_LEVEL`)
- **Client:** `airflow_dags/autonomous_fixing/adapters/ai/claude_client.py`
- **SDK:** `airflow_dags/claude_query_sdk.py`
- **Debug Logger:** `airflow_dags/autonomous_fixing/core/debug_logger.py`
