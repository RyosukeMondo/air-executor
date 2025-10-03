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
