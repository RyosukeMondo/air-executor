#!/bin/bash
# coverage-check.sh - Complete coverage analysis workflow

set -e

echo "🧪 Running Unit Tests with Coverage..."
.venv/bin/python3 -m pytest tests/unit/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-unit \
  --cov-report=term-missing

echo ""
echo "🔗 Running Integration Tests with Coverage..."
.venv/bin/python3 -m pytest tests/integration/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-integration \
  --cov-report=term-missing

echo ""
echo "🚀 Running E2E Tests with Coverage..."
.venv/bin/python3 -m pytest tests/e2e/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-e2e \
  --cov-report=term-missing

echo ""
echo "📊 Running ALL Tests with Combined Coverage..."
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80

echo ""
echo "✅ Coverage reports generated:"
echo "   Unit:        htmlcov-unit/index.html"
echo "   Integration: htmlcov-integration/index.html"
echo "   E2E:         htmlcov-e2e/index.html"
echo "   Combined:    htmlcov/index.html"
echo ""
echo "Open with: open htmlcov/index.html (macOS) or xdg-open htmlcov/index.html (Linux)"
