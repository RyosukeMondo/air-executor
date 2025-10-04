"""
Reusable Claude SDK function for Airflow DAGs.

This module provides run_claude_query_sdk() which runs Claude queries
without TTY requirements using claude_wrapper.py with JSON-based stdin/stdout.

This is a utility module imported by specialized DAGs (python_cleanup, commit_and_push, etc.)
"""

import json
import subprocess
import sys

# Add project to path to import config
sys.path.insert(0, "/home/rmondo/repos/air-executor/src")
from air_executor.config import load_config


def _load_config_and_params(context) -> tuple:
    """Load configuration and DAG parameters (SRP)"""
    try:
        config = load_config()
    except Exception as e:
        raise RuntimeError(
            f"Failed to load config: {e}\n"
            f"Create config/air-executor.toml from config/air-executor.example.toml"
        )

    dag_run_conf = context.get("dag_run").conf or {}
    prompt = dag_run_conf.get("prompt", "hello, how old are you?")
    working_directory = dag_run_conf.get("working_directory", config.project_root)

    return config, prompt, working_directory


def _send_prompt_command(process, prompt: str, config):
    """Send prompt command to wrapper (SRP)"""
    command = {
        "action": "prompt",
        "prompt": prompt,
        "options": {
            **config.claude_default_options,
            "permission_mode": config.claude_permission_mode,
        },
    }
    process.stdin.write(json.dumps(command) + "\n")
    process.stdin.flush()


def _extract_stream_text(payload: dict, conversation_text: list) -> bool:
    """Extract and print text from stream payload (SRP, KISS)"""
    message_type = payload.get("message_type")
    found_content = False

    if message_type == "ResultMessage" and payload.get("result"):
        text = payload["result"]
        conversation_text.append(text)
        print(text, end="", flush=True)
        found_content = True
    elif payload.get("content"):
        content = payload.get("content", [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if text:
                        conversation_text.append(text)
                        print(text, end="", flush=True)
                        found_content = True
    elif payload.get("text"):
        text = payload["text"]
        conversation_text.append(text)
        print(text, end="", flush=True)
        found_content = True

    return found_content


def _handle_event(event: dict, process, prompt: str, config, conversation_text: list) -> bool:
    """Handle single event, return True if should exit (SRP)"""
    event_type = event.get("event")

    if event_type != "stream":
        print(f"📨 Event: {event_type}")

    if event_type == "ready":
        print("✅ Wrapper ready, sending prompt...")
        _send_prompt_command(process, prompt, config)
    elif event_type == "stream":
        payload = event.get("payload", {})
        found_content = _extract_stream_text(payload, conversation_text)
        if not found_content:
            print(f"⚠️  Stream event with unrecognized payload: {list(payload.keys())}", flush=True)
    elif event_type == "run_completed":
        print("✅ Run completed successfully!")
    elif event_type == "run_failed":
        error = event.get("error", "Unknown error")
        print(f"❌ Run failed: {error}")
        raise RuntimeError(f"Claude query failed: {error}")
    elif event_type == "shutdown":
        print("✅ Wrapper shutdown")
        return True

    return False


def _process_wrapper_output(process, prompt: str, config) -> tuple:
    """Process wrapper output and collect events (SRP)"""
    events = []
    conversation_text = []

    for line in process.stdout:
        if not line.strip():
            if process.poll() is not None:
                print(f"✅ Process exited with code {process.returncode}")
                break
            continue

        try:
            event = json.loads(line)
            events.append(event)

            should_exit = _handle_event(event, process, prompt, config, conversation_text)
            if should_exit:
                break

        except json.JSONDecodeError:
            print(f"⚠️  Non-JSON output: {line.strip()}")
            continue

    return events, conversation_text


def _print_summary(full_response: str, events: list):
    """Print response summary (SRP)"""
    print("\n")
    print("=" * 60)
    print("📋 CLAUDE'S RESPONSE SUMMARY")
    print("=" * 60)
    print(f"Total response length: {len(full_response)} characters")
    print(f"Total events received: {len(events)}")
    print("=" * 60)


def run_claude_query_sdk(**context):
    """
    Run Claude query using claude_wrapper.py (non-blocking, no TTY needed).

    This function:
    1. Starts claude_wrapper.py process
    2. Sends prompt via JSON stdin
    3. Collects response via JSON stdout
    4. Returns the full conversation

    DAG parameters (pass via dag_run.conf):
    - prompt: The prompt to send to Claude (default: "hello, how old are you?")
    - working_directory: Directory to launch wrapper from (default: project root)
    """
    config, prompt, working_directory = _load_config_and_params(context)

    print("🚀 Starting claude_wrapper.py")
    print(f"   Working directory: {working_directory}")
    print(f"   Prompt: {prompt}")

    # Setup environment with log level from config
    import os

    env = os.environ.copy()
    wrapper_log_level = getattr(config, "logging", {}).get("wrapper", {}).get("level", "INFO")
    if isinstance(wrapper_log_level, str):
        env["CLAUDE_WRAPPER_LOG_LEVEL"] = wrapper_log_level

    process = subprocess.Popen(
        [str(config.venv_python), str(config.wrapper_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=working_directory,
        env=env,
    )

    try:
        events, conversation_text = _process_wrapper_output(process, prompt, config)

        process.stdin.close()
        return_code = process.wait(timeout=config.claude_timeout)

        if return_code != 0:
            stderr = process.stderr.read()
            raise RuntimeError(f"Wrapper exited with code {return_code}: {stderr}")

        full_response = "\n".join(conversation_text)

        _print_summary(full_response, events)

        context["task_instance"].xcom_push(key="claude_response", value=full_response)

        context["task_instance"].xcom_push(key="events_count", value=len(events))

        return {
            "status": "success",
            "response": full_response,
            "events_count": len(events),
        }

    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError(f"Claude query timed out after {config.claude_timeout} seconds")

    except Exception as e:
        process.kill()
        raise RuntimeError(f"Error running Claude query: {e}")
