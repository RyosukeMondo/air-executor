.PHONY: help install install-dev test lint format clean setup-tools check-tools
.PHONY: start start-all start-project stop status logs clean-logs

# Development Commands
help:
	@echo "Development Commands:"
	@echo "  install      - Install package and dependencies"
	@echo "  install-dev  - Install package with dev dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linting (ruff, mypy)"
	@echo "  format       - Format code (black, isort)"
	@echo "  clean        - Remove build artifacts"
	@echo ""
	@echo "Tool Setup Commands:"
	@echo "  setup-tools  - Install all language tools (Python, JS, Go, Flutter)"
	@echo "  check-tools  - Verify all tools are installed correctly"
	@echo ""
	@echo "Autonomous Fixing Commands:"
	@echo "  start-all    - Start all projects with PM2"
	@echo "  start PROJECT=<name> - Start specific project (e.g., make start PROJECT=air-executor)"
	@echo "  stop         - Stop all PM2 processes"
	@echo "  status       - Show PM2 process status"
	@echo "  logs         - Follow all PM2 logs"
	@echo "  clean-logs   - Remove all log files"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/

# Tool Setup
setup-tools:
	./scripts/setup_python.sh
	./scripts/setup_javascript.sh
	./scripts/setup_go.sh
	./scripts/setup_flutter.sh

check-tools:
	./scripts/check_tools.sh

# Autonomous Fixing
start-all:
	pm2 start config/pm2.config.js

start:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Error: PROJECT variable required. Usage: make start PROJECT=air-executor"; \
		exit 1; \
	fi
	pm2 start config/pm2.config.js --only fix-$(PROJECT)

stop:
	pm2 stop all

status:
	pm2 status

logs:
	pm2 logs

clean-logs:
	rm -rf logs/*.log logs/debug/*.jsonl
