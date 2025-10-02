# Configuration System - Quick Reference

## ✅ Implemented

Air Executor now uses **TOML configuration** instead of hardcoded paths!

### What Changed

**Before:**
```python
# ❌ Hardcoded, breaks on different machines
wrapper_path = Path("/home/rmondo/repos/air-executor/scripts/claude_wrapper.py")
```

**After:**
```python
# ✅ Config-driven, works anywhere
from air_executor.config import load_config
config = load_config()
wrapper_path = config.wrapper_path
```

---

## 🚀 Quick Start

### 1. Create Config

```bash
cp config/air-executor.example.toml config/air-executor.toml
```

### 2. Edit Paths

```toml
# config/air-executor.toml

[project]
root = "/home/YOUR_USERNAME/repos/air-executor"  # ← Change

[airflow]
home = "/home/YOUR_USERNAME/airflow"              # ← Change
```

### 3. Verify

```bash
source .venv/bin/activate
python -c "from air_executor.config import load_config; print(load_config())"
```

### 4. Done!

DAGs automatically use your config. No code changes needed!

---

## 📋 Why TOML?

Compared other formats (.env, JSON, YAML, TOML):

| Format | Comments | Types | Nested | Python Std | Score |
|--------|----------|-------|--------|------------|-------|
| .env   | ✅ | ❌ | ❌ | ❌ | 6/10 |
| JSON   | ❌ | ✅ | ✅ | ✅ | 7/10 |
| YAML   | ✅ | ✅ | ✅ | ❌ | 9/10 |
| **TOML** | **✅** | **✅** | **✅** | **✅ (3.11+)** | **10/10** ✅ |

**TOML wins because:**
- ✅ Built into Python 3.11+ (`tomllib`)
- ✅ Python ecosystem standard (`pyproject.toml`)
- ✅ Comments supported
- ✅ Clear, unambiguous syntax
- ✅ Perfect for our use case

---

## 📁 File Structure

```
air-executor/
├── config/
│   ├── air-executor.example.toml  # ✅ Template (committed)
│   └── air-executor.toml          # ⚠️  Your config (gitignored)
│
├── src/air_executor/
│   └── config.py                  # ✅ Config loader
│
├── airflow_dags/
│   └── claude_query_sdk.py        # ✅ Uses config (no hardcoded paths!)
│
└── .env                           # ⚠️  Secrets (gitignored)
```

---

## 🎯 Config Structure

```toml
# config/air-executor.toml

[project]
root = "/home/user/repos/air-executor"
scripts_dir = "scripts"
venv_python = ".venv/bin/python"

[airflow]
home = "/home/user/airflow"
dags_folder = "dags"

[claude]
timeout_seconds = 60
permission_mode = "bypassPermissions"

[claude.default_options]
exit_on_complete = true
resume_last_session = false
```

---

## 🔧 Environment Overrides

Override config with environment variables:

```bash
# .env
AIR_EXECUTOR_ROOT=/custom/path
AIRFLOW_HOME=/opt/airflow
CLAUDE_TIMEOUT=120
```

Or:

```bash
export AIR_EXECUTOR_ROOT=/custom/path
python your_script.py
```

---

## 📖 Documentation

- **Analysis:** `claudedocs/CONFIG_FORMAT_ANALYSIS.md` - Why TOML?
- **Guide:** `claudedocs/CONFIG_USAGE_GUIDE.md` - Complete usage guide
- **This file:** Quick reference

---

## ✨ Benefits

### Before (Hardcoded)
- ❌ Paths break on different machines
- ❌ Need to edit multiple files
- ❌ Hard to track changes
- ❌ No environment-specific settings

### After (Config-Driven)
- ✅ Works on any machine
- ✅ Edit one file (`config.toml`)
- ✅ Version controlled
- ✅ Environment overrides (`.env`)
- ✅ Validated automatically

---

## 🎉 Summary

**What we built:**
1. ✅ TOML config file (`config/air-executor.toml`)
2. ✅ Config loader (`src/air_executor/config.py`)
3. ✅ Updated DAG to use config (no hardcoded paths)
4. ✅ Environment variable support
5. ✅ Automatic validation
6. ✅ Comprehensive documentation

**Result:**
Your Airflow DAGs are now **environment-independent** and will work on any machine with the correct `config.toml`!

**Next:** Just create your `config.toml` and you're ready to go! 🚀
