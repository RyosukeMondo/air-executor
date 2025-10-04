"""
Wrapper Call History Logger - Track all claude_wrapper invocations.

Logs every wrapper call with:
- Timestamp
- Project path
- Prompt (full text)
- Result (success/failure)
- Events received
- Git commits created

Enables investigation via: ./scripts/claude_wrapper_history.sh
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class WrapperHistoryLogger:
    """Log all claude_wrapper calls for debugging and investigation."""

    def __init__(self, log_dir: str = "logs/wrapper-history"):
        """
        Initialize history logger.

        Args:
            log_dir: Directory to store history logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current session log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log = self.log_dir / f"wrapper_calls_{timestamp}.jsonl"

        # Also write to latest.jsonl for easy access
        self.latest_log = self.log_dir / "latest.jsonl"

    def log_call(
        self,
        prompt: str,
        project_path: str,
        prompt_type: str,
        result: Dict,
        duration: float,
        git_before: Optional[str] = None,
        git_after: Optional[str] = None,
    ) -> None:
        """
        Log a wrapper call.

        Args:
            prompt: Full prompt text sent to wrapper
            project_path: Working directory for prompt
            prompt_type: Type of prompt (fix_error, fix_test, analysis, etc.)
            result: Result dict from ClaudeClient.query()
            duration: Execution time in seconds
            git_before: Git HEAD commit before call (optional)
            git_after: Git HEAD commit after call (optional)
        """
        events = result.get('events', [])
        event_summary = self._extract_event_summary(events)
        claude_responses = self._extract_claude_responses(events)

        entry = self._build_log_entry(
            prompt=prompt,
            project_path=project_path,
            prompt_type=prompt_type,
            result=result,
            duration=duration,
            git_before=git_before,
            git_after=git_after,
            events=events,
            event_summary=event_summary,
            claude_responses=claude_responses,
        )

        # Write to both files
        self._write_entry(self.current_log, entry)
        self._write_entry(self.latest_log, entry)

    def _build_log_entry(
        self,
        prompt: str,
        project_path: str,
        prompt_type: str,
        result: Dict,
        duration: float,
        git_before: Optional[str],
        git_after: Optional[str],
        events: List[Dict],
        event_summary: List[str],
        claude_responses: List[str],
    ) -> Dict:
        """Build the log entry dictionary."""
        return {
            "timestamp": datetime.now().isoformat(),
            "prompt_type": prompt_type,
            "project": project_path,
            "duration": round(duration, 2),
            "success": result.get('success', False),
            # Prompt (full text for investigation)
            "prompt": prompt,
            "prompt_length": len(prompt),
            # Result details
            "error": result.get('error'),
            "outcome": result.get('outcome'),
            # Events (summary for readability)
            "events": event_summary,
            "event_count": len(events),
            # Claude's actual responses (CRITICAL for debugging)
            "claude_response": " ".join(claude_responses),
            "claude_response_length": sum(len(r) for r in claude_responses),
            # Full event objects (for deep debugging if needed)
            # Store first 3 stream events to save space
            "stream_events_sample": [e for e in events if e.get('event') == 'stream'][:3],
            # Git tracking
            "git": {
                "before": git_before,
                "after": git_after,
                "commit_created": git_before != git_after if (git_before and git_after) else None
            }
        }

    def _extract_event_summary(self, events: List[Dict]) -> List[str]:
        """Extract event types from events list."""
        return [e.get('event') for e in events if 'event' in e]

    def _extract_claude_responses(self, events: List[Dict]) -> List[str]:
        """Extract Claude's text responses from stream events."""
        responses = []
        for event in events:
            if event.get('event') != 'stream':
                continue

            payload = event.get('payload', {})
            self._extract_from_content_array(payload, responses)
            self._extract_from_direct_text(payload, responses)

        return responses

    def _extract_from_content_array(self, payload: Dict, responses: List[str]) -> None:
        """Extract text from content array in payload."""
        content = payload.get('content', [])
        if not isinstance(content, list):
            return

        for item in content:
            if not isinstance(item, dict):
                continue

            text = self._get_text_from_item(item)
            if text:
                responses.append(text)

    def _get_text_from_item(self, item: Dict) -> Optional[str]:
        """Get text from a content item."""
        # Check for text field (AssistantMessage format)
        if 'text' in item:
            return item.get('text', '')

        # Check for type='text' field (alternative format)
        if item.get('type') == 'text':
            return item.get('text')

        return None

    def _extract_from_direct_text(self, payload: Dict, responses: List[str]) -> None:
        """Extract text from direct text field in payload."""
        text = payload.get('text')
        if text:
            responses.append(text)

    def _write_entry(self, log_file: Path, entry: Dict) -> None:
        """Write JSON entry to log file."""
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            # Log errors but don't break execution
            print(f"⚠️  Failed to write wrapper history: {e}")

    def get_recent_calls(self, limit: int = 10) -> List[Dict]:
        """
        Get recent wrapper calls from latest.jsonl.

        Args:
            limit: Number of recent calls to return

        Returns:
            List of call entries (newest first)
        """
        if not self.latest_log.exists():
            return []

        calls = []
        try:
            with open(self.latest_log, 'r') as f:
                for line in f:
                    if line.strip():
                        calls.append(json.loads(line))
        except Exception:
            pass

        # Return newest first, limited
        return calls[-limit:][::-1]

    def get_failures(self, limit: int = 10) -> List[Dict]:
        """Get recent failed calls."""
        recent = self.get_recent_calls(limit * 2)  # Look at more to find failures
        failures = [c for c in recent if not c.get('success', True)]
        return failures[:limit]

    def get_successes(self, limit: int = 10) -> List[Dict]:
        """Get recent successful calls."""
        recent = self.get_recent_calls(limit * 2)
        successes = [c for c in recent if c.get('success', False)]
        return successes[:limit]

    def get_calls_by_project(self, project_path: str, limit: int = 10) -> List[Dict]:
        """Get recent calls for specific project."""
        recent = self.get_recent_calls(limit * 3)
        matches = [c for c in recent if c.get('project') == project_path]
        return matches[:limit]

    def get_calls_by_type(self, prompt_type: str, limit: int = 10) -> List[Dict]:
        """Get recent calls of specific type."""
        recent = self.get_recent_calls(limit * 3)
        matches = [c for c in recent if c.get('prompt_type') == prompt_type]
        return matches[:limit]

    def print_call_summary(self, call: Dict, verbose: bool = False) -> None:
        """
        Print human-readable summary of a wrapper call.

        Args:
            call: Call entry from history
            verbose: If True, show full prompt and events
        """
        self._print_header(call)
        self._print_basic_info(call)
        self._print_git_info(call)
        self._print_result(call)
        self._print_events(call)

        if verbose:
            self._print_verbose_details(call)

    def _print_header(self, call: Dict) -> None:
        """Print call header with timestamp and status."""
        timestamp = call.get('timestamp', 'Unknown time')
        success = '✅' if call.get('success') else '❌'
        print(f"\n{success} {timestamp}")

    def _print_basic_info(self, call: Dict) -> None:
        """Print basic call information."""
        print(f"  Type: {call.get('prompt_type')}")
        print(f"  Project: {call.get('project')}")
        print(f"  Duration: {call.get('duration')}s")

    def _print_git_info(self, call: Dict) -> None:
        """Print git commit information."""
        git = call.get('git', {})
        if git.get('commit_created'):
            before = git.get('before', '')[:8]
            after = git.get('after', '')[:8]
            print(f"  ✅ Git commit: {before} → {after}")
        elif git.get('commit_created') is False:
            before = git.get('before', '')[:8]
            print(f"  ❌ No commit: {before} (unchanged)")

    def _print_result(self, call: Dict) -> None:
        """Print call result or error."""
        if call.get('success'):
            outcome = call.get('outcome', 'ok')
            print(f"  Result: {outcome}")
        else:
            error = call.get('error', 'Unknown error')
            print(f"  Error: {error}")

    def _print_events(self, call: Dict) -> None:
        """Print event summary."""
        events = call.get('events', [])
        print(f"  Events: {', '.join(events)}")

    def _print_verbose_details(self, call: Dict) -> None:
        """Print detailed prompt and response in verbose mode."""
        self._print_prompt_details(call)
        self._print_response_details(call)

    def _print_prompt_details(self, call: Dict) -> None:
        """Print prompt details in verbose mode."""
        print(f"\n  Prompt ({call.get('prompt_length')} chars):")
        print("  " + "-" * 76)

        prompt = call.get('prompt', '')
        lines = prompt.split('\n')
        for line in lines[:20]:  # First 20 lines
            print(f"  {line}")

        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more lines)")

        print("  " + "-" * 76)

    def _print_response_details(self, call: Dict) -> None:
        """Print Claude response details in verbose mode."""
        response = call.get('claude_response', '')
        response_len = call.get('claude_response_length', 0)

        if not response:
            print(f"\n  ⚠️  No Claude response captured (response length: {response_len})")
            return

        print(f"\n  Claude Response ({response_len} chars):")
        print("  " + "-" * 76)

        lines = response.split('\n')
        for line in lines[:30]:  # First 30 lines
            print(f"  {line}")

        if len(lines) > 30:
            print(f"  ... ({len(lines) - 30} more lines)")

        print("  " + "-" * 76)

    def cleanup_old_logs(self, keep_days: int = 7) -> None:
        """
        Clean up old log files.

        Args:
            keep_days: Number of days to keep logs
        """
        import time
        cutoff = time.time() - (keep_days * 86400)

        for log_file in self.log_dir.glob("wrapper_calls_*.jsonl"):
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                print(f"Cleaned up old log: {log_file.name}")
