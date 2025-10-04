# Claude Wrapper Real-Time Monitor

Real-time terminal dashboard for `claude_wrapper.py` execution state and progress.

## Features

- **Live State Tracking**: See current execution state (ready, executing, completed, failed)
- **Phase Detection**: Automatically detects execution phase (P1-P4)
- **Tool Progress**: Track tool execution (Read, Bash, Edit, etc.) with progress counters
- **Event Stream**: Recent events with timestamps and icons
- **Runtime Metrics**: Execution time, tools completed, errors

## Quick Start

### Prerequisites

```bash
# Ensure rich library is installed
pip install rich
```

### For Autonomous Fixing (Recommended)

**Terminal 1** (start monitoring):
```bash
./scripts/monitor_wrapper.sh
```

**Terminal 2** (run execution):
```bash
./scripts/autonomous_fix.sh config/projects/warps.yaml
```

The monitor will automatically track all wrapper executions in real-time.

### For Direct Wrapper Usage

Pipe wrapper output directly to the monitor:

```bash
.venv/bin/python3 scripts/claude_wrapper.py | .venv/bin/python3 scripts/watch_wrapper.py
```

#### 2. Monitor Wrapper Logs

Watch existing log files in real-time:

```bash
tail -f logs/wrapper-*.log | .venv/bin/python3 scripts/watch_wrapper.py
```

#### 3. Demo Mode

Test the monitor with simulated output:

```bash
.venv/bin/python3 scripts/demo_wrapper_output.py | .venv/bin/python3 scripts/watch_wrapper.py
```

## Dashboard Layout

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          🤖 Claude Wrapper Monitor          ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃        State: EXECUTING                     ┃
┃        Phase: P1: Test Discovery            ┃
┃      Runtime: 1m 23s                        ┃
┃ Current Tool: 🔧 Bash                       ┃
┃     Progress: 4/6 tools                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              📋 Recent Events               ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 16:42:15  🚀 Wrapper ready                  ┃
┃ 16:42:16  ▶️  Run started                   ┃
┃ 16:42:17  📊 Phase: P1: Test Discovery      ┃
┃ 16:42:18  🔧 Tool: Read                     ┃
┃ 16:42:19  ✅ Done: Read                     ┃
┃ 16:42:20  🔧 Tool: Bash                     ┃
┃ 16:42:21  💬 Text: Analyzing tests...       ┃
┃ 16:42:22  ✅ Done: Bash                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Event Types

The monitor recognizes these wrapper events:

### State Events
- `ready` 🚀 - Wrapper initialized
- `run_started` ▶️ - Execution started
- `run_completed` 🎉 - Completed successfully
- `run_failed` ❌ - Execution failed
- `run_cancelled` ⏹️ - Cancelled by user
- `shutdown` 🛑 - Wrapper shutdown

### Execution Events
- `phase_detected` 📊 - Phase identified (P1-P4)
- `tool_started` 🔧 - Tool execution started
- `tool_completed` ✅ - Tool execution finished
- `stream` 💬 - Claude response stream
- `error` ⚠️ - Error occurred

### Phase Detection

The monitor automatically detects execution phases from prompt content:

- **P1: Test Discovery** - Test configuration discovery
- **P1: Static Analysis** - Linting, type checking
- **P2: Test Fixing** - Test failure resolution
- **P3: Coverage** - Coverage analysis
- **P4: E2E Tests** - End-to-end testing

## State Colors

- **Green** - ready, completed (success states)
- **Cyan** - executing (active state)
- **Yellow** - initializing, cancelled (transitional states)
- **Red** - failed (error state)
- **White** - shutdown (final state)

## Advanced Usage

### Filtering Wrapper Output

Only show monitor output, hide debug logs:

```bash
.venv/bin/python3 scripts/claude_wrapper.py 2>/dev/null | .venv/bin/python3 scripts/watch_wrapper.py
```

### Saving Monitor Output

Capture final summary after execution:

```bash
.venv/bin/python3 scripts/demo_wrapper_output.py | .venv/bin/python3 scripts/watch_wrapper.py > monitor_summary.txt
```

### Custom Event History Size

The monitor shows the last 12 events by default. Modify in code:

```python
monitor = WrapperMonitor(max_events=20)  # Show last 20 events
```

## Integration with Autonomous Fixing

Monitor autonomous fixing executions in real-time:

### Quick Start (Recommended)

```bash
# Terminal 1: Start monitoring
./scripts/monitor_wrapper.sh

# Terminal 2: Run autonomous fixing
./scripts/autonomous_fix.sh config/projects/warps.yaml
```

### Simple Method (Recommended)

```bash
# Terminal 1: Start monitoring
./scripts/monitor.sh

# Terminal 2: Run autonomous fixing
./scripts/autonomous_fix.sh config/projects/warps.yaml
```

The `claude_client.py` writes all wrapper events to `logs/wrapper-realtime.log` for real-time monitoring.

## How It Works

### Event Flow

```
claude_client.py → logs/wrapper-realtime.log → tail -F → watch_wrapper.py → Terminal Dashboard
```

### Process

1. **Event Capture**: `claude_client.py` intercepts wrapper stdout and writes all JSON events to `logs/wrapper-realtime.log`
2. **Log Clearing**: Each new wrapper call clears the log file to ensure only current execution is shown
3. **Live Monitoring**: `tail -F` follows the log file by name (handles truncation) and pipes events to `watch_wrapper.py`
4. **Event Processing**: Monitor parses events, tracks state/phase/tools, and updates terminal dashboard in real-time
5. **Dashboard Rendering**: Rich library renders live terminal UI with current status and recent events

### Tracked Information

- **State**: ready, executing, completed, failed, cancelled, shutdown
- **Phase**: Current execution phase (e.g., "P1: Static Analysis", "P2: Testing")
- **Tools**: Tool usage with progress tracking (e.g., "Read 3/5")
- **Runtime**: Elapsed time since run started
- **Events**: Last 10 events with timestamps and icons
- **Statistics**: Stream count, errors, tool completion

## Troubleshooting

### Quick Diagnostics

Run the test script to verify the monitoring system:

```bash
./scripts/test_monitor.sh
```

This checks:
- Rich library installation
- Log directory permissions
- Event parsing functionality
- tail -F truncation handling
- Log file write permissions

### Monitor Not Updating

**Check if monitor is running:**
```bash
ps aux | grep -E "(tail|watch_wrapper)" | grep -v grep
```

**Verify log file has events:**
```bash
tail logs/wrapper-realtime.log
```

**Common issues:**
- Monitor must run in a real terminal (TTY), not with redirected output
- Use `tail -F` (capital F), not `tail -f`
- Ensure `rich` library is installed: `pip install rich`
- Check that wrapper emits events to stdout, not stderr

### Missing Events

- Ensure wrapper includes enhanced logging (phase_detected, tool_started, tool_completed)
- Check wrapper version supports real-time event emission
- Verify JSON format is correct (valid JSON per line)

### Performance Issues

- Reduce max_events if terminal is slow
- Use `--no-color` if ANSI codes cause issues
- Consider buffering if network latency is high

## Files

- `scripts/monitor.sh` - **Main script to start monitoring** (recommended)
- `scripts/watch_wrapper.py` - Real-time terminal dashboard (called by monitor.sh)
- `scripts/test_monitor.sh` - Test script to verify monitoring system works
- `scripts/demo_wrapper_output.py` - Demo/testing script for development
- `scripts/claude_wrapper.py` - Enhanced with phase/tool tracking
- `airflow_dags/autonomous_fixing/adapters/ai/claude_client.py` - Writes events to `logs/wrapper-realtime.log`

## See Also

- [Autonomous Fixing Documentation](AUTONOMOUS_FIXING.md)
- [Architecture Diagrams](architecture/autonomous-fixing-diagrams.md)
- [Wrapper History Tool](../scripts/claude_wrapper_history.sh)

## Future Enhancements

Potential improvements (not yet implemented):

- Web-based dashboard (Flask/FastAPI + SSE)
- Historical metrics visualization
- Multi-wrapper monitoring (parallel sessions)
- Alert triggers on failures
- Export to structured logs (JSON, CSV)
