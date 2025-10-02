# Architecture Design Decisions

Key architectural decisions and their rationale.

## Decision Log

### ADR-001: Use Subprocess Isolation for Task Execution

**Context:** Tasks need to be executed in isolated environments to prevent interference.

**Decision:** Execute tasks as separate subprocess with dedicated environment.

**Rationale:**
- Process isolation prevents state pollution
- Easy timeout and cancellation management
- Clean resource cleanup
- Compatible with various execution contexts

**Consequences:**
- Slight overhead from process creation
- Inter-process communication required
- Simpler debugging and monitoring

### ADR-002: File-Based Storage for Job State

**Context:** Need persistent storage for job metadata and state.

**Decision:** Use JSON files for job storage with file-based locking.

**Rationale:**
- Simple implementation without external dependencies
- Easy to inspect and debug
- Human-readable format
- Sufficient for moderate scale

**Consequences:**
- Limited scalability for high-throughput scenarios
- File locking complexity
- Future migration path to database if needed

### ADR-003: Wrapper Pattern for Claude Integration

**Context:** Need flexible integration with Claude AI SDK.

**Decision:** Create wrapper script with JSON stdin/stdout protocol.

**Rationale:**
- Decouples Air Executor from Claude SDK implementation
- Language-agnostic protocol
- Easy to version and update independently
- Supports both SDK and CLI modes

**Consequences:**
- Additional layer of indirection
- Protocol overhead
- Excellent flexibility and testability

### ADR-004: Tiered Health Checks for Autonomous Fixing

**Context:** Health checks are slow when running full test suite.

**Decision:** Implement two-tier checks: static (fast) → dynamic (slow, conditional).

**Rationale:**
- Static checks (analyze + code quality) take 2-10s
- Dynamic checks (tests + coverage) take 2-5min
- Skip expensive checks when static fails
- 10-150x performance improvement

**Consequences:**
- More complex health monitoring logic
- Requires careful condition management
- Massive time savings in practice

### ADR-005: Separate Sessions with Shared State

**Context:** Balance between context size and fix quality in autonomous fixing.

**Decision:** Use separate Claude sessions per task, share state via Redis.

**Rationale:**
- Each task has minimal context (one error + surrounding code)
- Session summaries shared via Redis
- 70% reduction in context size vs full codebase
- Better focus on specific issues

**Consequences:**
- Redis dependency
- Session management complexity
- Excellent scaling properties

### ADR-006: Line-by-Line Stdout Reading

**Context:** Wrapper process hangs when using `communicate()`.

**Decision:** Read stdout line-by-line and break on shutdown events.

**Rationale:**
- Prevents buffer blocking
- Allows real-time event processing
- Matches Airflow DAG pattern
- Clean shutdown detection

**Consequences:**
- More complex stdout handling
- No hanging processes
- Better observability

### ADR-007: Explicit Git Commands in Prompts

**Context:** Changes made but not committed automatically.

**Decision:** Include explicit git commands in all fix prompts.

**Rationale:**
- Claude needs explicit instructions
- Auto-commit flags not reliable
- Clear, verifiable behavior
- Commit messages follow convention

**Consequences:**
- Longer prompts
- Consistent commit behavior
- Easy to track changes

## Future Considerations

### Database Backend
- Consider PostgreSQL/SQLite for job storage at scale
- Migration path exists with current abstraction

### Distributed Execution
- Multi-worker support for parallel task execution
- Queue-based task distribution

### Advanced Health Metrics
- Custom metric definitions
- Metric trend tracking
- Alerting thresholds

### Session Persistence
- Long-running Claude sessions for related tasks
- Context caching and reuse
- Cost optimization

## See Also

- [System Overview](./overview.md)
- [Autonomous Fixing](./autonomous-fixing.md)
- [Technical Research](./technical-research.md)
