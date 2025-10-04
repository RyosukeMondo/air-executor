"""
Claude Client - Helper for calling claude_wrapper with JSON protocol.

Provides simple interface to claude_wrapper's streaming JSON protocol.
"""

import json
import subprocess
import time

from ...domain.interfaces.ai_client import IAIClient
from .response_parser import ResponseParser
from .wrapper_history import WrapperHistoryLogger


class ClaudeClient(IAIClient):
    """Simple client for claude_wrapper JSON protocol."""

    def __init__(self, wrapper_path: str, python_exec: str, debug_logger=None, config: dict = None):
        """
        Initialize Claude client.

        Args:
            wrapper_path: Path to claude_wrapper.py
            python_exec: Python executable to use
            debug_logger: Optional DebugLogger instance for logging wrapper calls
            config: Optional config dict with logging settings
        """
        self.wrapper_path = wrapper_path
        self.python_exec = python_exec
        self.debug_logger = debug_logger
        self.config = config or {}

        # Initialize history logger
        self.history_logger = WrapperHistoryLogger()

        # Initialize response parser
        self.response_parser = ResponseParser()

    @staticmethod
    def _format_event(event: dict) -> str:
        """Format event for logging - simple and informative."""
        event_type = event.get("event")
        timestamp = event.get("timestamp", "")[-12:-4] if event.get("timestamp") else ""  # HH:MM:SS

        # Build formatted message based on event type
        formatted_msg = None

        # Add content type info for stream events
        if event_type == "stream":
            payload = event.get("payload", {})
            content = payload.get("content", [])

            # System events (init, etc)
            if payload.get("subtype") == "init":
                formatted_msg = f"[{timestamp}] {event_type} (init)"
            # Tool use - extract tool names
            elif content and isinstance(content, list):
                first_item = content[0]

                # Tool use
                if "name" in first_item and "input" in first_item:
                    tool_name = first_item.get("name", "unknown")
                    formatted_msg = f"[{timestamp}] {event_type} (tool: {tool_name})"
                # Tool result
                elif "tool_use_id" in first_item and "content" in first_item:
                    result_preview = str(first_item.get("content", ""))[:30]
                    formatted_msg = f"[{timestamp}] {event_type} (result: {result_preview}...)"
                # Text content
                elif "text" in first_item:
                    text_preview = first_item.get("text", "")[:40]
                    formatted_msg = f"[{timestamp}] {event_type} (text: {text_preview}...)"

            # Default for unknown stream content
            if formatted_msg is None:
                formatted_msg = f"[{timestamp}] {event_type} (unknown)"

        # For completion events, include outcome if available
        elif event_type == "run_completed":
            outcome = event.get("outcome", "")[:50]
            formatted_msg = (
                f"[{timestamp}] {event_type} ({outcome})"
                if outcome
                else f"[{timestamp}] {event_type}"
            )

        # Default formatting for other event types
        return (
            formatted_msg
            if formatted_msg
            else (f"[{timestamp}] {event_type}" if timestamp else event_type)
        )

    def _build_command(self, prompt: str, project_path: str, session_id: str | None) -> str:
        """Build JSON command for wrapper (SRP, SSOT)"""
        command = {
            "action": "prompt",
            "prompt": prompt,
            "options": {
                "cwd": project_path,
                "permission_mode": "bypassPermissions",
                "exit_on_complete": True,
            },
        }
        if session_id:
            command["options"]["session_id"] = session_id
        return json.dumps(command) + "\n"

    def _setup_environment(self) -> dict:
        """Setup environment with Claude CLI in PATH and log level (SRP)"""
        import os

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        # Set wrapper log level from config
        wrapper_log_level = self.config.get("logging", {}).get("wrapper", {}).get("level", "INFO")
        env["CLAUDE_WRAPPER_LOG_LEVEL"] = wrapper_log_level

        claude_paths = [
            os.path.expanduser("~/.npm-global/bin"),
            "/usr/local/bin",
            os.path.expanduser("~/.local/bin"),
        ]

        current_path = env.get("PATH", "")
        for path in claude_paths:
            if path not in current_path:
                env["PATH"] = f"{path}:{current_path}"
                current_path = env["PATH"]

        return env

    def _read_wrapper_events(self, process, debug_mode: bool) -> list:
        """Read and parse events from wrapper stdout (SRP)"""
        from pathlib import Path

        events = []

        # Create real-time log file for monitoring
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        realtime_log = log_dir / "wrapper-realtime.log"

        with open(realtime_log, "a", encoding="utf-8") as log_file:
            while True:
                line = process.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                # Write to real-time log for monitoring
                log_file.write(line + "\n")
                log_file.flush()

                try:
                    event = json.loads(line)
                    events.append(event)
                    event_type = event.get("event")

                    if debug_mode:
                        print(f"[WRAPPER DEBUG] {self._format_event(event)}")

                    if event_type in ["shutdown", "auto_shutdown"]:
                        break

                except json.JSONDecodeError:
                    if debug_mode:
                        print(f"[WRAPPER DEBUG] Failed to parse JSON: {line[:100]}")
                    continue

        return events

    def _parse_result_from_events(
        self, events: list, process, stderr: str, operation_type: str = "unknown"
    ) -> dict:
        """Parse final result from events with intelligent error detection (SRP, KISS)"""
        # Build initial result from events or process exit code
        initial_result = self._build_initial_result(events, process, stderr)

        # Add stderr to result for parser analysis
        if stderr:
            initial_result["stderr"] = stderr

        # Use ResponseParser for intelligent error detection
        parsed_result = self.response_parser.parse(initial_result, operation_type)

        # Preserve events and outcome in final result
        parsed_result["events"] = events
        if "outcome" in initial_result:
            parsed_result["outcome"] = initial_result["outcome"]

        return parsed_result

    def _build_initial_result(self, events: list, process, stderr: str) -> dict:
        """Build initial result dict from events or process exit code."""
        # Check for error events first
        for event in events:
            if event.get("event") == "error":
                return {
                    "success": False,
                    "error": event.get("error", "Unknown error"),
                    "events": events,
                }

        # Check for completion events
        for event in events:
            event_type = event.get("event")
            if event_type == "run_completed":
                return {"success": True, "outcome": event.get("outcome"), "events": events}
            if event_type == "run_failed":
                return {
                    "success": False,
                    "error": event.get("error", "Run failed"),
                    "events": events,
                }
            if event_type == "done":
                return {"success": True, "outcome": event.get("outcome"), "events": events}

        # No events - use process exit code
        if process.returncode == 0:
            return {"success": True, "events": events}
        return {
            "success": False,
            "error": f"Process exited with code {process.returncode}",
            "stderr": stderr,
            "events": events,
        }

    def _log_result(
        self, prompt: str, project_path: str, prompt_type: str, result: dict, duration: float
    ):
        """Log result to both history and debug logger (SRP)"""
        from .wrapper_history import CallContext

        self.history_logger.log_call(
            CallContext(prompt=prompt, project_path=project_path, prompt_type=prompt_type),
            result,
            duration,
        )

        if self.debug_logger:
            self.debug_logger.log_wrapper_call(
                prompt_type,
                project_path,
                duration=duration,
                success=result["success"],
                error=result.get("error"),
                response=result
                if self.debug_logger.debug_config.get("log_levels", {}).get("wrapper_responses")
                else None,
            )

    def query(
        self,
        prompt: str,
        project_path: str,
        timeout: int = 600,
        session_id: str | None = None,
        prompt_type: str = "generic",
    ) -> dict:
        """
        Send prompt to Claude via wrapper.

        Args:
            prompt: Prompt for Claude
            project_path: Project working directory
            timeout: Timeout in seconds
            session_id: Optional session ID for continuity
            prompt_type: Type of prompt for logging (analysis, fix_error, fix_test, create_test)

        Returns:
            Dict with result (or error)
        """
        from pathlib import Path

        # Ensure logs directory exists for real-time monitoring
        realtime_log = Path("logs/wrapper-realtime.log")
        realtime_log.parent.mkdir(exist_ok=True)

        command_json = self._build_command(prompt, project_path, session_id)

        start_time = time.time()
        # Show debug output if config enables it
        show_events = self.config.get("logging", {}).get("wrapper", {}).get("show_events", False)
        debug_mode = self.debug_logger is not None and show_events

        if debug_mode:
            print("\n[WRAPPER DEBUG] Starting claude_wrapper")
            print(f"  Wrapper: {self.wrapper_path}")
            print(f"  CWD: {project_path}")
            print(f"  Prompt type: {prompt_type}")

        try:
            env = self._setup_environment()

            if debug_mode:
                print(f"[WRAPPER DEBUG] PATH: {env['PATH'][:200]}...")

            process = subprocess.Popen(
                [self.python_exec, self.wrapper_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=project_path,
                env=env,
            )

            if debug_mode:
                print(f"[WRAPPER DEBUG] Process started (PID: {process.pid})")

            process.stdin.write(command_json)
            process.stdin.flush()

            events = self._read_wrapper_events(process, debug_mode)

            process.stdin.close()
            process.wait(timeout=5)

            stderr = process.stderr.read()

            if debug_mode:
                print(f"[WRAPPER DEBUG] Process completed (exit code: {process.returncode})")

            result = self._parse_result_from_events(events, process, stderr, prompt_type)
            duration = time.time() - start_time

            self._log_result(prompt, project_path, prompt_type, result, duration)

            return result

        except subprocess.TimeoutExpired:
            process.kill()
            duration = time.time() - start_time
            result = {"success": False, "error": f"Timeout after {timeout}s", "events": []}
            self._log_result(prompt, project_path, prompt_type, result, duration)
            return result

        except Exception as e:  # noqa: BLE001 - Catch-all for process errors
            # Process execution errors (subprocess, IO, etc.) - return failed result
            duration = time.time() - start_time
            result = {"success": False, "error": str(e), "events": []}
            self._log_result(prompt, project_path, prompt_type, result, duration)
            return result

    def query_simple(self, prompt: str, project_path: str, timeout: int = 600) -> bool:
        """
        Simplified query that returns True/False.

        Args:
            prompt: Prompt for Claude
            project_path: Project working directory
            timeout: Timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        result = self.query(prompt, project_path, timeout)
        return result.get("success", False)
