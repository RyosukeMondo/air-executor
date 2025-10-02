#!/bin/bash
#
# Run Multi-Language Orchestrator on Real Projects
#
# Projects:
# - /home/rmondo/repos/air-executor (Python)
# - /home/rmondo/repos/cc-task-manager (JavaScript)
# - /home/rmondo/repos/mind-training (JavaScript)
# - /home/rmondo/repos/money-making-app (Flutter)
# - /home/rmondo/repos/warps (JavaScript)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
CONFIG_FILE="${PROJECT_ROOT}/config/real_projects_fix.yaml"
VENV_PYTHON="$HOME/.venv/air-executor/bin/python"
ORCHESTRATOR="${PROJECT_ROOT}/airflow_dags/autonomous_fixing/multi_language_orchestrator.py"

echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}🚀 Real Projects Multi-Language Autonomous Fixing${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${BLUE}📋 Step 1: Checking Prerequisites${NC}"
echo ""

# Check Python venv
if [ ! -f "${VENV_PYTHON}" ]; then
    echo -e "${RED}❌ Python venv not found: ${VENV_PYTHON}${NC}"
    echo -e "${YELLOW}   Please create venv:${NC}"
    echo -e "   python -m venv ~/.venv/air-executor"
    echo -e "   source ~/.venv/air-executor/bin/activate"
    echo -e "   pip install redis pyyaml pytest pylint mypy"
    exit 1
fi
echo -e "${GREEN}✓ Python venv found${NC}"

# Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Redis is not running${NC}"
    echo -e "${YELLOW}   Start Redis: redis-server &${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"

# Check Claude CLI
if ! which claude > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Claude CLI not found in PATH${NC}"
    echo -e "${YELLOW}   This is OK if using subscription-based auth${NC}"
else
    echo -e "${GREEN}✓ Claude CLI found${NC}"
fi

# Check projects exist
echo ""
echo -e "${BLUE}📦 Step 2: Checking Projects${NC}"
echo ""

PROJECTS=(
    "/home/rmondo/repos/air-executor:Python"
    "/home/rmondo/repos/cc-task-manager:JavaScript"
    "/home/rmondo/repos/mind-training:JavaScript"
    "/home/rmondo/repos/money-making-app:Flutter"
    "/home/rmondo/repos/warps:JavaScript"
)

ALL_EXIST=true
for project_info in "${PROJECTS[@]}"; do
    IFS=':' read -r project_path project_lang <<< "$project_info"
    if [ -d "${project_path}" ]; then
        echo -e "${GREEN}✓ ${project_lang}: ${project_path}${NC}"
    else
        echo -e "${RED}❌ ${project_lang}: ${project_path} NOT FOUND${NC}"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo ""
    echo -e "${RED}❌ Some projects not found. Please check paths.${NC}"
    exit 1
fi

# Step 3: Check git status
echo ""
echo -e "${BLUE}📝 Step 3: Checking Git Status${NC}"
echo ""

HAS_UNCOMMITTED=false
for project_info in "${PROJECTS[@]}"; do
    IFS=':' read -r project_path project_lang <<< "$project_info"
    cd "${project_path}"

    if [ -d .git ]; then
        # Check for uncommitted changes
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            echo -e "${YELLOW}⚠️  ${project_lang} (${project_path##*/}): Has uncommitted changes${NC}"
            HAS_UNCOMMITTED=true
        else
            echo -e "${GREEN}✓ ${project_lang} (${project_path##*/}): Clean working directory${NC}"
        fi

        # Show current branch
        BRANCH=$(git branch --show-current)
        echo -e "   Branch: ${BRANCH}"
    else
        echo -e "${YELLOW}⚠️  ${project_lang} (${project_path##*/}): Not a git repository${NC}"
    fi
    echo ""
done

if [ "$HAS_UNCOMMITTED" = true ]; then
    echo -e "${YELLOW}⚠️  Some projects have uncommitted changes.${NC}"
    echo -e "${YELLOW}   The orchestrator will create commits on top of current state.${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Aborted by user${NC}"
        exit 1
    fi
fi

# Step 4: Test run (dry run on one project)
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}🧪 Step 4: Test Run (Checking Configuration)${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Add venv to PATH
VENV_BIN="$(dirname "${VENV_PYTHON}")"
export PATH="${VENV_BIN}:${PATH}"

echo -e "${YELLOW}Testing orchestrator with real config...${NC}"
echo ""

# Run orchestrator
"${VENV_PYTHON}" "${ORCHESTRATOR}" "${CONFIG_FILE}" || {
    EXIT_CODE=$?
    echo ""
    echo -e "${YELLOW}📊 Test run completed with exit code: ${EXIT_CODE}${NC}"
    echo -e "${YELLOW}   This is normal if priority gates are not met${NC}"
    echo ""
}

# Step 5: Show results summary
echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}📊 Step 5: Results Summary${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

echo -e "${YELLOW}Check git logs in each project:${NC}"
echo ""

for project_info in "${PROJECTS[@]}"; do
    IFS=':' read -r project_path project_lang <<< "$project_info"
    cd "${project_path}"

    if [ -d .git ]; then
        echo -e "${BLUE}=== ${project_lang}: ${project_path##*/} ===${NC}"

        # Show recent commits
        echo -e "   ${GREEN}Recent commits:${NC}"
        git log --oneline -3 | sed 's/^/     /'

        # Check for new commits from orchestrator
        NEW_COMMITS=$(git log --since="5 minutes ago" --oneline | wc -l)
        if [ "$NEW_COMMITS" -gt 0 ]; then
            echo -e "   ${GREEN}✓ ${NEW_COMMITS} new commit(s) from orchestrator${NC}"
        fi

        echo ""
    fi
done

# Step 6: Next steps
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}✅ Orchestrator Run Complete${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo -e "  ${BLUE}1. Review commits in each project:${NC}"
echo -e "     cd /home/rmondo/repos/air-executor && git log -p -1"
echo -e "     cd /home/rmondo/repos/money-making-app && git log -p -1"
echo ""
echo -e "  ${BLUE}2. Run with PM2 for automation:${NC}"
echo -e "     pm2 start ecosystem.real-projects.config.js"
echo -e "     pm2 logs real-projects-fixing"
echo ""
echo -e "  ${BLUE}3. Run multiple iterations:${NC}"
echo -e "     # The config has max_iterations: 5"
echo -e "     # It will run 5 times then stop"
echo ""
echo -e "  ${BLUE}4. Monitor progress:${NC}"
echo -e "     tail -f logs/real-projects-out.log"
echo ""
echo -e "  ${BLUE}5. Push changes when ready:${NC}"
echo -e "     cd /home/rmondo/repos/air-executor && git push"
echo ""
echo -e "${GREEN}Happy fixing! 🎉${NC}"
echo ""
