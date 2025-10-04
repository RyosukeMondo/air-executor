#!/home/rmondo/repos/air-executor/.venv/bin/python3
"""
Real-time Claude Wrapper Monitor

Live dashboard for monitoring claude_wrapper.py execution in real-time.

⚠️  DO NOT RUN THIS SCRIPT DIRECTLY!
    Use: ./scripts/monitor.sh instead

RECOMMENDED USAGE (Autonomous Fixing):
    Terminal 1: ./scripts/monitor.sh
    Terminal 2: ./scripts/autonomous_fix.sh config/projects/warps.yaml

ADVANCED USAGE (piping from other sources):
    # Pipe from running wrapper
    python scripts/claude_wrapper.py | python scripts/watch_wrapper.py

    # Watch wrapper logs with tail
    tail -f logs/wrapper-realtime.log | python scripts/watch_wrapper.py

    # Watch demo output
    python scripts/demo_wrapper_output.py | python scripts/watch_wrapper.py
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

    def __init__(self, max_events: int = 20):
        self.console = Console()
        self.max_events = max_events

        # State tracking
        self.state = "initializing"
        self.phase = "Unknown"
        self.run_id = None
        self.start_time = None
        self.current_tool = None
        self.current_tool_params = None
        self.tool_progress = "0/0"
        self.session_id = None
        self.last_text_content = None

        # Event history (recent events)
        self.events: deque = deque(maxlen=max_events)

        # Tool tracking
        self.tools_used = deque(maxlen=10)
        self.active_tools = {}

        # Statistics
        self.stats = {
            "tools_completed": 0,
            "tools_total": 0,
            "streams_received": 0,
            "text_blocks": 0,
            "tool_uses": 0,
            "errors": 0,
            "runs_completed": 0,
        }

    def process_event(self, event: Dict[str, Any]) -> None:
        """Process a single JSON event from the wrapper."""
        event_type = event.get("event")
        timestamp = event.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Dispatch to specific event handlers
        handlers = {
            "monitor_ready": self._handle_monitor_ready,
            "ready": self._handle_ready,
            "run_started": self._handle_run_started,
            "phase_detected": self._handle_phase_detected,
            "tool_started": self._handle_tool_started,
            "tool_completed": self._handle_tool_completed,
            "stream": self._handle_stream,
            "run_completed": self._handle_run_completed,
            "run_failed": self._handle_run_failed,
            "run_cancelled": self._handle_run_cancelled,
            "shutdown": self._handle_shutdown,
            "error": self._handle_error,
            "state": self._handle_state,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event, timestamp)

    def _handle_monitor_ready(self, event: Dict[str, Any], timestamp: str) -> None:
        self.state = "monitoring"
        message = event.get("message", "Monitor ready")
        self.add_event(timestamp, "👁️", message)

    def _handle_ready(self, event: Dict[str, Any], timestamp: str) -> None:
        self.state = "ready"
        self.start_time = None
        self.add_event(timestamp, "🚀", "Wrapper ready")

    def _handle_run_started(self, event: Dict[str, Any], timestamp: str) -> None:
        self.state = "executing"
        self.run_id = event.get("run_id")
        # Parse as timezone-aware datetime to match datetime.now(timezone.utc)
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        self.start_time = dt
        self.add_event(timestamp, "▶️", "Run started")

    def _handle_phase_detected(self, event: Dict[str, Any], timestamp: str) -> None:
        self.phase = event.get("phase", "Unknown")
        self.add_event(timestamp, "📊", f"Phase: {self.phase}")

    def _handle_tool_started(self, event: Dict[str, Any], timestamp: str) -> None:
        tool = event.get("tool", "unknown")
        self.current_tool = tool
        self.tool_progress = event.get("progress", "0/0")
        self.stats["tools_total"] = int(self.tool_progress.split("/")[1])
        self.add_event(timestamp, "🔧", f"Tool: {tool}")

    def _handle_tool_completed(self, event: Dict[str, Any], timestamp: str) -> None:
        tool = event.get("tool", self.current_tool)
        self.current_tool = None
        self.tool_progress = event.get("progress", self.tool_progress)
        self.stats["tools_completed"] = int(self.tool_progress.split("/")[0])
        self.add_event(timestamp, "✅", f"Done: {tool}")

    def _handle_stream(self, event: Dict[str, Any], timestamp: str) -> None:
        self.stats["streams_received"] += 1
        payload = event.get("payload", {})
        msg_type = payload.get("message_type", "")
        content = payload.get("content", [])

        # Process AssistantMessage with tool uses
        if msg_type == "AssistantMessage" and content:
            self._process_assistant_message(content, timestamp)

        # Process UserMessage (tool results)
        elif msg_type == "UserMessage" and content:
            self._process_user_message(content, timestamp)

    def _process_assistant_message(self, content: list, timestamp: str) -> None:
        """Process AssistantMessage content."""
        for item in content:
            self._process_content_item(item, timestamp)

    def _process_user_message(self, content: list, timestamp: str) -> None:
        """Process UserMessage content (tool results)."""
        for item in content:
            if isinstance(item, dict) and "tool_use_id" in item:
                tool_id = item.get("tool_use_id")
                if tool_id in self.active_tools:
                    tool_name = self.active_tools[tool_id]["name"]
                    is_error = item.get("is_error", False)

                    if is_error:
                        self.add_event(timestamp, "❌", f"{tool_name} failed")
                    else:
                        self.add_event(timestamp, "✓", f"{tool_name} completed")

                    del self.active_tools[tool_id]

    def _process_content_item(self, item: Dict[str, Any], timestamp: str) -> None:
        """Process a single content item (tool use or text)."""
        if isinstance(item, dict) and "name" in item:
            self._handle_tool_use(item, timestamp)
        elif isinstance(item, dict) and "text" in item:
            self._handle_text_content(item, timestamp)

    def _handle_tool_use(self, item: Dict[str, Any], timestamp: str) -> None:
        """Handle tool use content item."""
        tool_name = item.get("name")
        tool_id = item.get("id", "")
        tool_input = item.get("input", {})

        self.stats["tool_uses"] += 1
        self.active_tools[tool_id] = {"name": tool_name, "input": tool_input}

        input_preview = self._format_tool_input(tool_name, tool_input)
        self.add_event(timestamp, "🔧", f"{tool_name}: {input_preview}")
        self.tools_used.append((tool_name, input_preview))

    def _handle_text_content(self, item: Dict[str, Any], timestamp: str) -> None:
        """Handle text content item."""
        text = item.get("text", "")
        if text and len(text.strip()) > 0:
            self.stats["text_blocks"] += 1
            self.last_text_content = text
            preview = text[:60] + "..." if len(text) > 60 else text
            self.add_event(timestamp, "💬", preview)

    def _format_tool_input(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Format tool input for display."""
        if tool_name == "Read":
            return tool_input.get("file_path", "").split("/")[-1]
        elif tool_name == "Edit":
            return tool_input.get("file_path", "").split("/")[-1]
        elif tool_name == "Write":
            return tool_input.get("file_path", "").split("/")[-1]
        elif tool_name == "Bash":
            cmd = tool_input.get("command", "")
            return cmd[:50] + "..." if len(cmd) > 50 else cmd
        elif tool_name == "Glob":
            return tool_input.get("pattern", "")
        elif tool_name == "Grep":
            return tool_input.get("pattern", "")
        else:
            # Generic preview of first parameter
            if tool_input:
                first_val = str(list(tool_input.values())[0])
                return first_val[:50] + "..." if len(first_val) > 50 else first_val
            return ""

    def _handle_run_completed(self, event: Dict[str, Any], timestamp: str) -> None:
        self.state = "completed"
        self.stats["runs_completed"] += 1
        reason = event.get("reason", "ok")
        self.add_event(timestamp, "🎉", f"Completed: {reason}")

    def _handle_run_failed(self, event: Dict[str, Any], timestamp: str) -> None:
        self.state = "failed"
        self.stats["errors"] += 1
        error = event.get("error", "Unknown error")
        self.add_event(timestamp, "❌", f"Failed: {error}")

    def _handle_run_cancelled(self, event: Dict[str, Any], timestamp: str) -> None:
        self.state = "cancelled"
        self.add_event(timestamp, "⏹️", "Cancelled")

    def _handle_shutdown(self, event: Dict[str, Any], timestamp: str) -> None:
        self.state = "shutdown"
        self.add_event(timestamp, "🛑", "Shutdown")

    def _handle_error(self, event: Dict[str, Any], timestamp: str) -> None:
        self.stats["errors"] += 1
        error_msg = event.get("error", "Unknown")
        self.add_event(timestamp, "⚠️", f"Error: {error_msg}")

    def _handle_state(self, event: Dict[str, Any], timestamp: str) -> None:
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
            "monitoring": "blue",
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
            Layout(name="header", size=8),
            Layout(name="main", size=None),
        )

        layout["main"].split_row(
            Layout(name="events", ratio=2),
            Layout(name="stats", ratio=1),
        )

        # Header panel with current state
        header_table = Table.grid(padding=1)
        header_table.add_column(style="bold cyan", justify="right", width=14)
        header_table.add_column(style="bold white")

        state_text = Text(self.state.upper(), style=f"bold {self.get_state_color()}")
        header_table.add_row("State:", state_text)
        header_table.add_row("Phase:", self.phase)
        header_table.add_row("Runtime:", self.get_runtime())

        if self.session_id:
            session_preview = self.session_id[:16] + "..."
            header_table.add_row("Session:", session_preview)

        if self.active_tools:
            active = ", ".join([v["name"] for v in self.active_tools.values()])
            header_table.add_row("Active Tools:", f"🔧 {active}")

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
        events_table.add_column("Event", overflow="fold")

        if not self.events:
            events_table.add_row("--:--:--", "Waiting for events...")
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

        # Statistics panel
        stats_table = Table(show_header=False, box=box.SIMPLE, expand=True)
        stats_table.add_column("Metric", style="cyan", justify="left")
        stats_table.add_column("Value", style="white", justify="right")

        stats_table.add_row("Runs", str(self.stats["runs_completed"]))
        stats_table.add_row("Tool Uses", str(self.stats["tool_uses"]))
        stats_table.add_row("Text Blocks", str(self.stats["text_blocks"]))
        stats_table.add_row("Streams", str(self.stats["streams_received"]))
        stats_table.add_row("Errors", str(self.stats["errors"]))

        # Recent tools
        if self.tools_used:
            stats_table.add_row("─" * 12, "─" * 8)
            stats_table.add_row("[bold]Recent Tools", "")
            for tool_name, _ in list(self.tools_used)[-5:]:
                stats_table.add_row(f"  {tool_name}", "")

        layout["stats"].update(
            Panel(
                stats_table,
                title="📊 Statistics",
                border_style="green",
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
        self.console.print(f"  Runs completed: {self.stats['runs_completed']}")
        self.console.print(f"  Tool uses: {self.stats['tool_uses']}")
        self.console.print(f"  Text blocks: {self.stats['text_blocks']}")
        self.console.print(f"  Stream events: {self.stats['streams_received']}")
        self.console.print(f"  Errors: {self.stats['errors']}")
        if self.start_time:
            self.console.print(f"  Total runtime: {self.get_runtime()}")

        # Show recent tools used
        if self.tools_used:
            self.console.print("\n[bold]Tools Used:[/bold]")
            tool_counts: Dict[str, int] = {}
            for tool_name, _ in self.tools_used:
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

            for tool_name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
                self.console.print(f"  {tool_name}: {count}x")


def main():
    """Main entry point."""
    # Check if being run directly from terminal (not piped)
    if sys.stdin.isatty():
        print("\n⚠️  ERROR: Don't run watch_wrapper.py directly!", file=sys.stderr)
        print("\n   Use this instead:", file=sys.stderr)
        print("   ./scripts/monitor.sh\n", file=sys.stderr)
        print("   Or pipe events to it:", file=sys.stderr)
        print(
            "   tail -F logs/wrapper-realtime.log | python scripts/watch_wrapper.py\n",
            file=sys.stderr,
        )
        sys.exit(1)

    monitor = WrapperMonitor(max_events=20)

    try:
        monitor.run()
    except Exception as e:
        print(f"\n❌ Monitor failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
