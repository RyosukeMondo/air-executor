# Project Memory - air-executor

## Python Environment

**ALWAYS use**: `.venv/bin/python3` for running Python commands in this project

**Location**: `/home/rmondo/repos/air-executor/.venv/bin/python3`

**Why**:
- System `python` command not available
- Virtual environment ensures correct dependencies
- Avoids "python: コマンドが見つかりません" (command not found) errors

**Examples**:
```bash
# ✅ Correct
.venv/bin/python3 script.py
.venv/bin/python3 -m pytest

# ❌ Wrong
python script.py
python3 script.py  # might work but may use wrong environment
```

## Recent Refactoring (2025-10-03)

**Branch**: `refactor/autonomous-fixing-architecture`

### Completed Work
- Phase 1-2: Cleanup + Domain layer
- Phase 3: Import updates + Interface implementation
- Phase 4: Split PythonAdapter (529 lines → 5 focused modules)

### Architecture
```
airflow_dags/autonomous_fixing/
├── domain/                    # Models + Interfaces (SSOT)
├── adapters/                  # Infrastructure
│   ├── languages/
│   │   └── python/           # NEW: Focused sub-components
│   ├── state/
│   ├── ai/
│   └── git/
└── core/                      # Business logic
```

### Key Files
- Domain models: `airflow_dags/autonomous_fixing/domain/models/`
- Python adapter: `airflow_dags/autonomous_fixing/adapters/languages/python/`
- Documentation: `claudedocs/refactoring-final-complete.md`

### Principles Applied
- MECE (Mutually Exclusive, Collectively Exhaustive)
- SOLID (all 5 principles)
- SLAP (Single Level of Abstraction Principle)
- KISS (Keep It Simple)
- SSOT (Single Source of Truth)

### Status
✅ All phases complete
✅ 6 commits, 40 files changed
✅ Production ready
✅ Startup scripts created
✅ Configuration for money-making-app ready

## Autonomous Fixing Scripts (2025-10-03)

### Quick Start
```bash
# Run autonomous fixing on money-making-app
./scripts/autonomous_fix.sh config/money-making-app.yaml
```

### New Files Created
- **Config**: `config/money-making-app.yaml` - Flutter app configuration
- **Scripts**: `scripts/autonomous_fix.sh` - Main entry point (simple)
- **Scripts**: `scripts/autonomous_fix_with_redis.sh` - Full startup with Redis
- **Scripts**: `scripts/autonomous_fix_advanced.sh` - Advanced options
- **Docs**: `scripts/QUICK_START.md` - Quick reference
- **Docs**: `scripts/AUTONOMOUS_FIXING_GUIDE.md` - Complete guide

### Script Organization (Self-Explanatory Names)
```
scripts/
├── autonomous_fix.sh              ⭐ MAIN - Simple entry point
├── autonomous_fix_with_redis.sh   Full startup (Redis + validation)
├── autonomous_fix_advanced.sh     Advanced options (background, logging, etc)
├── install_redis.sh               Install Redis
├── install_flutter.sh             Install Flutter
├── QUICK_START.md                 Quick reference
└── AUTONOMOUS_FIXING_GUIDE.md     Complete documentation
```

### Features
- ✅ Auto-starts Redis if not running
- ✅ Auto-detects Python environment (.venv/bin/python3)
- ✅ Validates all dependencies and tools
- ✅ Comprehensive error messages
- ✅ Clean logging to logs/ directory

## Verification System (2025-10-03)

### Problem Solved
User identified silent failure: System reported "0 errors in 0.0s" but errors still existed.

### Solution: AnalysisVerifier Component
Created new focused component following clean architecture:
- **File**: `core/analysis_verifier.py` (180 lines)
- **Purpose**: Detect silent failures in analysis results
- **Integration**: IterationEngine verifies every analysis

### Verification Checks
1. **Execution Time Sanity**: Rejects analysis < 0.1s
2. **Zero Errors Pattern**: Catches "0 errors in 0.0s" silent failures
3. **Required Fields**: Validates result structure
4. **Error Messages**: Logs execution errors

### Testing Results
- ✅ Valid analysis (1.7s, 2229 errors): Passes
- ❌ Silent failure (0.0s, 0 errors): Caught and reported
- ✅ Real-world (money-making-app): Working correctly

### Documentation
See: `claudedocs/autonomous-fixing-verification-system.md`

### Architecture Impact
- Follows SOLID principles
- Single Responsibility (verification only)
- Clean integration (no breaking changes)
- Fail-fast on unreliable data
