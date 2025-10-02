#!/bin/bash
#
# Multi-Language Test Runner
#
# This script:
# 1. Creates a clean tmp directory
# 2. Copies sample projects (with bugs)
# 3. Initializes git repositories
# 4. Runs the multi-language orchestrator
# 5. Shows commits and results
#
# Can be run multiple times - each run starts fresh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="${SCRIPT_DIR}/tmp_test_run_$(date +%Y%m%d_%H%M%S)"
ORCHESTRATOR_SCRIPT="${SCRIPT_DIR}/../airflow_dags/autonomous_fixing/multi_language_orchestrator.py"
CONFIG_TEMPLATE="${SCRIPT_DIR}/../config/multi_language_fix.yaml"
VENV_PYTHON="$HOME/.venv/air-executor/bin/python"

echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}🧪 Multi-Language Autonomous Fixing - Test Runner${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""
echo -e "Test directory: ${YELLOW}${TMP_DIR}${NC}"
echo -e "Source samples: ${YELLOW}${SCRIPT_DIR}${NC}"
echo ""

# Step 1: Create tmp directory
echo -e "${BLUE}📁 Step 1: Creating temporary test directory...${NC}"
mkdir -p "${TMP_DIR}"
echo -e "${GREEN}✓ Created: ${TMP_DIR}${NC}"
echo ""

# Step 2: Copy sample projects
echo -e "${BLUE}📦 Step 2: Copying sample projects...${NC}"

# Copy Python project
if [ -d "${SCRIPT_DIR}/sample_python_project" ]; then
    echo -e "   Copying Python project..."
    cp -r "${SCRIPT_DIR}/sample_python_project" "${TMP_DIR}/sample_python_project"
    echo -e "${GREEN}   ✓ Python project copied${NC}"
fi

# Copy JavaScript project
if [ -d "${SCRIPT_DIR}/sample_javascript_project" ]; then
    echo -e "   Copying JavaScript/TypeScript project..."
    cp -r "${SCRIPT_DIR}/sample_javascript_project" "${TMP_DIR}/sample_javascript_project"
    echo -e "${GREEN}   ✓ JavaScript/TypeScript project copied${NC}"
fi

# Copy Go project
if [ -d "${SCRIPT_DIR}/sample_go_project" ]; then
    echo -e "   Copying Go project..."
    cp -r "${SCRIPT_DIR}/sample_go_project" "${TMP_DIR}/sample_go_project"
    echo -e "${GREEN}   ✓ Go project copied${NC}"
fi

echo ""

# Step 3: Initialize git repositories
echo -e "${BLUE}📝 Step 3: Initializing git repositories...${NC}"

init_git_repo() {
    local project_dir=$1
    local project_name=$2

    if [ -d "${project_dir}" ]; then
        echo -e "   Initializing git in ${project_name}..."
        cd "${project_dir}"

        # Initialize git
        git init -q

        # Configure git
        git config user.name "Test User"
        git config user.email "test@example.com"

        # Create .gitignore
        cat > .gitignore <<EOF
# Dependencies
node_modules/
__pycache__/
*.pyc
.pytest_cache/
coverage/
dist/
build/

# OS files
.DS_Store
*.swp
*.swo
EOF

        # Initial commit
        git add .
        git commit -q -m "Initial commit: ${project_name} with intentional bugs

This is the baseline with:
- Static analysis errors
- Failing tests
- Missing test coverage
- High complexity code

Ready for autonomous fixing test."

        echo -e "${GREEN}   ✓ Git initialized for ${project_name}${NC}"
        echo -e "     Commit: $(git rev-parse --short HEAD) - Initial commit"

        cd - > /dev/null
    fi
}

init_git_repo "${TMP_DIR}/sample_python_project" "Python"
init_git_repo "${TMP_DIR}/sample_javascript_project" "JavaScript/TypeScript"
init_git_repo "${TMP_DIR}/sample_go_project" "Go"

echo ""

# Step 4: Create test config
echo -e "${BLUE}⚙️  Step 4: Creating test configuration...${NC}"

TEST_CONFIG="${TMP_DIR}/test_config.yaml"

cat > "${TEST_CONFIG}" <<EOF
# Multi-Language Test Configuration
# Generated for test run: $(date)

target_project: "${TMP_DIR}"

languages:
  enabled:
    - python
    - javascript
    - go

  auto_detect: true

  python:
    linters: ["pylint", "mypy"]
    test_framework: "pytest"
    complexity_threshold: 10
    max_file_lines: 500

  javascript:
    linters: ["eslint"]
    type_checker: "tsc"
    test_framework: "jest"
    complexity_threshold: 10
    max_file_lines: 500

  go:
    linters: ["go vet", "staticcheck"]
    test_timeout: 300
    complexity_threshold: 10
    max_file_lines: 500

priorities:
  p1_static:
    enabled: true
    max_duration_seconds: 120
    success_threshold: 0.90

  p2_tests:
    enabled: true
    adaptive_strategy: true
    time_budgets:
      minimal: 300
      selective: 900
      comprehensive: 1800
    success_threshold: 0.85

  p3_coverage:
    enabled: true
    gate_requirements:
      p1_score: 0.90
      p2_score: 0.85
    max_duration_seconds: 3600
    target_coverage: 0.80

  p4_e2e:
    enabled: false  # Disabled for quick testing
    gate_requirements:
      overall_health: 0.90

execution:
  parallel_languages: true
  max_concurrent_projects: 3
  fail_fast: false
  priority_gates: true

wrapper:
  path: "${SCRIPT_DIR}/../scripts/claude_wrapper.py"
  python_executable: "${VENV_PYTHON}"
  timeout: 900

state_manager:
  redis_host: "localhost"
  redis_port: 6379
  namespace: "ml_test"

git:
  auto_commit: true
  commit_prefix: "fix"
  push_after_commit: false
EOF

echo -e "${GREEN}✓ Test config created: ${TEST_CONFIG}${NC}"
echo ""

# Step 5: Show project status
echo -e "${BLUE}📊 Step 5: Project Status (Before Fixing)${NC}"
echo ""

show_project_status() {
    local project_dir=$1
    local project_name=$2

    if [ -d "${project_dir}" ]; then
        echo -e "${YELLOW}=== ${project_name} ===${NC}"
        cd "${project_dir}"

        # Show git status
        echo -e "   Git status:"
        git log --oneline -1 | sed 's/^/     /'

        # Count files
        local file_count=$(find . -type f -not -path './.git/*' -not -path './node_modules/*' -not -path './__pycache__/*' | wc -l)
        echo -e "   Files: ${file_count}"

        cd - > /dev/null
        echo ""
    fi
}

show_project_status "${TMP_DIR}/sample_python_project" "Python"
show_project_status "${TMP_DIR}/sample_javascript_project" "JavaScript/TypeScript"
show_project_status "${TMP_DIR}/sample_go_project" "Go"

# Step 6: Run orchestrator
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}🚀 Step 6: Running Multi-Language Orchestrator${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Check if orchestrator exists
if [ ! -f "${ORCHESTRATOR_SCRIPT}" ]; then
    echo -e "${RED}❌ Orchestrator script not found: ${ORCHESTRATOR_SCRIPT}${NC}"
    exit 1
fi

# Check if Python venv exists
if [ ! -f "${VENV_PYTHON}" ]; then
    echo -e "${RED}❌ Python venv not found: ${VENV_PYTHON}${NC}"
    echo -e "${YELLOW}   Please create venv first:${NC}"
    echo -e "   python -m venv ~/.venv/air-executor"
    echo -e "   source ~/.venv/air-executor/bin/activate"
    echo -e "   pip install redis pyyaml"
    exit 1
fi

# Run orchestrator
echo -e "${YELLOW}Running orchestrator (this may take a few minutes)...${NC}"
echo ""

# Add venv to PATH so language adapters can find tools (pytest, etc.)
VENV_BIN="$(dirname "${VENV_PYTHON}")"
export PATH="${VENV_BIN}:${PATH}"

"${VENV_PYTHON}" "${ORCHESTRATOR_SCRIPT}" "${TEST_CONFIG}" || {
    echo ""
    echo -e "${RED}❌ Orchestrator failed${NC}"
    echo -e "${YELLOW}💡 This is expected if projects have intentional issues below thresholds${NC}"
    echo ""
}

# Step 7: Show results
echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}📊 Step 7: Results Summary${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

show_project_results() {
    local project_dir=$1
    local project_name=$2

    if [ -d "${project_dir}" ]; then
        echo -e "${YELLOW}=== ${project_name} ===${NC}"
        cd "${project_dir}"

        # Show all commits
        echo -e "   ${BLUE}Git History:${NC}"
        git log --oneline --decorate | sed 's/^/     /'

        # Show changed files in latest commit (if not initial)
        local commit_count=$(git rev-list --count HEAD)
        if [ "$commit_count" -gt 1 ]; then
            echo ""
            echo -e "   ${BLUE}Latest Changes:${NC}"
            git diff HEAD~1 HEAD --stat | sed 's/^/     /'
        fi

        cd - > /dev/null
        echo ""
    fi
}

show_project_results "${TMP_DIR}/sample_python_project" "Python"
show_project_results "${TMP_DIR}/sample_javascript_project" "JavaScript/TypeScript"
show_project_results "${TMP_DIR}/sample_go_project" "Go"

# Step 8: Provide next steps
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}✅ Test Run Complete${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""
echo -e "${GREEN}Test directory: ${TMP_DIR}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo -e "  ${BLUE}1. Inspect commits:${NC}"
echo -e "     cd ${TMP_DIR}/sample_python_project"
echo -e "     git log -p"
echo ""
echo -e "  ${BLUE}2. View changes:${NC}"
echo -e "     cd ${TMP_DIR}/sample_python_project"
echo -e "     git show HEAD"
echo ""
echo -e "  ${BLUE}3. Check diffs:${NC}"
echo -e "     cd ${TMP_DIR}/sample_python_project"
echo -e "     git diff HEAD~1 HEAD"
echo ""
echo -e "  ${BLUE}4. Run tests manually:${NC}"
echo -e "     cd ${TMP_DIR}/sample_python_project"
echo -e "     pytest"
echo ""
echo -e "  ${BLUE}5. Clean up when done:${NC}"
echo -e "     rm -rf ${TMP_DIR}"
echo ""
echo -e "  ${BLUE}6. Run another test:${NC}"
echo -e "     ${SCRIPT_DIR}/run_multi_language_test.sh"
echo ""
echo -e "${GREEN}Happy testing! 🎉${NC}"
echo ""
