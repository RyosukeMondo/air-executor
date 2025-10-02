#!/bin/bash
# Sync DAG files from git repo to Airflow dags folder

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIRFLOW_DAGS_DIR="${HOME}/airflow/dags"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Sync DAG files to Airflow dags folder"
    echo ""
    echo "Options:"
    echo "  --symlink    Create symlinks instead of copying (recommended for dev)"
    echo "  --copy       Copy files (default, safe for all environments)"
    echo "  --dry-run    Show what would be done without doing it"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Copy DAG files to Airflow"
    echo "  $0 --symlink        # Create symlinks (changes auto-sync)"
    echo "  $0 --dry-run        # See what would be copied"
}

symlink_mode=false
dry_run=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --symlink)
            symlink_mode=true
            shift
            ;;
        --copy)
            symlink_mode=false
            shift
            ;;
        --dry-run)
            dry_run=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check if Airflow dags directory exists
if [ ! -d "$AIRFLOW_DAGS_DIR" ]; then
    echo -e "${YELLOW}Warning: Airflow dags directory not found: $AIRFLOW_DAGS_DIR${NC}"
    echo "Please ensure Airflow is installed and initialized."
    exit 1
fi

echo -e "${BLUE}📁 Airflow DAGs Sync${NC}"
echo "Source: $SCRIPT_DIR"
echo "Target: $AIRFLOW_DAGS_DIR"
echo ""

# Find all Python DAG files (exclude README, scripts, etc.)
dag_files=$(find "$SCRIPT_DIR" -maxdepth 1 -name "*.py" -type f)

if [ -z "$dag_files" ]; then
    echo -e "${YELLOW}No DAG files found in $SCRIPT_DIR${NC}"
    exit 0
fi

if [ "$symlink_mode" = true ]; then
    echo -e "${BLUE}Mode: Symlink (changes will auto-sync)${NC}"
else
    echo -e "${BLUE}Mode: Copy${NC}"
fi

if [ "$dry_run" = true ]; then
    echo -e "${YELLOW}Dry-run mode (no changes will be made)${NC}"
fi

echo ""

# Sync each DAG file
for dag_file in $dag_files; do
    filename=$(basename "$dag_file")
    target="$AIRFLOW_DAGS_DIR/$filename"

    if [ "$dry_run" = true ]; then
        if [ "$symlink_mode" = true ]; then
            echo -e "${GREEN}Would symlink:${NC} $filename"
        else
            echo -e "${GREEN}Would copy:${NC} $filename"
        fi
    else
        # Remove existing file/symlink
        if [ -e "$target" ] || [ -L "$target" ]; then
            rm "$target"
        fi

        if [ "$symlink_mode" = true ]; then
            ln -s "$dag_file" "$target"
            echo -e "${GREEN}✓ Symlinked:${NC} $filename"
        else
            cp "$dag_file" "$target"
            echo -e "${GREEN}✓ Copied:${NC} $filename"
        fi
    fi
done

echo ""

if [ "$dry_run" = false ]; then
    echo -e "${GREEN}✅ Sync complete!${NC}"
    echo ""
    echo "DAGs will appear in Airflow UI within ~30 seconds"
    echo "Access Airflow: http://localhost:8080"
else
    echo -e "${BLUE}Dry-run complete. Use without --dry-run to apply changes.${NC}"
fi
