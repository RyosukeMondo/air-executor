#!/bin/bash
# Unified DAG sync script with auto-detection, validation, and cleanup

set -e

PROJECT_ROOT="/home/rmondo/repos/air-executor"
AIRFLOW_DAGS="/home/rmondo/airflow/dags"
VENV_PYTHON="/home/rmondo/repos/air-executor/.venv/bin/python"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Sync DAG files to Airflow with validation and cleanup"
    echo ""
    echo "Options:"
    echo "  --symlink       Create symlinks instead of copying (dev mode)"
    echo "  --copy          Copy files (default, safe for production)"
    echo "  --auto-unpause  Automatically unpause new DAGs"
    echo "  --cleanup       Clean up stale DAG metadata"
    echo "  --dry-run       Show what would be done"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                           # Copy and validate"
    echo "  $0 --symlink --auto-unpause  # Dev mode with auto-unpause"
    echo "  $0 --cleanup                 # Sync and clean up stale DAGs"
}

symlink_mode=false
auto_unpause=false
cleanup_stale=false
dry_run=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --symlink) symlink_mode=true; shift ;;
        --copy) symlink_mode=false; shift ;;
        --auto-unpause) auto_unpause=true; shift ;;
        --cleanup) cleanup_stale=true; shift ;;
        --dry-run) dry_run=true; shift ;;
        --help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

echo -e "${BLUE}📦 Syncing DAG files to Airflow${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Source: $PROJECT_ROOT/airflow_dags"
echo "Target: $AIRFLOW_DAGS"
[ "$symlink_mode" = true ] && echo -e "Mode: ${BLUE}Symlink${NC}" || echo -e "Mode: ${BLUE}Copy${NC}"
[ "$dry_run" = true ] && echo -e "${YELLOW}DRY RUN MODE${NC}"
echo ""

# Create directory if needed
mkdir -p "$AIRFLOW_DAGS"

# Auto-discover all Python files
echo -e "${BLUE}📋 Auto-discovering DAG files...${NC}"
DAG_FILES=()
while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    DAG_FILES+=("$filename")
done < <(find "$PROJECT_ROOT/airflow_dags" -maxdepth 1 -name "*.py" -type f -print0 | sort -z)

if [ ${#DAG_FILES[@]} -eq 0 ]; then
    echo -e "${RED}❌ No Python files found in $PROJECT_ROOT/airflow_dags/${NC}"
    exit 1
fi

echo "Found ${#DAG_FILES[@]} files:"
for file in "${DAG_FILES[@]}"; do
    echo "   - $file"
done
echo ""

# Sync each file
echo -e "${BLUE}📁 Syncing files...${NC}"
for file in "${DAG_FILES[@]}"; do
    SOURCE="$PROJECT_ROOT/airflow_dags/$file"
    DEST="$AIRFLOW_DAGS/$file"

    if [ "$dry_run" = true ]; then
        [ "$symlink_mode" = true ] && echo -e "${GREEN}Would symlink:${NC} $file" || echo -e "${GREEN}Would copy:${NC} $file"
    else
        # Remove existing
        [ -e "$DEST" ] || [ -L "$DEST" ] && rm "$DEST" 2>/dev/null || true

        if [ "$symlink_mode" = true ]; then
            ln -s "$SOURCE" "$DEST"
            echo -e "${GREEN}✓ Symlinked:${NC} $file"
        else
            cp "$SOURCE" "$DEST"
            echo -e "${GREEN}✓ Copied:${NC} $file"
        fi
    fi
done
echo ""

# Clean up removed DAGs
if [ "$cleanup_stale" = true ] && [ "$dry_run" = false ]; then
    echo -e "${BLUE}🧹 Cleaning up stale DAGs...${NC}"

    for dest_file in "$AIRFLOW_DAGS"/*.py; do
        if [ -f "$dest_file" ]; then
            filename=$(basename "$dest_file")
            if [ ! -f "$PROJECT_ROOT/airflow_dags/$filename" ]; then
                rm "$dest_file"
                echo -e "${YELLOW}🗑️  Removed: $filename${NC}"
            fi
        fi
    done
    echo ""
fi

# Validate DAGs
if [ "$dry_run" = false ]; then
    echo -e "${BLUE}🔍 Validating DAG files...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    validate_dag() {
        local dag_file=$1
        local dag_path="$AIRFLOW_DAGS/$dag_file"

        echo ""
        echo "Validating: $dag_file"

        # Syntax check
        if ! $VENV_PYTHON -m py_compile "$dag_path" 2>&1; then
            echo -e "${RED}❌ Syntax error in $dag_file${NC}"
            return 1
        fi
        echo "  ✓ Syntax OK"

        # Import check
        cd "$AIRFLOW_DAGS"
        if ! $VENV_PYTHON -c "
import sys
sys.path.insert(0, '$AIRFLOW_DAGS')
try:
    import ${dag_file%.py}
    print('  ✓ Import OK')
except Exception as e:
    print(f'  ✗ Import failed: {e}')
    sys.exit(1)
" 2>&1; then
            echo -e "${RED}❌ Import error in $dag_file${NC}"
            cd - > /dev/null
            return 1
        fi
        cd - > /dev/null

        echo "  ✓ DAG validation passed"
        return 0
    }

    VALIDATION_FAILED=0
    for file in "${DAG_FILES[@]}"; do
        if ! validate_dag "$file"; then
            VALIDATION_FAILED=1
        fi
    done

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ $VALIDATION_FAILED -eq 1 ]; then
        echo -e "${RED}❌ Validation failed for one or more DAGs${NC}"
        exit 1
    fi
fi

# Detect and clean stale metadata
if [ "$cleanup_stale" = true ] && [ "$dry_run" = false ]; then
    echo ""
    echo -e "${BLUE}🔍 Detecting stale DAG metadata...${NC}"

    $VENV_PYTHON << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/rmondo/repos/air-executor/airflow_dags')

from airflow import settings
from airflow.models import DagModel, DagRun, TaskInstance, Log
from pathlib import Path

session = settings.Session()
try:
    # Get all DAGs in database
    db_dags = session.query(DagModel).all()

    # Get all Python files in airflow_dags
    dag_files = set()
    dags_dir = Path('/home/rmondo/repos/air-executor/airflow_dags')
    for py_file in dags_dir.glob('*.py'):
        dag_files.add(py_file.stem)

    # Find stale DAGs (in DB but not in files or defining DAGs)
    stale_dags = []
    for dag in db_dags:
        fileloc = Path(dag.fileloc)

        # Check if the file still exists
        if not fileloc.exists():
            stale_dags.append(dag.dag_id)
            continue

        # Check if file still defines this DAG
        try:
            with open(fileloc) as f:
                content = f.read()
                if f"'{dag.dag_id}'" not in content and f'"{dag.dag_id}"' not in content:
                    stale_dags.append(dag.dag_id)
        except:
            pass

    if stale_dags:
        print(f"Found {len(stale_dags)} stale DAG(s): {', '.join(stale_dags)}")
        print("Cleaning up...")

        for dag_id in stale_dags:
            # Delete in order
            ti_count = session.query(TaskInstance).filter(TaskInstance.dag_id == dag_id).delete()
            dr_count = session.query(DagRun).filter(DagRun.dag_id == dag_id).delete()
            try:
                log_count = session.query(Log).filter(Log.dag_id == dag_id).delete()
            except:
                log_count = 0
            dag_count = session.query(DagModel).filter(DagModel.dag_id == dag_id).delete()

            print(f"  ✓ Deleted {dag_id}: {dag_count} DAG, {dr_count} runs, {ti_count} tasks, {log_count} logs")

        session.commit()
        print(f"✅ Cleaned up {len(stale_dags)} stale DAG(s)")
    else:
        print("✓ No stale DAGs found")

finally:
    session.close()
PYTHON_SCRIPT
fi

# Auto-unpause DAGs
if [ "$auto_unpause" = true ] && [ "$dry_run" = false ]; then
    echo ""
    echo -e "${BLUE}🔓 Auto-unpausing DAGs...${NC}"

    $VENV_PYTHON << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/rmondo/repos/air-executor/airflow_dags')

from airflow import settings
from airflow.models import DagModel

session = settings.Session()
try:
    paused_dags = session.query(DagModel).filter(DagModel.is_paused == True).all()

    if paused_dags:
        print(f"Found {len(paused_dags)} paused DAG(s)")
        for dag in paused_dags:
            dag.is_paused = False
            print(f"  ✓ Unpaused: {dag.dag_id}")

        session.commit()
        print(f"✅ Unpaused {len(paused_dags)} DAG(s)")
    else:
        print("✓ All DAGs already active")

finally:
    session.close()
PYTHON_SCRIPT
fi

# Final status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$dry_run" = true ]; then
    echo -e "${BLUE}Dry-run complete. Use without --dry-run to apply.${NC}"
else
    echo -e "${GREEN}✅ Sync complete!${NC}"
    echo ""
    echo "💡 To trigger DAGs:"
    echo "   airflow dags trigger python_cleanup"
    echo "   airflow dags trigger commit_and_push"
    echo ""
    echo "📊 Check status: airflow dags list | grep -E '(python_cleanup|commit_and_push)'"
fi
