"""Centralized error handling for language adapters (SSOT)."""

import subprocess
from collections.abc import Callable
from functools import wraps

from ..domain.exceptions import ConfigurationError


def handle_analysis_errors(phase_name: str, tool_name: str = None, install_command: str = None):
    """Decorator for consistent error handling across adapter methods.

    Args:
        phase_name: Name of the analysis phase (e.g., "static analysis", "tests")
        tool_name: Name of the required tool (e.g., "pytest", "npm")
        install_command: Installation command to suggest if tool missing

    This decorator:
    - Catches FileNotFoundError and raises RuntimeError with installation help
    - Catches RuntimeError with "not installed" and re-raises with context
    - Catches subprocess.TimeoutExpired and sets result.success = False
    - Catches unexpected errors and logs them
    - Always sets result.execution_time
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, project_path: str, *args, **kwargs):
            import time

            start_time = time.time()

            try:
                # Call the original method
                result = func(self, project_path, *args, **kwargs)
                return result

            except subprocess.TimeoutExpired as e:
                # Timeout is expected - set result to failed
                result = func.__annotations__.get("return")  # Get AnalysisResult type
                if result:
                    # Create minimal result
                    from ...domain.models import AnalysisResult

                    result = AnalysisResult(
                        language=self.language_name, phase=phase_name, project_path=project_path
                    )
                    result.success = False
                    result.error_message = (
                        f"{phase_name.capitalize()} timed out after {e.timeout} seconds"
                    )
                    result.execution_time = time.time() - start_time
                    return result
                raise

            except FileNotFoundError as e:
                # Tool not installed - fail fast with helpful message
                if tool_name and install_command:
                    raise ConfigurationError(
                        f"{tool_name} not found: {e}\n" f"Install with: {install_command}"
                    ) from e
                raise ConfigurationError(
                    f"Tool not found for {phase_name}: {e}\n" f"Check tool installation"
                ) from e

            except ConfigurationError:
                # Configuration errors from nested calls - re-raise immediately
                raise

            except RuntimeError:
                # Other runtime errors - let method handle or propagate
                raise

            except Exception as e:  # noqa: BLE001 - Catch-all for graceful degradation
                # Unexpected errors - create failed result to prevent complete failure
                from ...domain.models import AnalysisResult

                result = AnalysisResult(
                    language=self.language_name, phase=phase_name, project_path=project_path
                )
                result.success = False
                result.error_message = f"Unexpected error in {phase_name}: {e}"
                result.execution_time = time.time() - start_time
                return result

        return wrapper

    return decorator


def with_execution_time(func: Callable):
    """Decorator to automatically add execution_time to result.

    Simpler decorator for methods that already handle their own errors
    but need execution time tracking.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        import time

        start_time = time.time()

        try:
            result = func(self, *args, **kwargs)
            if hasattr(result, "execution_time") and result.execution_time is None:
                result.execution_time = time.time() - start_time
            return result
        except Exception:
            # Re-raise but ensure timing is set if result exists in exception context
            raise

    return wrapper
