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
    def _check_phase_keywords(prompt_lower: str, keywords: tuple) -> bool:
        """Check if all keywords are present in prompt."""
        return all(kw in prompt_lower for kw in keywords)

    @staticmethod
    def _check_any_phase_keywords(prompt_lower: str, keywords: tuple) -> bool:
        """Check if any keyword is present in prompt."""
        return any(kw in prompt_lower for kw in keywords)

    @staticmethod
    def detect_phase(prompt: str) -> Optional[str]:
        """Detect execution phase from prompt content."""
        prompt_lower = prompt.lower()

        # Phase detection rules: (check_func, keywords, phase_name)
        phase_rules = [
            (MonitoringTracker._check_phase_keywords, ("discover", "test"), "P1: Test Discovery"),
            (
                MonitoringTracker._check_any_phase_keywords,
                ("fix_error", "linting", "type"),
                "P1: Static Analysis",
            ),
            (
                MonitoringTracker._check_any_phase_keywords,
                ("fix_test", "test failure"),
                "P2: Test Fixing",
            ),
            (MonitoringTracker._check_any_phase_keywords, ("coverage",), "P3: Coverage"),
            (MonitoringTracker._check_any_phase_keywords, ("e2e", "integration"), "P4: E2E Tests"),
        ]

        for check_func, keywords, phase_name in phase_rules:
            if check_func(prompt_lower, keywords):
                return phase_name

        return None

    @staticmethod
    def _is_tool_started(msg_type: str, serialised_type: str) -> bool:
        """Check if message indicates tool started."""
        return msg_type == "ToolUseBlock" or "tool" in serialised_type

    @staticmethod
    def _is_tool_completed(msg_type: str, serialised_type: str) -> bool:
        """Check if message indicates tool completed."""
        return msg_type == "ToolResultBlock" or "result" in serialised_type

    @staticmethod
    def _extract_tool_name(serialised: Dict[str, Any]) -> Optional[str]:
        """Extract tool name from serialised message."""
        return serialised.get("name") or serialised.get("tool_name")

    @staticmethod
    def detect_tool_event(serialised: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect tool execution events from stream messages."""
        msg_type = serialised.get("message_type", "")
        serialised_type = serialised.get("type", "")

        # Tool started
        if MonitoringTracker._is_tool_started(msg_type, serialised_type):
            tool_name = MonitoringTracker._extract_tool_name(serialised)
            if tool_name:
                return {
                    "event_type": "tool_started",
                    "tool": tool_name,
                    "details": serialised.get("input", {}),
                }

        # Tool completed (result received)
        if MonitoringTracker._is_tool_completed(msg_type, serialised_type):
            return {"event_type": "tool_completed"}

        return None

    @staticmethod
    def _collect_top_level_strings(serialised_message: Dict[str, Any]) -> list[str]:
        """Collect top-level string values from message."""
        candidates = []
        for key in ("message", "error", "reason"):
            value = serialised_message.get(key)
            if isinstance(value, str) and value:
                candidates.append(value)
        return candidates

    @staticmethod
    def _collect_payload_strings(payload: Dict[str, Any]) -> list[str]:
        """Collect string values from payload dict."""
        candidates = []
        for key in ("result", "message", "error", "details", "reason"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                candidates.append(value)
        return candidates

    @staticmethod
    def _collect_content_strings(content: list) -> list[str]:
        """Collect text strings from content array."""
        candidates = []
        for item in content[:5]:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text:
                    candidates.append(text)
        return candidates

    @staticmethod
    def _search_for_limit_pattern(candidates: list[str]) -> Optional[str]:
        """Search for limit-related patterns in candidate strings."""
        import re

        pattern = re.compile(r"(limit\s*reached|rate\s*limit|usage\s*limit)", re.IGNORECASE)
        for text in candidates:
            if pattern.search(text):
                return text
        return None

    @staticmethod
    def detect_limit_message(serialised_message: Dict[str, Any]) -> Optional[str]:
        """Detect textual rate/usage limit notice within a Claude SDK stream payload."""
        candidates: list[str] = []

        # Collect from top-level fields
        candidates.extend(MonitoringTracker._collect_top_level_strings(serialised_message))

        # Collect from payload
        payload = serialised_message.get("payload")
        if isinstance(payload, dict):
            candidates.extend(MonitoringTracker._collect_payload_strings(payload))

        # Collect from content array
        content = serialised_message.get("content")
        if isinstance(content, list):
            candidates.extend(MonitoringTracker._collect_content_strings(content))

        return MonitoringTracker._search_for_limit_pattern(candidates)

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
