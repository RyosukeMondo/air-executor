# Autonomous Fixing - Quick Start

## One-Command Usage

### For money-making-app Flutter project:

```bash
./scripts/autonomous_fix.sh config/money-making-app.yaml
```

That's it! The script will:
- ✓ Start Redis automatically
- ✓ Detect Python environment
- ✓ Validate all tools
- ✓ Run autonomous fixing

## What Gets Fixed

The system will automatically:
1. **Analyze** your project (lint, tests, coverage)
2. **Identify** issues and prioritize them
3. **Fix** issues systematically
4. **Verify** fixes work
5. **Commit** changes (if enabled)
6. **Iterate** until health threshold met

## Configuration

Edit `config/money-making-app.yaml` to customize:

```yaml
# What to fix
priorities:
  p1_static: {enabled: true}   # Lint/analysis errors
  p2_tests: {enabled: true}    # Test failures
  p3_coverage: {enabled: true} # Coverage gaps
  p4_e2e: {enabled: false}     # E2E tests

# How many iterations
execution:
  max_iterations: 3

# Safety
git:
  auto_commit: true  # Set false to review changes first
```

## Monitoring

```bash
# Watch progress
tail -f logs/orchestrator_run.log

# Check Redis state
redis-cli keys "money_making_app:*"
```

## Prerequisites

- Redis running (script auto-starts)
- Python 3.8+ with venv
- Flutter SDK (for Flutter projects)

Install missing tools:
```bash
./scripts/install_redis.sh    # Install Redis
./scripts/install_flutter.sh  # Install Flutter
```

## Full Guide

See [AUTONOMOUS_FIXING_GUIDE.md](./AUTONOMOUS_FIXING_GUIDE.md) for complete documentation.
