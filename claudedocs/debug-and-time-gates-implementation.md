# Debug Logging and Time Gate Implementation

## Summary

Implemented two critical improvements to prevent wasteful API usage and improve debugging:

1. **Structured Debug Logging System** - Records all operations in JSON format for systematic debugging
2. **Time Gate Keeper** - Prevents rapid iterations that waste API calls

## What Was Implemented

### 1. Configuration (config/prompts.yaml)

Added two new configuration sections:

#### Time Gates Configuration
```yaml
time_gates:
  min_iteration_duration: 30     # Minimum 30 seconds per iteration
  rapid_iteration_threshold: 3   # Detect 3 fast iterations
  rapid_iteration_window: 90     # Within 90 seconds = abort
  wrapper_call_min_duration: 20  # Claude wrapper takes ~20s minimum
```

#### Debug Logging Configuration
```yaml
debug:
  enabled: true
  log_dir: "logs/debug"
  log_levels:
    wrapper_calls: true           # Log all claude_wrapper invocations
    wrapper_responses: true       # Log wrapper JSON responses
    iteration_timing: true        # Log iteration start/end times
    fix_results: true             # Log fix success/failure details
  format: json                    # JSON format for structured logging
  track_metrics:
    claude_usage: true            # Track API usage/costs
    iteration_duration: true      # Track time per iteration
    fix_success_rate: true        # Track fix success/failure rates
```

### 2. Core Modules Created

#### core/debug_logger.py
- **DebugLogger class**: Structured logging for all operations
- **WrapperCall dataclass**: Track claude_wrapper invocations
- **IterationMetrics dataclass**: Track iteration timing and results
- **Key methods**:
  - `log_wrapper_call()`: Log wrapper invocations with duration
  - `log_iteration_start/end()`: Track iteration timing
  - `log_fix_result()`: Track fix attempts and success rates
  - `log_test_creation()`: Track test creation attempts
  - `get_metrics()`: Get summary statistics
  - `log_session_end()`: Final metrics dump

#### core/time_gatekeeper.py
- **TimeGatekeeper class**: Prevent wasteful rapid iterations
- **IterationTiming dataclass**: Track iteration timing data
- **Key methods**:
  - `start_iteration()`: Mark iteration start
  - `end_iteration()`: Calculate duration, check gates
  - `_check_should_abort()`: Detect stuck in rapid loop
  - `wait_if_needed()`: Sleep if iteration too fast
  - `get_timing_summary()`: Statistics on all iterations

### 3. Integration Points

#### core/iteration_engine.py
- Initialize DebugLogger and TimeGatekeeper
- Track iteration timing (start/end)
- Log all fix results and iteration metrics
- Check for rapid iteration abort condition
- Enforce minimum iteration duration
- Return timing summary and metrics with results

#### core/claude_client.py
- Track timing for all wrapper calls
- Log wrapper calls with duration, success, errors
- Pass prompt_type for categorization
- Handle timeouts and exceptions with logging

#### core/fixer.py
- Pass debug_logger to ClaudeClient
- Add prompt_type to all claude.query() calls:
  - `fix_error` - Fixing errors
  - `fix_complexity` - Fixing complexity issues
  - `fix_test` - Fixing test failures
  - `create_test` - Creating new tests
  - `analysis` - Static analysis
  - `discover_tests` - Test discovery

## How It Works

### Debug Logging Flow
1. Each project gets timestamped JSONL log file in `logs/debug/`
2. Every claude_wrapper call logged with:
   - Timestamp
   - Prompt type (analysis, fix_error, fix_test, create_test)
   - Duration (seconds)
   - Success/failure
   - Error message (if failed)
3. Iteration metrics tracked:
   - Start/end times
   - Duration
   - Phase (p1_analysis, p1_fix, p2_test, p2_fix)
   - Fixes applied
   - Tests created
4. Session summary at end with:
   - Total wrapper calls
   - Average duration
   - Fix success rate
   - Tests created/fixed

### Time Gate Flow
1. **Start Iteration**: Mark timestamp when iteration begins
2. **End Iteration**: Calculate duration and check:
   - Is duration < 30 seconds? (too fast)
   - Have we had 3 fast iterations within 90 seconds? (stuck loop)
3. **Actions**:
   - If too fast: Wait remaining time to reach 30 seconds
   - If stuck loop: Abort with clear message and timing summary
4. **Prevents**:
   - Rapid iterations that accomplish nothing
   - Infinite loops from quick failures
   - API waste from rapid-fire calls

## Example Output

### Console Output (Rapid Iteration Detected)
```
❌ ABORT: Detected 3 rapid iterations within 90s
   This indicates the system is stuck in a wasteful loop.
   Timing summary: {
     'total_iterations': 3,
     'avg_duration': 25.3,
     'rapid_count': 3,
     'rapid_iterations': [1, 2, 3]
   }
```

### Debug Log (logs/debug/warps_20250103_143022.jsonl)
```json
{"timestamp": "2025-01-03T14:30:22", "event": "session_start", "project": "warps"}
{"timestamp": "2025-01-03T14:30:22", "event": "iteration_start", "iteration": 1, "phase": "p1_analysis"}
{"timestamp": "2025-01-03T14:30:25", "event": "wrapper_call", "prompt_type": "analysis", "duration": 2.8, "success": true}
{"timestamp": "2025-01-03T14:30:30", "event": "wrapper_call", "prompt_type": "fix_error", "duration": 4.2, "success": true}
{"timestamp": "2025-01-03T14:30:35", "event": "fix_result", "fix_type": "static_issue", "success": true, "duration": 10.5}
{"timestamp": "2025-01-03T14:30:35", "event": "iteration_end", "iteration": 1, "phase": "p1_fix", "duration": 13.2, "success": true, "fixes_applied": 8}
```

## Benefits

### Debug Logging Benefits
- **Systematic debugging**: All operations recorded for analysis
- **Prompt engineering**: See exactly what prompts were sent and results
- **Performance tracking**: Identify slow operations
- **Success rate monitoring**: Track fix effectiveness
- **Future-ready**: Prepared for logging server/monitoring server

### Time Gate Benefits
- **API cost savings**: Prevent wasteful rapid iterations
- **Loop detection**: Automatically detect and abort stuck loops
- **Quality enforcement**: Ensure minimum iteration time for meaningful work
- **Clear diagnostics**: Timing summary explains why abort happened

## Testing

To test the improvements:

1. **Run a project through the system**:
   ```bash
   pm2 start airflow_dags/autonomous_fixing/ecosystem.config.js --only fix-warps
   ```

2. **Check debug logs**:
   ```bash
   ls -lh logs/debug/
   cat logs/debug/warps_*.jsonl | jq .
   ```

3. **Monitor time gates**:
   - Watch for "⏸️  Iteration completed too quickly" messages
   - Watch for "❌ ABORT: Detected 3 rapid iterations" abort messages

4. **Analyze metrics**:
   - Check wrapper call durations
   - Check iteration timing
   - Check fix success rates

## Future Enhancements

### Logging Server (Future)
The debug configuration already includes placeholders for remote logging:
```yaml
debug:
  remote_logging:
    enabled: false
    endpoint: null  # Future: monitoring server URL
```

This allows future integration with a centralized logging/monitoring server for:
- Real-time monitoring across all projects
- Historical analysis and trends
- Alert on anomalies
- Dashboard visualization

## Files Modified

- `config/prompts.yaml` - Added time_gates and debug configuration
- `core/debug_logger.py` - NEW: Structured debug logging
- `core/time_gatekeeper.py` - NEW: Time gate enforcement
- `core/iteration_engine.py` - Integrated debug logging and time gates
- `core/claude_client.py` - Added timing and logging for wrapper calls
- `core/fixer.py` - Pass prompt_type for categorization
- `multi_language_orchestrator.py` - Pass project_name to IterationEngine

## Notes

- Minimum iteration duration: 30 seconds (configurable)
- Rapid iteration threshold: 3 fast iterations (configurable)
- Rapid iteration window: 90 seconds (configurable)
- Wrapper call minimum: 20 seconds (based on observed timing)
- Debug logs: JSONL format (one JSON event per line)
- Log directory: `logs/debug/` (created automatically)
