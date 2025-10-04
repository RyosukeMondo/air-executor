#!/usr/bin/env python3
"""
Real-time Claude Wrapper Monitor

Live dashboard for monitoring claude_wrapper.py execution in real-time.

Usage:
    # Watch wrapper output directly
    ./scripts/watch_wrapper.py < wrapper_output.log

    # Pipe from running wrapper
    python scripts/claude_wrapper.py | python scripts/watch_wrapper.py

    # Watch wrapper logs with tail
    tail -f logs/wrapper-*.log | python scripts/watch_wrapper.py
"""

import json
import sys
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict

try:
    from rich import box
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("ERROR: 'rich' library not installed.", file=sys.stderr)
    print("Install with: pip install rich", file=sys.stderr)
    sys.exit(1)


class WrapperMonitor:
    """Real-time monitor for Claude wrapper execution."""

    def __init__(self, max_events: int = 10):
        self.console = Console()
        self.max_events = max_events

        # State tracking
        self.state = "initializing"
        self.phase = "Unknown"
        self.run_id = None
        self.start_time = None
        self.current_tool = None
        self.tool_progress = "0/0"
        self.session_id = None

        # Event history (recent events)
        self.events: deque = deque(maxlen=max_events)

        # Statistics
        self.stats = {
            "tools_completed": 0,
            "tools_total": 0,
            "streams_received": 0,
            "errors": 0,
        }

    def process_event(self, event: Dict[str, Any]) -> None:  # noqa: C901
        """Process a single JSON event from the wrapper."""
        event_type = event.get("event")
        timestamp = event.get("timestamp", datetime.now(timezone.utc).isoformat())

        if event_type == "ready":
            self.state = "ready"
            self.start_time = None
            self.add_event(timestamp, "🚀", "Wrapper ready")

        elif event_type == "run_started":
            self.state = "executing"
            self.run_id = event.get("run_id")
            self.start_time = datetime.fromisoformat(timestamp)
            self.add_event(timestamp, "▶️", "Run started")

        elif event_type == "phase_detected":
            self.phase = event.get("phase", "Unknown")
            self.add_event(timestamp, "📊", f"Phase: {self.phase}")

        elif event_type == "tool_started":
            tool = event.get("tool", "unknown")
            self.current_tool = tool
            self.tool_progress = event.get("progress", "0/0")
            self.stats["tools_total"] = int(self.tool_progress.split("/")[1])
            self.add_event(timestamp, "🔧", f"Tool: {tool}")

        elif event_type == "tool_completed":
            tool = event.get("tool", self.current_tool)
            self.current_tool = None
            self.tool_progress = event.get("progress", self.tool_progress)
            self.stats["tools_completed"] = int(self.tool_progress.split("/")[0])
            self.add_event(timestamp, "✅", f"Done: {tool}")

        elif event_type == "stream":
            self.stats["streams_received"] += 1
            payload = event.get("payload", {})
            msg_type = payload.get("message_type", "")

            # Only log significant stream events
            if "text" in msg_type.lower() or msg_type == "TextBlock":
                text = payload.get("text", "")
                if text and len(text.strip()) > 0:
                    preview = text[:50] + "..." if len(text) > 50 else text
                    self.add_event(timestamp, "💬", f"Text: {preview}")

        elif event_type == "run_completed":
            self.state = "completed"
            reason = event.get("reason", "ok")
            self.add_event(timestamp, "🎉", f"Completed: {reason}")

        elif event_type == "run_failed":
            self.state = "failed"
            self.stats["errors"] += 1
            error = event.get("error", "Unknown error")
            self.add_event(timestamp, "❌", f"Failed: {error}")

        elif event_type == "run_cancelled":
            self.state = "cancelled"
            self.add_event(timestamp, "⏹️", "Cancelled")

        elif event_type == "shutdown":
            self.state = "shutdown"
            self.add_event(timestamp, "🛑", "Shutdown")

        elif event_type == "error":
            self.stats["errors"] += 1
            error_msg = event.get("error", "Unknown")
            self.add_event(timestamp, "⚠️", f"Error: {error_msg}")

        elif event_type == "state":
            new_state = event.get("state", "unknown")
            self.state = new_state
            self.session_id = event.get("last_session_id")

    def add_event(self, timestamp: str, icon: str, message: str) -> None:
        """Add event to recent events list."""
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            time_str = timestamp[:8] if len(timestamp) >= 8 else timestamp

        self.events.append((time_str, icon, message))

    def get_runtime(self) -> str:
        """Calculate current runtime."""
        if not self.start_time:
            return "0s"

        delta = datetime.now(timezone.utc) - self.start_time
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s"
        else:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"

    def get_state_color(self) -> str:
        """Get color for current state."""
        state_colors = {
            "initializing": "yellow",
            "ready": "green",
            "executing": "cyan",
            "completed": "green",
            "failed": "red",
            "cancelled": "yellow",
            "shutdown": "white",
        }
        return state_colors.get(self.state, "white")

    def build_dashboard(self) -> Layout:
        """Build the live dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=7),
            Layout(name="events", size=None),
        )

        # Header panel with current state
        header_table = Table.grid(padding=1)
        header_table.add_column(style="bold cyan", justify="right")
        header_table.add_column(style="bold white")

        state_text = Text(self.state.upper(), style=f"bold {self.get_state_color()}")
        header_table.add_row("State:", state_text)
        header_table.add_row("Phase:", self.phase)
        header_table.add_row("Runtime:", self.get_runtime())

        if self.current_tool:
            header_table.add_row("Current Tool:", f"🔧 {self.current_tool}")

        header_table.add_row("Progress:", f"{self.tool_progress} tools")

        layout["header"].update(
            Panel(
                header_table,
                title="🤖 Claude Wrapper Monitor",
                border_style=self.get_state_color(),
                box=box.ROUNDED,
            )
        )

        # Events panel with recent activity
        events_table = Table(show_header=True, box=box.SIMPLE, expand=True)
        events_table.add_column("Time", style="dim", width=10)
        events_table.add_column("Event", width=50)

        if not self.events:
            events_table.add_row("--:--:--", "No events yet...")
        else:
            for time_str, icon, message in self.events:
                events_table.add_row(time_str, f"{icon} {message}")

        layout["events"].update(
            Panel(
                events_table,
                title="📋 Recent Events",
                border_style="blue",
                box=box.ROUNDED,
            )
        )

        return layout

    def run(self) -> None:
        """Run the live monitor, reading from stdin."""
        with Live(self.build_dashboard(), refresh_per_second=4, console=self.console) as live:
            try:
                for line in sys.stdin:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                        self.process_event(event)
                        live.update(self.build_dashboard())
                    except json.JSONDecodeError:
                        # Skip non-JSON lines (e.g., debug output)
                        continue
                    except Exception as e:
                        self.stats["errors"] += 1
                        self.add_event(
                            datetime.now(timezone.utc).isoformat(),
                            "⚠️",
                            f"Parse error: {str(e)[:40]}",
                        )
                        live.update(self.build_dashboard())

            except KeyboardInterrupt:
                self.state = "interrupted"
                self.add_event(
                    datetime.now(timezone.utc).isoformat(), "⏹️", "Monitor stopped by user"
                )
                live.update(self.build_dashboard())

        # Final summary
        self.console.print("\n[bold]Monitor Summary:[/bold]")
        self.console.print(f"  Final state: [{self.get_state_color()}]{self.state}[/]")
        self.console.print(
            f"  Tools completed: {self.stats['tools_completed']}/{self.stats['tools_total']}"
        )
        self.console.print(f"  Stream events: {self.stats['streams_received']}")
        self.console.print(f"  Errors: {self.stats['errors']}")
        if self.start_time:
            self.console.print(f"  Total runtime: {self.get_runtime()}")


def main():
    """Main entry point."""
    monitor = WrapperMonitor(max_events=12)

    try:
        monitor.run()
    except Exception as e:
        print(f"\n❌ Monitor failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
