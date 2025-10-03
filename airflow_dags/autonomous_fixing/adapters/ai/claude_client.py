"""
Claude Client - Helper for calling claude_wrapper with JSON protocol.

Provides simple interface to claude_wrapper's streaming JSON protocol.
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from typing import Dict, Optional


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
                "permission_mode": "bypassPermissions"  # Auto-approve for automation
            }
        }

        if session_id:
            command["options"]["session_id"] = session_id

        # Convert to JSON string with newline
        command_json = json.dumps(command) + "\n"

        # Track timing
        start_time = time.time()

        try:
            # Run wrapper with JSON on stdin
            process = subprocess.Popen(
                [self.python_exec, self.wrapper_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_path
            )

            # Send command and shutdown
            stdout, stderr = process.communicate(
                input=command_json + json.dumps({"action": "shutdown"}) + "\n",
                timeout=timeout
            )

            # Parse response lines (streaming JSON)
            events = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError:
                        continue

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

            # Check for completion
            result = None
            for event in events:
                if event.get('event') == 'done':
                    result = {
                        'success': True,
                        'outcome': event.get('outcome'),
                        'events': events
                    }
                    break

            # If no done event, check process exit
            if result is None:
                if process.returncode == 0:
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

            # Log wrapper call
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
                'error': f'Timeout after {timeout}s'
            }

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
                'error': str(e)
            }

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
