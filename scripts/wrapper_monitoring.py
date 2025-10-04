"""
Monitoring and event tracking for claude_wrapper.py

Extracted to reduce file size and complexity of main wrapper module.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class MonitoringTracker:
    """Tracks phase and tool execution state for real-time monitoring."""

    def __init__(self):
        self.current_phase: Optional[str] = None
        self.tool_stats = {"total": 0, "completed": 0, "active": None}

    def reset_tools(self) -> None:
        """Reset tool tracking for new run."""
        self.tool_stats = {"total": 0, "completed": 0, "active": None}

    def start_tool(self, tool_name: str) -> Dict[str, Any]:
        """Track tool start and return event data."""
        self.tool_stats["total"] += 1
        self.tool_stats["active"] = tool_name
        return {
            "tool": tool_name,
            "progress": f"{self.tool_stats['completed']}/{self.tool_stats['total']}",
        }

    def complete_tool(self) -> Dict[str, Any]:
        """Track tool completion and return event data."""
        self.tool_stats["completed"] += 1
        completed_tool = self.tool_stats["active"]
        self.tool_stats["active"] = None
        return {
            "tool": completed_tool,
            "progress": f"{self.tool_stats['completed']}/{self.tool_stats['total']}",
        }

    @staticmethod
    def detect_phase(prompt: str) -> Optional[str]:
        """Detect execution phase from prompt content."""
        prompt_lower = prompt.lower()
        if "discover" in prompt_lower and "test" in prompt_lower:
            return "P1: Test Discovery"
        elif "fix_error" in prompt_lower or "linting" in prompt_lower or "type" in prompt_lower:
            return "P1: Static Analysis"
        elif "fix_test" in prompt_lower or "test failure" in prompt_lower:
            return "P2: Test Fixing"
        elif "coverage" in prompt_lower:
            return "P3: Coverage"
        elif "e2e" in prompt_lower or "integration" in prompt_lower:
            return "P4: E2E Tests"
        return None

    @staticmethod
    def detect_tool_event(serialised: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect tool execution events from stream messages."""
        msg_type = serialised.get("message_type", "")

        # Tool started
        if msg_type == "ToolUseBlock" or "tool" in serialised.get("type", ""):
            tool_name = serialised.get("name") or serialised.get("tool_name")
            if tool_name:
                return {
                    "event_type": "tool_started",
                    "tool": tool_name,
                    "details": serialised.get("input", {}),
                }

        # Tool completed (result received)
        if msg_type == "ToolResultBlock" or "result" in serialised.get("type", ""):
            return {"event_type": "tool_completed"}

        return None

    @staticmethod
    def detect_limit_message(serialised_message: Dict[str, Any]) -> Optional[str]:
        """Detect textual rate/usage limit notice within a Claude SDK stream payload."""
        import re

        candidates: list[str] = []

        def push(value: Any) -> None:
            if isinstance(value, str) and value:
                candidates.append(value)

        push(serialised_message.get("message"))
        push(serialised_message.get("error"))
        push(serialised_message.get("reason"))

        payload = serialised_message.get("payload")
        if isinstance(payload, dict):
            for key in ("result", "message", "error", "details", "reason"):
                push(payload.get(key))

        # shallow scan of nested content arrays
        content = serialised_message.get("content")
        if isinstance(content, list):
            for item in content[:5]:
                if isinstance(item, dict):
                    push(item.get("text"))

        pattern = re.compile(r"(limit\s*reached|rate\s*limit|usage\s*limit)", re.IGNORECASE)
        for text in candidates:
            if pattern.search(text):
                return text
        return None

    @staticmethod
    def extract_session_id(serialised_message: Dict[str, Any]) -> Optional[str]:
        """Extract session ID from stream message."""
        session_id = serialised_message.get("session_id")
        if isinstance(session_id, str):
            return session_id

        metadata = serialised_message.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("session_id"), str):
            return metadata["session_id"]

        return None


def emit_phase_detected(
    output_func, run_context: Dict[str, Any], phase: str, timestamp: Optional[str] = None
) -> None:
    """Emit phase_detected event."""
    output_func(
        {
            "event": "phase_detected",
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "run_id": run_context["id"],
            "phase": phase,
        }
    )


def emit_tool_event(
    output_func,
    event_type: str,
    run_context: Dict[str, Any],
    tool_data: Dict[str, Any],
    timestamp: Optional[str] = None,
) -> None:
    """Emit tool_started or tool_completed event."""
    output_func(
        {
            "event": event_type,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "run_id": run_context["id"],
            **tool_data,
        }
    )


def emit_limit_notice(
    output_func, run_context: Dict[str, Any], message: str, timestamp: Optional[str] = None
) -> None:
    """Emit limit_notice event."""
    output_func(
        {
            "event": "limit_notice",
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "run_id": run_context["id"],
            "message": message,
        }
    )


def emit_run_completed(
    output_func, run_context: Dict[str, Any], reason: str = "ok", **extra_fields
) -> None:
    """Emit run_completed event."""
    output_func(
        {
            "event": "run_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_context["id"],
            "version": 1,
            "outcome": "completed",
            "reason": reason,
            "tags": extra_fields.get("tags", []),
            **{k: v for k, v in extra_fields.items() if k != "tags"},
        }
    )


def emit_auto_shutdown(output_func, run_context: Dict[str, Any]) -> None:
    """Emit auto_shutdown event."""
    output_func(
        {
            "event": "auto_shutdown",
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "exit_on_complete",
            "run_id": run_context["id"],
            "version": 1,
            "outcome": "shutdown",
            "tags": [],
        }
    )


def emit_run_failed(
    output_func,
    run_context: Dict[str, Any],
    reason: str,
    error: str,
    traceback_str: Optional[str] = None,
) -> None:
    """Emit run_failed event."""
    event_data = {
        "event": "run_failed",
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": run_context["id"],
        "version": 1,
        "outcome": "failed",
        "reason": reason,
        "tags": [],
        "error": error,
    }
    if traceback_str:
        event_data["traceback"] = traceback_str
    output_func(event_data)


def emit_run_terminated(output_func, run_context: Dict[str, Any]) -> None:
    """Emit run_terminated event (broken pipe)."""
    output_func(
        {
            "event": "run_terminated",
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_context["id"],
            "reason": "broken_pipe",
            "version": 1,
            "outcome": "terminated",
            "tags": [],
        }
    )


def emit_state(output_func, state: str, last_session_id: Optional[str]) -> None:
    """Emit state event."""
    output_func(
        {
            "event": "state",
            "timestamp": datetime.utcnow().isoformat(),
            "state": state,
            "last_session_id": last_session_id,
        }
    )
