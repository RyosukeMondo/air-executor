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
import select
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

    def __init__(self, max_events: int = 20, filter_cwd: str | None = None):
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
        self.last_event_detail = None  # Store detailed view of last event
        self.raw_events: deque = deque(maxlen=max_events)  # Store raw events for navigation

        # Project tracking (filter by cwd where monitor is run)
        self.project_name = None
        self.cwd = None
        self.filter_cwd = filter_cwd  # Set from command line or first event
        self.current_run_id = None  # Track run_id of matching runs

        # Event history (recent events)
        self.events: deque = deque(maxlen=max_events)

        # Interactive navigation state
        self.cursor_position = 0  # Visual position from top (0 = top row)
        self.paused = False  # Pause auto-scrolling

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

        # Extract and set filter_cwd from first event with cwd (if not already set)
        if self.filter_cwd is None and "cwd" in event:
            self.filter_cwd = event["cwd"]

        # Track run_id when we see run_started with matching cwd
        if event_type == "run_started" and event.get("cwd") == self.filter_cwd:
            self.current_run_id = event.get("run_id")
            if not self.project_name:
                self.project_name = event.get("project", os.path.basename(self.filter_cwd))
                self.cwd = self.filter_cwd

        # Filter: Only process events matching our cwd or belonging to current run
        event_cwd = event.get("cwd")
        event_run_id = event.get("run_id")

        # Skip if event has different cwd (and is not from current run)
        if event_cwd and self.filter_cwd and event_cwd != self.filter_cwd:
            return  # Different project entirely

        # Skip if event has run_id but doesn't match our current run
        if event_run_id and self.current_run_id and event_run_id != self.current_run_id:
            return  # Different run in same or different project

        # Store raw event for navigation
        self.raw_events.append(event)

        # Update detail view based on cursor position (cursor stays at same visual position)
        self._update_selected_detail()

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

    def _format_stream_event(self, payload: Dict[str, Any]) -> str:
        """Format stream event content."""
        content = payload.get("content", [])

        # Look for text in content
        text_items = [
            item.get("text", "") for item in content if isinstance(item, dict) and "text" in item
        ]
        if text_items:
            combined_text = "\n\n".join(text_items)
            return f"[bold cyan]Text Content:[/bold cyan]\n{combined_text}"

        # Look for tool uses in content
        tool_items = [item for item in content if isinstance(item, dict) and "name" in item]
        if tool_items:
            return self._format_tool_uses(tool_items)

        return ""

    def _format_tool_uses(self, tool_items: list) -> str:
        """Format tool use items for display."""
        lines = ["[bold cyan]Tool Uses:[/bold cyan]"]
        for tool in tool_items:
            tool_name = tool.get("name", "unknown")
            tool_input = tool.get("input", {})
            lines.append(f"\n[yellow]{tool_name}[/yellow]:")
            for key, value in tool_input.items():
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                lines.append(f"  {key}: {value_str}")
        return "\n".join(lines)

    def _format_error_event(self, event: Dict[str, Any]) -> str:
        """Format error event."""
        error_msg = event.get("error", event.get("message", "Unknown error"))
        details = event.get("details", "")
        result = f"[bold red]Error:[/bold red]\n{error_msg}"
        if details:
            result += f"\n\nDetails:\n{details}"
        return result

    def _format_run_started(self, event: Dict[str, Any]) -> str:
        """Format run_started event."""
        run_id = event.get("run_id", "N/A")
        prompt_preview = event.get("prompt", "")[:200]
        result = f"[bold green]Run Started[/bold green]\nID: {run_id}"
        if "cwd" in event:
            result += f"\n[dim]Working Directory:[/dim] {event['cwd']}"
        if prompt_preview:
            result += f"\n\nPrompt: {prompt_preview}..."
        return result

    def _format_run_completed(self, event: Dict[str, Any]) -> str:
        """Format run_completed event."""
        reason = event.get("reason", "ok")
        output = event.get("output", "")
        result = f"[bold green]Run Completed[/bold green]\nReason: {reason}"
        if output:
            output_preview = output[:300] + ("..." if len(output) > 300 else "")
            result += f"\n\nOutput:\n{output_preview}"
        return result

    def _format_phase_event(self, event: Dict[str, Any]) -> str:
        """Format phase_detected event."""
        phase = event.get("phase", "Unknown")
        return f"[bold blue]Phase:[/bold blue] {phase}"

    def _format_state_event(self, event: Dict[str, Any]) -> str:
        """Format state event."""
        state = event.get("state", "unknown")
        session_id = event.get("last_session_id", "N/A")
        return f"[bold blue]State:[/bold blue] {state}\nSession: {session_id}"

    def _format_default_event(self, event: Dict[str, Any], event_type: str) -> str:
        """Format default/unknown event."""
        lines = [f"[bold cyan]{event_type}[/bold cyan]"]

        # Show cwd/project at top if present
        if "cwd" in event:
            lines.append(f"[dim]Working Directory:[/dim] {event['cwd']}")
        if "project" in event and "cwd" not in event:
            lines.append(f"[dim]Project:[/dim] {event['project']}")

        for key, value in event.items():
            if key in ("event", "timestamp", "cwd", "project"):
                continue
            value_str = str(value)
            if len(value_str) > 150:
                value_str = value_str[:150] + "..."
            lines.append(f"{key}: {value_str}")
        return "\n".join(lines)

    def _format_stream_as_bare(self, event: Dict[str, Any]) -> str:
        """Format stream event like a bare event - extract content from payload.content."""
        lines = ["[bold cyan]stream[/bold cyan]"]

        # Show top-level fields (like run_id)
        for key, value in event.items():
            if key in ("event", "timestamp", "payload"):
                continue
            value_str = str(value)
            if len(value_str) > 150:
                value_str = value_str[:150] + "..."
            lines.append(f"{key}: {value_str}")

        # Extract and show content from payload.content (same level as other fields)
        payload = event.get("payload", {})
        content_items = payload.get("content", [])

        if content_items:
            # Get first content item
            item = content_items[0] if isinstance(content_items, list) else content_items

            if isinstance(item, dict):
                # Show all fields from content item (text, content, tool_use_id, etc.)
                for key, value in item.items():
                    value_str = str(value)
                    # Truncate long values
                    if len(value_str) > 300:
                        value_str = value_str[:300] + "..."
                    lines.append(f"{key}: {value_str}")

        return "\n".join(lines)

    def _format_event_detail(self, event: Dict[str, Any]) -> str:
        """Format event details based on known patterns for human-readable display."""
        event_type = event.get("event", "unknown")

        # Stream events - treat content same as bare events
        if event_type == "stream":
            return self._format_stream_as_bare(event)

        # Error events
        if event_type in ("error", "run_failed"):
            return self._format_error_event(event)

        # Run events
        if event_type == "run_started":
            return self._format_run_started(event)
        if event_type == "run_completed":
            return self._format_run_completed(event)

        # Phase/State events
        if event_type == "phase_detected":
            return self._format_phase_event(event)
        if event_type == "state":
            return self._format_state_event(event)

        # Default
        return self._format_default_event(event, event_type)

    def add_event(self, timestamp: str, icon: str, message: str) -> None:
        """Add event to recent events list."""
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            time_str = timestamp[:8] if len(timestamp) >= 8 else timestamp

        self.events.append((time_str, icon, message))

    def navigate_up(self) -> None:
        """Navigate cursor up (visually up in list, to newer events)."""
        if self.cursor_position > 0:
            self.cursor_position -= 1
            self._update_selected_detail()

    def navigate_down(self) -> None:
        """Navigate cursor down (visually down in list, to older events)."""
        max_position = min(len(self.events) - 1, self.max_events - 1)
        if self.cursor_position < max_position:
            self.cursor_position += 1
            self._update_selected_detail()

    def toggle_pause(self) -> None:
        """Toggle pause state for auto-scrolling."""
        self.paused = not self.paused

    def _update_selected_detail(self) -> None:
        """Update detail panel based on cursor position (visual position from top)."""
        if not self.raw_events:
            self.last_event_detail = None
            return

        # Events displayed in descending order (newest first)
        # Cursor position 0 = top (newest), higher = older
        events_list = list(self.raw_events)

        # Ensure cursor is within bounds
        if self.cursor_position >= len(events_list):
            self.cursor_position = max(0, len(events_list) - 1)

        try:
            # Reverse list to show newest first, then index by cursor position
            selected_event = events_list[-(self.cursor_position + 1)]

            # Get the formatted message from events list
            formatted_message = None
            if self.events and self.cursor_position < len(self.events):
                events_reversed = list(reversed(self.events))
                time_str, icon, message = events_reversed[self.cursor_position]
                formatted_message = f"{icon} {message}"

            # Format detail with message at top
            detail = self._format_event_detail(selected_event)
            if formatted_message:
                self.last_event_detail = (
                    f"[bold yellow]{formatted_message}[/bold yellow]\n\n{detail}"
                )
            else:
                self.last_event_detail = detail
        except (IndexError, TypeError):
            self.last_event_detail = None

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

    def _build_header_panel(self) -> Panel:
        """Build the header panel with current state."""
        header_table = Table.grid(padding=1)
        header_table.add_column(style="bold cyan", justify="right", width=14)
        header_table.add_column(style="bold white")

        # Project name at top
        if self.project_name:
            header_table.add_row("Project:", f"📁 {self.project_name}")

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

        return Panel(
            header_table,
            title="🤖 Claude Wrapper Monitor",
            border_style=self.get_state_color(),
            box=box.ROUNDED,
        )

    def _build_stats_panel(self) -> Panel:
        """Build the statistics panel."""
        stats_table = Table(show_header=False, box=box.SIMPLE, expand=True)
        stats_table.add_column("Metric", style="cyan", justify="left")
        stats_table.add_column("Value", style="white", justify="right")

        stats_table.add_row("Runs", str(self.stats["runs_completed"]))
        stats_table.add_row("Tool Uses", str(self.stats["tool_uses"]))
        stats_table.add_row("Text Blocks", str(self.stats["text_blocks"]))
        stats_table.add_row("Streams", str(self.stats["streams_received"]))
        stats_table.add_row("Errors", str(self.stats["errors"]))

        if self.tools_used:
            stats_table.add_row("─" * 12, "─" * 8)
            stats_table.add_row("[bold]Recent Tools", "")
            for tool_name, _ in list(self.tools_used)[-5:]:
                stats_table.add_row(f"  {tool_name}", "")

        return Panel(
            stats_table,
            title="📊 Statistics",
            border_style="green",
            box=box.ROUNDED,
        )

    def _build_events_panel(self) -> Panel:
        """Build the events panel with recent activity."""
        events_table = Table(show_header=True, box=box.SIMPLE, expand=True)
        events_table.add_column("", width=2)
        events_table.add_column("Time", style="dim", width=10)
        events_table.add_column("Event", overflow="fold")

        if not self.events:
            events_table.add_row("", "--:--:--", "Waiting for events...")
        else:
            events_list = list(reversed(self.events))
            for idx, (time_str, icon, message) in enumerate(events_list):
                is_selected = idx == self.cursor_position
                indicator = (
                    "👉" if is_selected and not self.paused else ("⏸️" if is_selected else "")
                )
                style = "bold yellow" if is_selected else ""
                events_table.add_row(indicator, time_str, f"{icon} {message}", style=style)

        events_title = "📋 Recent Events" + (" [PAUSED]" if self.paused else "")
        border_style = "yellow" if self.paused else "blue"

        return Panel(events_table, title=events_title, border_style=border_style, box=box.ROUNDED)

    def _build_detail_panel(self) -> Panel:
        """Build the event detail panel."""
        if self.last_event_detail:
            detail_content = Text.from_markup(self.last_event_detail)
        else:
            detail_content = Text("Waiting for events...", style="dim")

        detail_title = f"🔍 Event Detail [Row {self.cursor_position + 1}/{len(self.raw_events)}]"
        if len(self.raw_events) > 0:
            detail_title += " | ↑↓:Navigate SPACE:Pause Q:Quit"

        return Panel(detail_content, title=detail_title, border_style="magenta", box=box.ROUNDED)

    def build_dashboard(self) -> Layout:
        """Build the live dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="top", size=8),
            Layout(name="bottom", size=None),
        )

        layout["top"].split_row(
            Layout(name="header", ratio=3),
            Layout(name="stats", ratio=1),
        )

        layout["bottom"].split_row(
            Layout(name="events", ratio=2),
            Layout(name="detail", ratio=2),
        )

        layout["header"].update(self._build_header_panel())
        layout["stats"].update(self._build_stats_panel())
        layout["events"].update(self._build_events_panel())
        layout["detail"].update(self._build_detail_panel())

        return layout

    def _setup_keyboard(self):
        """Setup keyboard input from /dev/tty. Returns (fd, has_keyboard, old_settings)."""
        import termios
        import tty

        try:
            keyboard_fd = open("/dev/tty", "r")
        except (OSError, FileNotFoundError):
            return None, False, None

        try:
            old_settings = termios.tcgetattr(keyboard_fd)
            tty.setcbreak(keyboard_fd.fileno())
            return keyboard_fd, True, old_settings
        except Exception:
            keyboard_fd.close()
            return None, False, None

    def _restore_keyboard(self, keyboard_fd, old_settings):
        """Restore keyboard terminal settings."""
        import termios

        if keyboard_fd and old_settings:
            try:
                termios.tcsetattr(keyboard_fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass
        if keyboard_fd:
            keyboard_fd.close()

    def _handle_keyboard_input(self, keyboard_fd, live):
        """Handle keyboard input and return True if should quit."""
        key = keyboard_fd.read(1)

        if key == "q" or key == "Q":
            return True

        if key == " ":
            self.toggle_pause()
            live.update(self.build_dashboard())
            return False

        if key == "\x1b":  # Escape sequence for arrow keys
            next1 = keyboard_fd.read(1)
            next2 = keyboard_fd.read(1)
            if next1 == "[":
                if next2 == "A":  # Up arrow
                    self.navigate_up()
                    live.update(self.build_dashboard())
                elif next2 == "B":  # Down arrow
                    self.navigate_down()
                    live.update(self.build_dashboard())

        return False

    def _process_stdin_line(self, line, live):
        """Process a single line from stdin. Returns True if EOF."""
        if not line:
            return True

        line = line.strip()
        if not line:
            return False

        try:
            event = json.loads(line)
            self.process_event(event)
            live.update(self.build_dashboard())
        except json.JSONDecodeError:
            pass
        except Exception as e:
            self.stats["errors"] += 1
            self.add_event(
                datetime.now(timezone.utc).isoformat(),
                "⚠️",
                f"Parse error: {str(e)[:40]}",
            )
            live.update(self.build_dashboard())

        return False

    def _run_event_loop(self, live, keyboard_fd, has_keyboard):
        """Main event loop for processing stdin and keyboard."""
        while True:
            # Select on stdin and keyboard
            if has_keyboard:
                readable, _, _ = select.select([keyboard_fd, sys.stdin], [], [], 0.05)
                if keyboard_fd in readable:
                    if self._handle_keyboard_input(keyboard_fd, live):
                        break
            else:
                readable, _, _ = select.select([sys.stdin], [], [], 0.05)

            # Process stdin events
            if sys.stdin in readable:
                line = sys.stdin.readline()
                if self._process_stdin_line(line, live):
                    break

    def run(self) -> None:
        """Run the live monitor, reading from stdin."""
        keyboard_fd, has_keyboard, old_settings = self._setup_keyboard()

        try:
            with Live(self.build_dashboard(), refresh_per_second=4, console=self.console) as live:
                try:
                    self._run_event_loop(live, keyboard_fd, has_keyboard)
                except KeyboardInterrupt:
                    self.state = "interrupted"
                    self.add_event(
                        datetime.now(timezone.utc).isoformat(), "⏹️", "Monitor stopped by user"
                    )
                    live.update(self.build_dashboard())
        finally:
            self._restore_keyboard(keyboard_fd, old_settings)

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
    import os

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

    # Filter by current working directory (set by monitor.sh via env var or use current dir)
    filter_cwd = os.environ.get("MONITOR_CWD", os.getcwd())
    monitor = WrapperMonitor(max_events=20, filter_cwd=filter_cwd)

    try:
        monitor.run()
    except Exception as e:
        print(f"\n❌ Monitor failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
