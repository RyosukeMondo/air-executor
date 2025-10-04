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
sys.path.insert(0, '/home/rmondo/repos/air-executor/src')
from air_executor.config import load_config


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
    # Load configuration (paths are now environment-independent!)
    try:
        config = load_config()
        wrapper_path = config.wrapper_path
        venv_python = config.venv_python
        timeout = config.claude_timeout
        permission_mode = config.claude_permission_mode
    except Exception as e:
        raise RuntimeError(f"Failed to load config: {e}\n"
                         f"Create config/air-executor.toml from config/air-executor.example.toml")

    # Get parameters from DAG run config
    dag_run_conf = context.get('dag_run').conf or {}
    prompt = dag_run_conf.get('prompt', 'hello, how old are you?')
    working_directory = dag_run_conf.get('working_directory', config.project_root)

    print("🚀 Starting claude_wrapper.py")
    print(f"   Working directory: {working_directory}")
    print(f"   Prompt: {prompt}")

    # Start the wrapper process
    process = subprocess.Popen(
        [str(venv_python), str(wrapper_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
        cwd=working_directory,  # Set working directory for wrapper
    )

    try:
        # Collect all output events
        events = []
        conversation_text = []

        # Track if we should exit the loop
        should_exit = False

        # Wait for "ready" event
        for line in process.stdout:
            if not line.strip():
                # Check if process exited
                if process.poll() is not None:
                    print(f"✅ Process exited with code {process.returncode}")
                    break
                continue

            try:
                event = json.loads(line)
                events.append(event)

                event_type = event.get("event")
                # Don't print generic event for stream (we'll print content instead)
                if event_type != "stream":
                    print(f"📨 Event: {event_type}")

                if event_type == "ready":
                    print("✅ Wrapper ready, sending prompt...")

                    # Send the prompt command (using config values)
                    command = {
                        "action": "prompt",
                        "prompt": prompt,
                        "options": {
                            **config.claude_default_options,  # Use defaults from config
                            "permission_mode": permission_mode,  # From config
                        }
                    }

                    process.stdin.write(json.dumps(command) + "\n")
                    process.stdin.flush()

                elif event_type == "stream":
                    # Extract message content from stream - print in real-time for Airflow logs
                    payload = event.get("payload", {})
                    message_type = payload.get("message_type")

                    # Track if we found any text content to print
                    found_content = False

                    # Extract text from different message types
                    if message_type == "ResultMessage" and payload.get("result"):
                        # Final result message
                        text = payload["result"]
                        conversation_text.append(text)
                        print(text, end='', flush=True)  # Real-time streaming output
                        found_content = True
                    elif payload.get("content"):
                        # Content array (for streaming chunks)
                        content = payload.get("content", [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    text = item.get("text", "")
                                    if text:
                                        conversation_text.append(text)
                                        print(text, end='', flush=True)  # Real-time streaming
                                        found_content = True
                    elif payload.get("text"):
                        # Direct text field
                        text = payload["text"]
                        conversation_text.append(text)
                        print(text, end='', flush=True)  # Real-time streaming
                        found_content = True

                    # Debug: If no content matched, log the payload structure
                    if not found_content:
                        print(f"⚠️  Stream event with unrecognized payload: {list(payload.keys())}", flush=True)

                elif event_type == "run_completed":
                    print("✅ Run completed successfully!")

                elif event_type == "run_failed":
                    error = event.get("error", "Unknown error")
                    print(f"❌ Run failed: {error}")
                    raise RuntimeError(f"Claude query failed: {error}")

                elif event_type == "auto_shutdown":
                    print("✅ Auto-shutdown triggered")
                    should_exit = True  # Mark for exit after final events

                elif event_type == "shutdown":
                    print("✅ Wrapper shutdown")
                    break

                elif event_type == "state":
                    # State event comes after auto_shutdown
                    if should_exit and event.get("state") == "idle":
                        print("✅ Wrapper idle, exiting loop")
                        break

            except json.JSONDecodeError:
                print(f"⚠️  Non-JSON output: {line.strip()}")
                continue

        # Close stdin to signal wrapper we're done
        process.stdin.close()

        # Wait for process to complete (using timeout from config)
        return_code = process.wait(timeout=timeout)

        if return_code != 0:
            stderr = process.stderr.read()
            raise RuntimeError(f"Wrapper exited with code {return_code}: {stderr}")

        # Combine all conversation text
        full_response = "\n".join(conversation_text)

        # Add final newline after streaming output
        print("\n")

        # Print summary (full response already streamed above)
        print("="*60)
        print("📋 CLAUDE'S RESPONSE SUMMARY")
        print("="*60)
        print(f"Total response length: {len(full_response)} characters")
        print(f"Total events received: {len(events)}")
        print("="*60)

        # Push to XCom for downstream tasks
        context['task_instance'].xcom_push(
            key='claude_response',
            value=full_response
        )

        context['task_instance'].xcom_push(
            key='events_count',
            value=len(events)
        )

        return {
            "status": "success",
            "response": full_response,
            "events_count": len(events),
        }

    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError(f"Claude query timed out after {timeout} seconds")

    except Exception as e:
        process.kill()
        raise RuntimeError(f"Error running Claude query: {e}")
