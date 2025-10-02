"""
Airflow DAG that uses claude_code_sdk via claude_wrapper.py (non-blocking).

This DAG runs Claude queries without TTY requirements using the proven
claude_wrapper.py approach with JSON-based stdin/stdout communication.
"""

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import json
import os
import sys
from pathlib import Path

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

    # The prompt to send to Claude
    prompt = "hello, how old are you?"

    print(f"🚀 Starting claude_wrapper.py with prompt: {prompt}")

    # Start the wrapper process
    process = subprocess.Popen(
        [str(venv_python), str(wrapper_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
    )

    try:
        # Collect all output events
        events = []
        conversation_text = []

        # Track if we should exit the loop
        should_exit = False
        completed = False

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
                    # Extract message content from stream
                    payload = event.get("payload", {})
                    message_type = payload.get("message_type")

                    # Extract text from different message types
                    if message_type == "ResultMessage" and payload.get("result"):
                        # Final result message
                        text = payload["result"]
                        conversation_text.append(text)
                        print(f"💬 Claude (final): {text[:100]}...")
                    elif payload.get("content"):
                        # Content array (for streaming chunks)
                        content = payload.get("content", [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    text = item.get("text", "")
                                    if text:
                                        conversation_text.append(text)
                                        print(f"💬 Claude: {text[:100]}...")
                    elif payload.get("text"):
                        # Direct text field
                        text = payload["text"]
                        conversation_text.append(text)
                        print(f"💬 Claude: {text[:100]}...")

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

            except json.JSONDecodeError as e:
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

        print("\n" + "="*60)
        print("📋 CLAUDE'S RESPONSE")
        print("="*60)
        print(full_response)
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


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 2),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'claude_query_sdk',
    default_args=default_args,
    description='Run Claude query using claude_code_sdk (non-blocking)',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['claude', 'sdk', 'non-blocking'],
) as dag:

    run_query = PythonOperator(
        task_id='run_claude_query_sdk',
        python_callable=run_claude_query_sdk,
        doc_md="""
        ### Run Claude Query via SDK

        This task uses `claude_wrapper.py` which:
        - ✅ Non-blocking execution (no TTY required)
        - ✅ JSON-based stdin/stdout communication
        - ✅ Streams responses in real-time
        - ✅ Auto-exits when complete (`exit_on_complete: true`)

        **Prompt:** "hello, how old are you?"

        **How it works:**
        1. Starts `claude_wrapper.py` subprocess
        2. Waits for "ready" event
        3. Sends prompt via JSON stdin
        4. Collects stream events
        5. Waits for "run_completed"
        6. Returns full response

        **Output:** Check logs to see Claude's response!
        """,
    )

    run_query
