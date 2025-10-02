#!/bin/bash
# Pre-flight check for Airflow E2E test

echo "🔍 Airflow E2E Pre-flight Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 1: Config file
echo ""
echo "1️⃣ Checking config file..."
if [ -f "config/air-executor.toml" ]; then
    echo "   ✅ config/air-executor.toml exists"
else
    echo "   ❌ config/air-executor.toml missing"
    echo "      Run: cp config/air-executor.example.toml config/air-executor.toml"
fi

# Check 2: Config loads
echo ""
echo "2️⃣ Checking config loads..."
source .venv/bin/activate 2>/dev/null
if python -c "from air_executor.config import load_config; load_config()" 2>/dev/null; then
    echo "   ✅ Config loads successfully"
else
    echo "   ❌ Config fails to load"
fi

# Check 3: claude_code_sdk installed
echo ""
echo "3️⃣ Checking claude_code_sdk..."
if python -c "import claude_code_sdk" 2>/dev/null; then
    echo "   ✅ claude_code_sdk installed"
else
    echo "   ❌ claude_code_sdk not installed"
    echo "      Run: pip install claude-code-sdk"
fi

# Check 4: Wrapper exists
echo ""
echo "4️⃣ Checking claude_wrapper.py..."
if [ -f "scripts/claude_wrapper.py" ]; then
    echo "   ✅ scripts/claude_wrapper.py exists"
    if [ -x "scripts/claude_wrapper.py" ]; then
        echo "   ✅ claude_wrapper.py is executable"
    else
        echo "   ⚠️  claude_wrapper.py not executable"
        echo "      Run: chmod +x scripts/claude_wrapper.py"
    fi
else
    echo "   ❌ scripts/claude_wrapper.py missing"
fi

# Check 5: DAG in Airflow
echo ""
echo "5️⃣ Checking DAG registration..."
if airflow dags list 2>/dev/null | grep -q "claude_query_sdk"; then
    echo "   ✅ claude_query_sdk registered in Airflow"
    
    # Check if paused
    if airflow dags list 2>/dev/null | grep "claude_query_sdk" | grep -q "False"; then
        echo "   ✅ claude_query_sdk is unpaused (ready to run)"
    else
        echo "   ⚠️  claude_query_sdk is paused"
        echo "      Run: airflow dags unpause claude_query_sdk"
    fi
else
    echo "   ❌ claude_query_sdk not found in Airflow"
    echo "      Run: ./airflow_dags/sync_to_airflow.sh"
fi

# Check 6: Airflow scheduler
echo ""
echo "6️⃣ Checking Airflow scheduler..."
if ps aux | grep -v grep | grep -q "airflow scheduler"; then
    echo "   ✅ Airflow scheduler is running"
else
    echo "   ❌ Airflow scheduler not running"
    echo "      Run: airflow scheduler (or ./scripts/start-airflow.sh)"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Next Steps:"
echo "   1. Fix any ❌ issues above"
echo "   2. Open http://localhost:8080"
echo "   3. Find 'claude_query_sdk' DAG"
echo "   4. Click ▶️ Play button"
echo "   5. Check logs for Claude's response"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
