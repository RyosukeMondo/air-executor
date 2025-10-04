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
        # Build JSON command
        command = {
            "action": "prompt",
            "prompt": prompt,
            "options": {
                "cwd": project_path,
                "permission_mode": "bypassPermissions",  # Auto-approve for automation
                "exit_on_complete": True  # Shutdown wrapper after task completes
            }
        }

        if session_id:
            command["options"]["session_id"] = session_id

        # Convert to JSON string with newline
        command_json = json.dumps(command) + "\n"

        # Track timing
        start_time = time.time()

        # Enable detailed logging for debugging
        debug_mode = self.debug_logger is not None
        if debug_mode:
            print("\n[WRAPPER DEBUG] Starting claude_wrapper")
            print(f"  Wrapper: {self.wrapper_path}")
            print(f"  Python: {self.python_exec}")
            print(f"  CWD: {project_path}")
            print(f"  Prompt type: {prompt_type}")
            print(f"  Prompt (first 100 chars): {prompt[:100]}...")

        try:
            # Set up environment with Claude CLI in PATH
            import os
            env = os.environ.copy()

            # CRITICAL: Ensure unbuffered Python output
            env["PYTHONUNBUFFERED"] = "1"

            # Add common locations for Claude CLI to PATH
            claude_paths = [
                os.path.expanduser("~/.npm-global/bin"),  # npm global
                "/usr/local/bin",  # macOS/Linux system
                os.path.expanduser("~/.local/bin"),  # pip user install
            ]

            current_path = env.get("PATH", "")
            for path in claude_paths:
                if path not in current_path:
                    env["PATH"] = f"{path}:{current_path}"
                    current_path = env["PATH"]

            if debug_mode:
                print(f"[WRAPPER DEBUG] PATH: {env['PATH'][:200]}...")
                print(f"[WRAPPER DEBUG] PYTHONUNBUFFERED: {env.get('PYTHONUNBUFFERED')}")

            # Run wrapper with JSON on stdin
            process = subprocess.Popen(
                [self.python_exec, self.wrapper_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered for real-time output
                cwd=project_path,
                env=env  # Pass environment with Claude CLI in PATH
            )

            if debug_mode:
                print(f"[WRAPPER DEBUG] Process started (PID: {process.pid})")
                print("[WRAPPER DEBUG] Sending JSON command...")

            # Send command and keep stdin open to avoid EOF detection
            # Wrapper needs stdin to stay open while Claude executes
            process.stdin.write(command_json)
            process.stdin.flush()

            if debug_mode:
                print("[WRAPPER DEBUG] Command sent, reading events...")

            # Read events from stdout as they stream
            events = []
            event_types_seen = []

            # Read line by line until shutdown
            while True:
                line = process.stdout.readline()
                if not line:
                    break  # EOF

                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    events.append(event)
                    event_type = event.get('event')
                    event_types_seen.append(event_type)

                    if debug_mode:
                        print(f"[WRAPPER DEBUG] {self._format_event(event)}")

                    # Stop reading when wrapper shuts down
                    if event_type in ['shutdown', 'auto_shutdown']:
                        break

                except json.JSONDecodeError:
                    if debug_mode:
                        print(f"[WRAPPER DEBUG] Failed to parse JSON: {line[:100]}")
                    continue

            # Close stdin and wait for process to finish
            process.stdin.close()
            process.wait(timeout=5)

            # Read any remaining stderr
            stderr = process.stderr.read()

            if debug_mode:
                print(f"[WRAPPER DEBUG] Process completed (exit code: {process.returncode})")
                print(f"[WRAPPER DEBUG] Events received: {', '.join(event_types_seen)}")
                print(f"[WRAPPER DEBUG] Stderr length: {len(stderr)} chars")

            # Check for errors in events
            for event in events:
                if event.get('event') == 'error':
                    return {
                        'success': False,
                        'error': event.get('error', 'Unknown error'),
                        'events': events
                    }

            # Calculate duration
            duration = time.time() - start_time

            # Check for completion (wrapper sends 'run_completed', not 'done')
            result = None
            for event in events:
                event_type = event.get('event')
                # Check for successful completion
                if event_type == 'run_completed':
                    result = {
                        'success': True,
                        'outcome': event.get('outcome'),
                        'events': events
                    }
                    break
                # Check for failures
                elif event_type == 'run_failed':
                    result = {
                        'success': False,
                        'error': event.get('error', 'Run failed'),
                        'events': events
                    }
                    break
                # Legacy 'done' event (kept for backward compatibility)
                elif event_type == 'done':
                    result = {
                        'success': True,
                        'outcome': event.get('outcome'),
                        'events': events
                    }
                    break

            # If no completion event, check process exit
            if result is None:
                if process.returncode == 0:
                    # Wrapper exited cleanly - assume success
                    result = {
                        'success': True,
                        'events': events
                    }
                else:
                    result = {
                        'success': False,
                        'error': f'Process exited with code {process.returncode}',
                        'stderr': stderr,
                        'events': events
                    }

            # Log to history (ALWAYS - critical for investigation)
            self.history_logger.log_call(
                prompt=prompt,
                project_path=project_path,
                prompt_type=prompt_type,
                result=result,
                duration=duration
            )

            # Log wrapper call (optional debug logger)
            if self.debug_logger:
                self.debug_logger.log_wrapper_call(
                    prompt_type=prompt_type,
                    project=project_path,
                    duration=duration,
                    success=result['success'],
                    error=result.get('error'),
                    response=result if self.debug_logger.debug_config.get('log_levels', {}).get('wrapper_responses') else None
                )

            return result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            process.kill()

            result = {
                'success': False,
                'error': f'Timeout after {timeout}s',
                'events': []
            }

            # Log to history
            self.history_logger.log_call(
                prompt=prompt,
                project_path=project_path,
                prompt_type=prompt_type,
                result=result,
                duration=duration
            )

            # Log timeout
            if self.debug_logger:
                self.debug_logger.log_wrapper_call(
                    prompt_type=prompt_type,
                    project=project_path,
                    duration=duration,
                    success=False,
                    error=f'Timeout after {timeout}s'
                )

            return result

        except Exception as e:
            duration = time.time() - start_time

            result = {
                'success': False,
                'error': str(e),
                'events': []
            }

            # Log to history
            self.history_logger.log_call(
                prompt=prompt,
                project_path=project_path,
                prompt_type=prompt_type,
                result=result,
                duration=duration
            )

            # Log exception
            if self.debug_logger:
                self.debug_logger.log_wrapper_call(
                    prompt_type=prompt_type,
                    project=project_path,
                    duration=duration,
                    success=False,
                    error=str(e)
                )

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
