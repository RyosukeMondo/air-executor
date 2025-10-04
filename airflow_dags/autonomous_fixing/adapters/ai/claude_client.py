"""
Claude Client - Helper for calling claude_wrapper with JSON protocol.

Provides simple interface to claude_wrapper's streaming JSON protocol.
"""

import json
import subprocess
import time
from typing import Dict, Optional

from .wrapper_history import WrapperHistoryLogger


class ClaudeClient:
    """Simple client for claude_wrapper JSON protocol."""

    def __init__(self, wrapper_path: str, python_exec: str, debug_logger=None):
        """
        Initialize Claude client.

        Args:
            wrapper_path: Path to claude_wrapper.py
            python_exec: Python executable to use
            debug_logger: Optional DebugLogger instance for logging wrapper calls
        """
        self.wrapper_path = wrapper_path
        self.python_exec = python_exec
        self.debug_logger = debug_logger

        # Initialize history logger
        self.history_logger = WrapperHistoryLogger()

    @staticmethod
    def _format_event(event: Dict) -> str:
        """Format event for logging - simple and informative."""
        event_type = event.get('event')
        timestamp = event.get('timestamp', '')[-12:-4] if event.get('timestamp') else ''  # HH:MM:SS

        # Add content type info for stream events
        if event_type == 'stream':
            payload = event.get('payload', {})
            content = payload.get('content', [])

            # System events (init, etc)
            if payload.get('subtype') == 'init':
                return f"[{timestamp}] {event_type} (init)"

            # Tool use - extract tool names
            if content and isinstance(content, list):
                first_item = content[0]

                # Tool use
                if 'name' in first_item and 'input' in first_item:
                    tool_name = first_item.get('name', 'unknown')
                    return f"[{timestamp}] {event_type} (tool: {tool_name})"

                # Tool result
                elif 'tool_use_id' in first_item and 'content' in first_item:
                    result_preview = str(first_item.get('content', ''))[:30]
                    return f"[{timestamp}] {event_type} (result: {result_preview}...)"

                # Text content
                elif 'text' in first_item:
                    text_preview = first_item.get('text', '')[:40]
                    return f"[{timestamp}] {event_type} (text: {text_preview}...)"

            return f"[{timestamp}] {event_type} (unknown)"

        # For completion events, include outcome if available
        elif event_type == 'run_completed':
            outcome = event.get('outcome', '')[:50]
            return f"[{timestamp}] {event_type} ({outcome})" if outcome else f"[{timestamp}] {event_type}"

        return f"[{timestamp}] {event_type}" if timestamp else event_type

    def _build_command(self, prompt: str, project_path: str, session_id: Optional[str]) -> str:
        """Build JSON command for wrapper (SRP, SSOT)"""
        command = {
            "action": "prompt",
            "prompt": prompt,
            "options": {
                "cwd": project_path,
                "permission_mode": "bypassPermissions",
                "exit_on_complete": True
            }
        }
        if session_id:
            command["options"]["session_id"] = session_id
        return json.dumps(command) + "\n"

    def _setup_environment(self) -> dict:
        """Setup environment with Claude CLI in PATH (SRP)"""
        import os
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

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
        events = []

        while True:
            line = process.stdout.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
                events.append(event)
                event_type = event.get('event')

                if debug_mode:
                    print(f"[WRAPPER DEBUG] {self._format_event(event)}")

                if event_type in ['shutdown', 'auto_shutdown']:
                    break

            except json.JSONDecodeError:
                if debug_mode:
                    print(f"[WRAPPER DEBUG] Failed to parse JSON: {line[:100]}")
                continue

        return events

    def _parse_result_from_events(self, events: list, process, stderr: str) -> dict:
        """Parse final result from events (SRP, KISS)"""
        # Check for errors first
        for event in events:
            if event.get('event') == 'error':
                return {
                    'success': False,
                    'error': event.get('error', 'Unknown error'),
                    'events': events
                }

        # Check for completion events
        for event in events:
            event_type = event.get('event')
            if event_type == 'run_completed':
                return {'success': True, 'outcome': event.get('outcome'), 'events': events}
            elif event_type == 'run_failed':
                return {'success': False, 'error': event.get('error', 'Run failed'), 'events': events}
            elif event_type == 'done':
                return {'success': True, 'outcome': event.get('outcome'), 'events': events}

        # No completion event - check process exit code
        if process.returncode == 0:
            return {'success': True, 'events': events}
        else:
            return {
                'success': False,
                'error': f'Process exited with code {process.returncode}',
                'stderr': stderr,
                'events': events
            }

    def _log_result(self, prompt: str, project_path: str, prompt_type: str,
                   result: dict, duration: float):
        """Log result to both history and debug logger (SRP)"""
        self.history_logger.log_call(
            prompt=prompt,
            project_path=project_path,
            prompt_type=prompt_type,
            result=result,
            duration=duration
        )

        if self.debug_logger:
            self.debug_logger.log_wrapper_call(
                prompt_type=prompt_type,
                project=project_path,
                duration=duration,
                success=result['success'],
                error=result.get('error'),
                response=result if self.debug_logger.debug_config.get('log_levels', {}).get('wrapper_responses') else None
            )

    def query(
        self,
        prompt: str,
        project_path: str,
        timeout: int = 600,
        session_id: Optional[str] = None,
        prompt_type: str = "generic"
    ) -> Dict:
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
        command_json = self._build_command(prompt, project_path, session_id)

        start_time = time.time()
        debug_mode = self.debug_logger is not None

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
                env=env
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

            result = self._parse_result_from_events(events, process, stderr)
            duration = time.time() - start_time

            self._log_result(prompt, project_path, prompt_type, result, duration)

            return result

        except subprocess.TimeoutExpired:
            process.kill()
            duration = time.time() - start_time
            result = {'success': False, 'error': f'Timeout after {timeout}s', 'events': []}
            self._log_result(prompt, project_path, prompt_type, result, duration)
            return result

        except Exception as e:
            duration = time.time() - start_time
            result = {'success': False, 'error': str(e), 'events': []}
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
        return result.get('success', False)
