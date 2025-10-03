# Development Tools Setup

Setup scripts for installing development tools required by the autonomous fixing system.

## Overview

Each language has a setup script that installs all tools defined in the project configs:
- `setup_python.sh` - Installs pylint, mypy, pytest, coverage, radon
- `setup_javascript.sh` - Installs eslint, typescript, jest, prettier, ts-node
- `setup_go.sh` - Installs Go SDK, staticcheck, gocyclo, golint
- `setup_flutter.sh` - Installs Flutter SDK, dart, flutter analyze, flutter test

## Quick Start

### Python Tools
```bash
# User installation (recommended)
./scripts/setup_python.sh

# System-wide installation
./scripts/setup_python.sh --sudo
```

**Installs**:
- pylint (linter)
- mypy (type checker)
- pytest (test runner)
- coverage (coverage analysis)
- radon (complexity metrics)

### JavaScript/TypeScript Tools
```bash
# User installation
./scripts/setup_javascript.sh

# System-wide installation
./scripts/setup_javascript.sh --sudo
```

**Installs**:
- eslint (linter)
- typescript/tsc (type checker)
- jest (test runner)
- prettier (code formatter)
- ts-node (TypeScript execution)

**Note**: If you get permission errors with npm, configure npm to use a user directory:
```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.profile
source ~/.profile
```

### Go Tools
```bash
# User installation (recommended)
./scripts/setup_go.sh

# System-wide installation
./scripts/setup_go.sh --sudo
```

**Installs**:
- Go SDK (if not present)
- go vet (built-in static analysis)
- staticcheck (advanced linter)
- gocyclo (complexity metrics)
- golint (additional linting)

**Important**: After installation, reload your shell:
```bash
source ~/.profile
# Or restart your terminal
```

### Flutter Tools
```bash
# User installation (recommended)
./scripts/setup_flutter.sh

# System-wide dependencies (if needed)
./scripts/setup_flutter.sh --sudo
```

**Installs**:
- Flutter SDK (if not present)
- dart (comes with Flutter)
- flutter analyze (static analysis)
- flutter test (test runner)

**Important**: After installation, reload your shell:
```bash
source ~/.profile
# Or restart your terminal
```

Then verify with:
```bash
flutter doctor
```

## Verify Installation

After running setup scripts, verify all tools are installed correctly:

```bash
# Check specific language
python3 airflow_dags/autonomous_fixing/core/tool_validator.py --check-flutter
python3 airflow_dags/autonomous_fixing/core/tool_validator.py config/projects/money-making-app.yaml

# Check all languages
PYTHONPATH=/home/rmondo/repos/air-executor python3 airflow_dags/autonomous_fixing/core/tool_validator.py --check-all
```

**Expected Output**:
```
================================================================================
🔧 TOOL VALIDATION
================================================================================

📋 Validating PYTHON toolchain...
   ✅ python (v3.12.3) @ /usr/bin/python3
   ✅ pylint (v3.0.0) @ /usr/local/bin/pylint
   ✅ mypy (v1.8.0) @ /usr/local/bin/mypy
   ✅ pytest (v7.4.3) @ /usr/local/bin/pytest
   ✅ coverage (v7.4.0) @ /usr/local/bin/coverage

📋 Validating JAVASCRIPT toolchain...
   ✅ node (v18.19.1) @ /usr/bin/node
   ✅ npm (v9.2.0) @ /usr/bin/npm
   ✅ eslint (v8.56.0) @ /usr/bin/eslint
   ✅ jest (v29.7.0) @ /usr/bin/jest

... etc
```

## Tool Configuration

Tools are configured in project config files:

### Python (`config/projects/air-executor.yaml`)
```yaml
languages:
  python:
    linters: ["pylint", "mypy"]
    test_framework: "pytest"
```

### JavaScript (`config/projects/cc-task-manager.yaml`)
```yaml
languages:
  javascript:
    linters: ["eslint"]
    type_checker: "tsc"
    test_framework: "jest"
```

### Flutter (`config/projects/money-making-app.yaml`)
```yaml
languages:
  flutter:
    analyzer_args: "--fatal-infos --fatal-warnings"
    test_timeout: 600
```

## Troubleshooting

### Python: pip install fails
**Problem**: Permission denied when installing packages

**Solution**: Use `--user` flag (default) or setup virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
./scripts/setup_python.sh
```

### JavaScript: npm permission errors
**Problem**: Cannot write to /usr/local/lib/node_modules

**Solution 1**: Use user npm directory:
```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH
```

**Solution 2**: Use sudo:
```bash
./scripts/setup_javascript.sh --sudo
```

### Go: Command not found after installation
**Problem**: `go: command not found` after running setup

**Solution**: Reload shell configuration:
```bash
source ~/.profile
# Or
source ~/.bashrc
# Or restart terminal
```

Verify PATH includes Go:
```bash
echo $PATH | grep go
```

### Flutter: Command not found
**Problem**: `flutter: command not found` after running setup

**Solution**: Same as Go - reload shell or restart terminal:
```bash
source ~/.profile
flutter doctor
```

### Tool validator reports "NOT FOUND"
**Problem**: Tool installed but validator can't find it

**Solution**: Check if tool is in PATH:
```bash
which pylint
which eslint
which go
which flutter
```

If not in PATH, add to ~/.profile:
```bash
echo 'export PATH=$PATH:/path/to/tool' >> ~/.profile
source ~/.profile
```

## Uninstallation

### Python Tools
```bash
pip3 uninstall pylint mypy pytest coverage radon
```

### JavaScript Tools
```bash
npm uninstall -g eslint typescript jest prettier ts-node
```

### Go Tools
```bash
# Remove Go SDK
sudo rm -rf /usr/local/go
# Or for user installation
rm -rf ~/go-sdk

# Remove installed tools
rm -rf ~/go/bin
```

### Flutter
```bash
rm -rf ~/flutter
# Remove from PATH (edit ~/.profile and remove Flutter lines)
```

## CI/CD Integration

For automated setups in CI/CD pipelines:

```bash
# Non-interactive installation
./scripts/setup_python.sh --sudo
./scripts/setup_javascript.sh --sudo

# Verify installation
python3 airflow_dags/autonomous_fixing/core/tool_validator.py --check-all
if [ $? -ne 0 ]; then
    echo "Tool validation failed"
    exit 1
fi
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run tool validator to see which tools are missing
3. Verify your PATH includes tool installation directories
4. Check tool-specific documentation for installation issues
