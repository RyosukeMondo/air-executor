.PHONY: help install install-dev test lint format clean run

help:
	@echo "Available targets:"
	@echo "  install      - Install package and dependencies"
	@echo "  install-dev  - Install package with dev dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linting (ruff, mypy)"
	@echo "  format       - Format code (black, isort)"
	@echo "  clean        - Remove build artifacts"
	@echo "  run          - Start job manager in foreground"

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

run:
	@echo "Starting job manager in foreground (Ctrl+C to stop)..."
	@python -m air_executor.cli.main start
