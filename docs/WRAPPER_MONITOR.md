# Claude Wrapper Real-Time Monitor

Real-time visualization dashboard for `claude_wrapper.py` execution state and progress.

## Features

- **Live State Tracking**: See current execution state (ready, executing, completed, failed)
- **Phase Detection**: Automatically detects execution phase (P1-P4)
- **Tool Progress**: Track tool execution (Read, Bash, Edit, etc.) with progress counters
- **Event Stream**: Recent events with timestamps and icons
- **Runtime Metrics**: Execution time, tools completed, errors

## Quick Start

### Installation

```bash
# Install rich library (for terminal UI)
pip install -r requirements-dev.txt
```

### Basic Usage

#### 1. Monitor Live Wrapper Execution

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

Monitor autonomous fixing executions:

```bash
# Monitor test discovery phase
./scripts/autonomous_fixing_orchestrator.py --simulate 2>/dev/null | .venv/bin/python3 scripts/watch_wrapper.py

# Monitor live execution
./scripts/run_autonomous_fixing.sh | .venv/bin/python3 scripts/watch_wrapper.py
```

## Troubleshooting

### Monitor Not Updating

- Ensure wrapper outputs JSON events (check with `head -n 5` on output)
- Verify `rich` library is installed: `pip list | grep rich`
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

- `scripts/watch_wrapper.py` - Real-time monitor dashboard
- `scripts/demo_wrapper_output.py` - Demo/testing script
- `scripts/claude_wrapper.py` - Enhanced with phase/tool tracking

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
