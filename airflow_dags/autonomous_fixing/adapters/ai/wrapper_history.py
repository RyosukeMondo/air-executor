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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class GitContext:
    """Git commit context for wrapper calls."""

    before: str | None = None
    after: str | None = None


@dataclass
class CallContext:
    """Context for a wrapper call."""

    prompt: str
    project_path: str
    prompt_type: str


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
        context: CallContext,
        result: dict,
        duration: float,
        git_context: GitContext | None = None,
    ) -> None:
        """
        Log a wrapper call.

        Args:
            context: Call context (prompt, project_path, prompt_type)
            result: Result dict from ClaudeClient.query()
            duration: Execution time in seconds
            git_context: Git context (before/after commits), optional
        """
        if git_context is None:
            git_context = GitContext()

        events = result.get("events", [])
        entry = self._create_log_entry(context, result, duration, git_context, events)
        self._write_log_entries(entry)

    def _create_log_entry(
        self,
        context: CallContext,
        result: dict,
        duration: float,
        git_context: GitContext,
        events: list[dict],
    ) -> dict:
        """Create complete log entry from call parameters."""
        event_summary = self._extract_event_summary(events)
        claude_responses = self._extract_claude_responses(events)

        entry = self._build_base_entry(
            context.prompt, context.project_path, context.prompt_type, duration
        )
        entry.update(self._build_result_fields(result))
        entry.update(self._build_event_fields(events, event_summary, claude_responses))
        entry["git"] = self._build_git_fields(git_context.before, git_context.after)

        return entry

    def _build_base_entry(
        self, prompt: str, project_path: str, prompt_type: str, duration: float
    ) -> dict:
        """Build base entry fields."""
        return {
            "timestamp": datetime.now().isoformat(),
            "prompt_type": prompt_type,
            "project": project_path,
            "duration": round(duration, 2),
            "prompt": prompt,
            "prompt_length": len(prompt),
        }

    def _build_result_fields(self, result: dict) -> dict:
        """Build result-related fields."""
        return {
            "success": result.get("success", False),
            "error": result.get("error"),
            "outcome": result.get("outcome"),
        }

    def _build_event_fields(
        self, events: list[dict], event_summary: list[str], claude_responses: list[str]
    ) -> dict:
        """Build event-related fields."""
        return {
            "events": event_summary,
            "event_count": len(events),
            "claude_response": " ".join(claude_responses),
            "claude_response_length": sum(len(r) for r in claude_responses),
            "stream_events_sample": [e for e in events if e.get("event") == "stream"][:3],
        }

    def _build_git_fields(self, git_before: str | None, git_after: str | None) -> dict:
        """Build git tracking fields."""
        commit_created = None
        if git_before and git_after:
            commit_created = git_before != git_after

        return {
            "before": git_before,
            "after": git_after,
            "commit_created": commit_created,
        }

    def _write_log_entries(self, entry: dict) -> None:
        """Write entry to both current and latest log files."""
        self._write_entry(self.current_log, entry)
        self._write_entry(self.latest_log, entry)

    def _extract_event_summary(self, events: list[dict]) -> list[str]:
        """Extract event types from events list."""
        return [e.get("event") for e in events if "event" in e]

    def _extract_claude_responses(self, events: list[dict]) -> list[str]:
        """Extract Claude's text responses from stream events."""
        responses = []
        for event in events:
            if event.get("event") == "stream":
                payload = event.get("payload", {})
                self._extract_responses_from_payload(payload, responses)
        return responses

    def _extract_responses_from_payload(self, payload: dict, responses: list[str]) -> None:
        """Extract all responses from a payload."""
        self._extract_from_content_array(payload, responses)
        self._extract_from_direct_text(payload, responses)

    def _extract_from_content_array(self, payload: dict, responses: list[str]) -> None:
        """Extract text from content array in payload."""
        content = payload.get("content", [])
        if not isinstance(content, list):
            return

        for item in content:
            if isinstance(item, dict):
                text = self._get_text_from_item(item)
                if text:
                    responses.append(text)

    def _get_text_from_item(self, item: dict) -> str | None:
        """Get text from a content item."""
        if "text" in item:
            return item.get("text", "")
        if item.get("type") == "text":
            return item.get("text")
        return None

    def _extract_from_direct_text(self, payload: dict, responses: list[str]) -> None:
        """Extract text from direct text field in payload."""
        text = payload.get("text")
        if text:
            responses.append(text)

    def _write_entry(self, log_file: Path, entry: dict) -> None:
        """Write JSON entry to log file."""
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # Log errors but don't break execution
            print(f"⚠️  Failed to write wrapper history: {e}")

    def get_recent_calls(self, limit: int = 10) -> list[dict]:
        """
        Get recent wrapper calls from latest.jsonl.

        Args:
            limit: Number of recent calls to return

        Returns:
            List of call entries (newest first)
        """
        if not self.latest_log.exists():
            return []

        calls = self._read_all_calls()
        return self._get_newest_calls(calls, limit)

    def _read_all_calls(self) -> list[dict]:
        """Read all calls from latest log file."""
        calls = []
        try:
            with open(self.latest_log, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        calls.append(json.loads(line))
        except Exception:
            pass
        return calls

    def _get_newest_calls(self, calls: list[dict], limit: int) -> list[dict]:
        """Get newest N calls from list."""
        return calls[-limit:][::-1]

    def get_failures(self, limit: int = 10) -> list[dict]:
        """Get recent failed calls."""
        recent = self.get_recent_calls(limit * 2)  # Look at more to find failures
        failures = [c for c in recent if not c.get("success", True)]
        return failures[:limit]

    def get_successes(self, limit: int = 10) -> list[dict]:
        """Get recent successful calls."""
        recent = self.get_recent_calls(limit * 2)
        successes = [c for c in recent if c.get("success", False)]
        return successes[:limit]

    def get_calls_by_project(self, project_path: str, limit: int = 10) -> list[dict]:
        """Get recent calls for specific project."""
        recent = self.get_recent_calls(limit * 3)
        matches = [c for c in recent if c.get("project") == project_path]
        return matches[:limit]

    def get_calls_by_type(self, prompt_type: str, limit: int = 10) -> list[dict]:
        """Get recent calls of specific type."""
        recent = self.get_recent_calls(limit * 3)
        matches = [c for c in recent if c.get("prompt_type") == prompt_type]
        return matches[:limit]

    def print_call_summary(self, call: dict, verbose: bool = False) -> None:
        """
        Print human-readable summary of a wrapper call.

        Args:
            call: Call entry from history
            verbose: If True, show full prompt and events
        """
        self._print_basic_summary(call)
        if verbose:
            self._print_verbose_details(call)

    def _print_basic_summary(self, call: dict) -> None:
        """Print basic call summary."""
        self._print_header(call)
        self._print_basic_info(call)
        self._print_git_info(call)
        self._print_result(call)
        self._print_events(call)

    def _print_header(self, call: dict) -> None:
        """Print call header with timestamp and status."""
        timestamp = call.get("timestamp", "Unknown time")
        success = "✅" if call.get("success") else "❌"
        print(f"\n{success} {timestamp}")

    def _print_basic_info(self, call: dict) -> None:
        """Print basic call information."""
        print(f"  Type: {call.get('prompt_type')}")
        print(f"  Project: {call.get('project')}")
        print(f"  Duration: {call.get('duration')}s")

    def _print_git_info(self, call: dict) -> None:
        """Print git commit information."""
        git = call.get("git", {})
        commit_created = git.get("commit_created")

        if commit_created:
            self._print_commit_created(git)
        elif commit_created is False:
            self._print_no_commit(git)

    def _print_commit_created(self, git: dict) -> None:
        """Print message for created commit."""
        before = git.get("before", "")[:8]
        after = git.get("after", "")[:8]
        print(f"  ✅ Git commit: {before} → {after}")

    def _print_no_commit(self, git: dict) -> None:
        """Print message for no commit."""
        before = git.get("before", "")[:8]
        print(f"  ❌ No commit: {before} (unchanged)")

    def _print_result(self, call: dict) -> None:
        """Print call result or error."""
        if call.get("success"):
            outcome = call.get("outcome", "ok")
            print(f"  Result: {outcome}")
        else:
            error = call.get("error", "Unknown error")
            print(f"  Error: {error}")

    def _print_events(self, call: dict) -> None:
        """Print event summary."""
        events = call.get("events", [])
        print(f"  Events: {', '.join(events)}")

    def _print_verbose_details(self, call: dict) -> None:
        """Print detailed prompt and response in verbose mode."""
        self._print_prompt_details(call)
        self._print_response_details(call)

    def _print_prompt_details(self, call: dict) -> None:
        """Print prompt details in verbose mode."""
        prompt = call.get("prompt", "")
        prompt_len = call.get("prompt_length", 0)

        print(f"\n  Prompt ({prompt_len} chars):")
        print("  " + "-" * 76)

        self._print_truncated_lines(prompt, max_lines=20)

        print("  " + "-" * 76)

    def _print_truncated_lines(self, text: str, max_lines: int) -> None:
        """Print first N lines of text with truncation indicator."""
        lines = text.split("\n")
        for line in lines[:max_lines]:
            print(f"  {line}")

        if len(lines) > max_lines:
            print(f"  ... ({len(lines) - max_lines} more lines)")

    def _print_response_details(self, call: dict) -> None:
        """Print Claude response details in verbose mode."""
        response = call.get("claude_response", "")
        response_len = call.get("claude_response_length", 0)

        if not response:
            print(f"\n  ⚠️  No Claude response captured (response length: {response_len})")
            return

        print(f"\n  Claude Response ({response_len} chars):")
        print("  " + "-" * 76)

        self._print_truncated_lines(response, max_lines=30)

        print("  " + "-" * 76)

    def cleanup_old_logs(self, keep_days: int = 7) -> None:
        """
        Clean up old log files.

        Args:
            keep_days: Number of days to keep logs
        """
        import time

        cutoff = time.time() - (keep_days * 86400)
        self._remove_old_log_files(cutoff)

    def _remove_old_log_files(self, cutoff: float) -> None:
        """Remove log files older than cutoff timestamp."""
        for log_file in self.log_dir.glob("wrapper_calls_*.jsonl"):
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                print(f"Cleaned up old log: {log_file.name}")
