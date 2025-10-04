# Interactive Wrapper Monitor

Enhanced real-time monitoring dashboard for `claude_wrapper.py` with event inspection capabilities.

## Features

### 🎨 New Layout Design

#### Split Header
- **Left Panel**: State, Phase, Runtime
  - Real-time execution state with color coding
  - Current processing phase detection
  - Elapsed runtime tracking

- **Right Panel**: Compact Statistics
  - Runs completed
  - Tool uses count
  - Stream events received
  - Errors encountered

#### Main Display
- **Left Panel**: Event List (50% width)
  - Chronological event feed (newest first)
  - Selection cursor (▶) for navigation
  - Shows time, icon, and event summary
  - Auto-scrolls as new events arrive

- **Right Panel**: Event Detail Inspector (50% width)
  - Full JSON view of selected event
  - Syntax-highlighted for readability
  - Shows complete event payload
  - Updates when selection changes

### ⌨️ Keyboard Controls

| Key | Action |
|-----|--------|
| `↑` or `k` | Navigate to previous event (older) |
| `↓` or `j` | Navigate to next event (newer) |
| `q` | Quit monitor |

**Vi-style navigation**: Use `j`/`k` keys for vi-like navigation
**Arrow keys**: Standard up/down arrow keys also work

### 🔍 Event Inspection

Select any event from the list to view:
- Full event type and timestamp
- Complete payload data
- Tool parameters (for tool use events)
- Response content (for stream events)
- Error details (for error events)

## Usage

### Basic Usage
```bash
# Terminal 1: Start monitoring
./scripts/monitor.sh

# Terminal 2: Run autonomous fixing
./scripts/autonomous_fix.sh config/projects/warps.yaml
```

### Testing Interactive Features
```bash
# Run demo with sample events
./scripts/test_interactive_monitor.sh
```

## Layout Diagram

```
╭────────────────────────────────────────────────────────────────────╮
│ 🤖 Claude Wrapper Monitor          │ 📊 Stats                     │
│ State:   EXECUTING                  │ Runs    1    Tools    5      │
│ Phase:   P1 Analysis                │ Streams 12   Errors   0      │
│ Runtime: 2m 34s                     │                              │
╰────────────────────────────────────────────────────────────────────╯
╭─────────────────────────────────────╮╭─────────────────────────────╮
│ 📋 Recent Events (15/20)            ││ 🔍 Event Detail             │
│ ↑/↓: Navigate  q: Quit              ││                             │
│                                     ││ {                            │
│   Time     Event                    ││   "event": "stream",         │
│ ────────────────────────────────    ││   "timestamp": "...",        │
│ ▶ 10:44:54 💬 Configuration updated ││   "payload": {              │
│   10:44:43 ✓ Edit completed         ││     "message_type": "...",  │
│   10:44:43 🔧 Edit: warps.yaml      ││     "content": [...]         │
│   10:44:36 ✓ Edit completed         ││   }                          │
│   10:44:36 🔧 Edit: warps.yaml      ││ }                            │
│   10:44:20 🎉 Completed: ok         ││                             │
│   ...                               ││                             │
╰─────────────────────────────────────╯╰─────────────────────────────╯
```

## Event Types

The monitor displays different icons for each event type:

| Icon | Event Type | Description |
|------|------------|-------------|
| 👁️ | monitor_ready | Monitor initialized |
| 🚀 | ready | Wrapper ready for input |
| ▶️ | run_started | Execution began |
| 📊 | phase_detected | Analysis phase identified |
| 🔧 | tool_started/tool_use | Tool execution |
| ✅ | tool_completed | Tool finished successfully |
| ✓ | tool_result | Tool returned result |
| 💬 | text_content | Text response from Claude |
| 🎉 | run_completed | Execution completed successfully |
| ❌ | run_failed | Execution failed |
| ⏹️ | cancelled/interrupted | Execution stopped |
| ⚠️ | error | Error occurred |

## Advanced Features

### Real-time Updates
- Dashboard refreshes 4 times per second
- New events appear automatically at the top
- Selection stays on the same event during updates
- Auto-scrolls when buffer is full (20 events)

### Event Buffer Management
- Maintains last 20 events in display
- Stores corresponding raw event data for inspection
- Selection cursor automatically adjusts when old events are removed
- Most recent event selected by default

### Terminal Compatibility
- Requires terminal with ANSI color support
- Interactive mode requires `/dev/tty` access
- Works with standard Unix-like terminals
- Falls back gracefully if terminal features unavailable

## Troubleshooting

### Keyboard Not Responding
- Ensure you're running in a real terminal (not via pipe)
- Check that `/dev/tty` is accessible
- Try using `j`/`k` keys instead of arrow keys

### Events Not Showing
- Verify `logs/wrapper-realtime.log` is being written
- Check wrapper is actually running (Terminal 2)
- Look for JSON parse errors in error count

### Display Issues
- Increase terminal size (recommended: 120x30 or larger)
- Check terminal supports ANSI colors
- Try reducing font size for more content

## Implementation Notes

### Threading Model
- Main thread: Reads events from stdin, updates display
- Keyboard thread: Reads from `/dev/tty`, handles navigation
- Both threads share state through monitor object
- Safe concurrent updates via Rich's Live display

### Event Storage
- `self.events`: Deque of (time, icon, message) tuples for display
- `self.raw_events`: Deque of raw Dict events for inspection
- Both synchronized with 20-event limit
- Selection index maintained across scrolling

### Color Scheme
- State panel: Color-coded by execution state
- Events panel: Blue border
- Detail panel: Cyan border
- Statistics: Green border
- Selected row: Bold text with yellow cursor

## Future Enhancements

Potential improvements:
- [ ] Event filtering (show only errors, tools, etc.)
- [ ] Event search/jump to event
- [ ] Save/export event history
- [ ] Diff view between events
- [ ] Custom color themes
- [ ] Configurable refresh rate
- [ ] Event statistics and charts
