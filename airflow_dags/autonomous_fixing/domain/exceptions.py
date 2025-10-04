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
