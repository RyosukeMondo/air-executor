# Wrapper Monitoring Scripts

Simple guide to monitoring Claude wrapper execution in real-time.

## Quick Start

```bash
# Terminal 1: Start the monitor
./scripts/monitor.sh

# Terminal 2: Run your task
./scripts/autonomous_fix.sh config/projects/warps.yaml
```

That's it! Watch the events stream in Terminal 1.

## What Each Script Does

| Script | Purpose | How to Use |
|--------|---------|------------|
| **monitor.sh** | ✅ **USE THIS** - Main monitoring script | `./scripts/monitor.sh` |
| watch_wrapper.py | Dashboard implementation (called by monitor.sh) | Don't run directly |
| test_monitor.sh | Test if monitoring works | `./scripts/test_monitor.sh` |
| demo_wrapper_output.py | Generate test events | For development only |

## Troubleshooting

### "No events yet..."
This is normal! Events only appear when Claude wrapper is actually called (during analysis/fixing, not setup).

### Tried to run watch_wrapper.py?
Don't! Use `./scripts/monitor.sh` instead.

### Monitor not updating?
1. Check if autonomous_fix.sh is running in Terminal 2
2. Verify `logs/wrapper-realtime.log` exists and has content: `tail logs/wrapper-realtime.log`
3. Run diagnostics: `./scripts/test_monitor.sh`

## Advanced Usage

If you want to pipe events from another source:
```bash
# From another log file
tail -F other-log.json | python scripts/watch_wrapper.py

# From a running process
python scripts/claude_wrapper.py | python scripts/watch_wrapper.py
```

## More Info

See [WRAPPER_MONITOR.md](../docs/WRAPPER_MONITOR.md) for detailed documentation.
