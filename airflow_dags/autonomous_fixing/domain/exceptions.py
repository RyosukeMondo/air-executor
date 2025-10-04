"""Custom exceptions for autonomous fixing system."""


class ConfigurationError(Exception):
    """
    Raised when required tools or dependencies are not installed or misconfigured.

    This error should HALT execution immediately - it indicates a setup problem
    that cannot be resolved by retrying or fixing code.

    Examples:
        - pytest not installed
        - npm not found
        - radon missing
        - go command not in PATH

    When this error is raised, the orchestrator should:
        1. Print clear error message with installation instructions
        2. Halt execution immediately (no retries)
        3. Exit with non-zero status code
    """

    pass


class AnalysisError(Exception):
    """
    Raised when analysis operations fail unexpectedly.

    This is different from ConfigurationError - it indicates an unexpected
    problem during analysis, not a missing tool.

    Examples:
        - Malformed source file
        - Unexpected tool output format
        - Timeout during analysis
    """

    pass


class AirExecutorError(Exception):
    """Base exception for Air-Executor related errors."""


class JobFailedError(AirExecutorError):
    """Raised when an Air-Executor job fails."""

    def __init__(self, job_name: str):
        self.job_name = job_name
        super().__init__(f"Air-Executor job {job_name} failed!")


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""


class OrchestratorFailedError(OrchestratorError):
    """Raised when orchestrator fails to complete."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Orchestrator did not complete: {reason}")


class OrchestratorExitError(OrchestratorError):
    """Raised when orchestrator exits with non-zero code."""

    def __init__(self, exit_code: int):
        self.exit_code = exit_code
        super().__init__(f"Orchestrator failed with exit code {exit_code}")


class WrapperError(Exception):
    """Base exception for Claude wrapper errors."""


class WrapperExitError(WrapperError):
    """Raised when wrapper exits with non-zero code."""

    def __init__(self, return_code: int, stderr: str):
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(f"Wrapper exited with code {return_code}: {stderr}")


class WrapperTimeoutError(WrapperError):
    """Raised when Claude query times out."""

    def __init__(self, timeout: int):
        self.timeout = timeout
        super().__init__(f"Claude query timed out after {timeout} seconds")


class WrapperQueryError(WrapperError):
    """Raised when Claude query encounters an error."""

    def __init__(self, error: str):
        self.error = error
        super().__init__(f"Claude query failed: {error}")


class WrapperRuntimeError(WrapperError):
    """Raised when wrapper encounters a runtime error."""

    def __init__(self, error: str):
        self.error = error
        super().__init__(f"Error running Claude query: {error}")
