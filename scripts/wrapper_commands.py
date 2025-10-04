"""
Command handling for claude_wrapper.py

Extracted to reduce main file size and improve maintainability.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def handle_prompt_command(
    wrapper,
    payload: Dict[str, Any],
    build_options_func,
    start_query_func,
) -> None:
    """Handle 'prompt' command."""
    if wrapper.current_run is not None:
        wrapper.output_json(
            {
                "event": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Agent is busy",
                "state": wrapper.state,
                "active_run_id": wrapper.current_run.get("id") if wrapper.current_run else None,
            }
        )
        return

    prompt = payload.get("prompt")
    if not prompt:
        wrapper.output_json(
            {
                "event": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Missing prompt",
            }
        )
        return

    run_id = payload.get("run_id") or str(uuid.uuid4())
    options_dict = payload.get("options") or {}
    exit_on_complete = bool(options_dict.get("exit_on_complete"))

    try:
        options = build_options_func(options_dict)
    except Exception as exc:
        logger.exception("Failed to construct ClaudeCodeOptions")
        wrapper.output_json(
            {
                "event": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Invalid ClaudeCodeOptions",
                "details": str(exc),
            }
        )
        return

    await start_query_func(run_id, prompt, options, options_dict, exit_on_complete)


async def handle_cancel_command(wrapper, payload: Dict[str, Any]) -> None:
    """Handle 'cancel' command."""
    requested_run_id = payload.get("run_id")
    if not wrapper.current_run:
        wrapper.output_json(
            {
                "event": "cancel_ignored",
                "reason": "no_active_run",
                "timestamp": datetime.utcnow().isoformat(),
                "requested_run_id": requested_run_id,
            }
        )
        return

    if requested_run_id and requested_run_id != wrapper.current_run.get("id"):
        wrapper.output_json(
            {
                "event": "cancel_ignored",
                "reason": "run_id_mismatch",
                "timestamp": datetime.utcnow().isoformat(),
                "requested_run_id": requested_run_id,
                "active_run_id": wrapper.current_run.get("id"),
            }
        )
        return

    cancel_scope = wrapper.current_run.get("cancel_scope")
    if cancel_scope is None:
        wrapper.output_json(
            {
                "event": "cancel_ignored",
                "reason": "not_cancellable",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return

    cancel_scope.cancel()
    wrapper.output_json(
        {
            "event": "cancel_requested",
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": wrapper.current_run.get("id"),
        }
    )


def handle_status_command(wrapper) -> None:
    """Handle 'status' command."""
    status_payload: Dict[str, Any] = {
        "event": "status",
        "timestamp": datetime.utcnow().isoformat(),
        "state": wrapper.state,
        "last_session_id": wrapper.last_session_id,
    }
    if wrapper.current_run:
        status_payload["active_run"] = {
            key: value for key, value in wrapper.current_run.items() if key not in {"cancel_scope"}
        }
    wrapper.output_json(status_payload)


def handle_shutdown_command(wrapper) -> None:
    """Handle 'shutdown' command."""
    logger.info("Shutdown command received")
    wrapper.shutdown_requested = True
    if wrapper.current_run and wrapper.current_run.get("cancel_scope") is not None:
        wrapper.current_run["cancel_scope"].cancel()
