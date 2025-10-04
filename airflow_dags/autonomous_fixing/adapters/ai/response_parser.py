"""
Response Parser - Intelligent error detection for AI wrapper responses.

Distinguishes real errors from benign warnings in stderr, preventing false failures.
"""

import logging
import os
from typing import Dict, List, Optional

import yaml

# Default noise patterns (substring matching for efficiency)
DEFAULT_NOISE_PATTERNS = [
    "punycode",
    "ExperimentalWarning",
    "Skipping files",
    "DeprecationWarning",
]

# Default error indicators (real failures)
DEFAULT_ERROR_INDICATORS = [
    "Error:",
    "FAILED:",
    "Exception",
    "Traceback",
    "error:",
    "failed:",
    "Fatal:",
    "FATAL:",
]

logger = logging.getLogger(__name__)


class ResponseParser:
    """Intelligent parser for AI wrapper responses with noise filtering."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize response parser with optional config file.

        Args:
            config_path: Optional path to error_patterns.yaml
                        (defaults to config/error_patterns.yaml)
        """
        self.config_path = config_path or "config/error_patterns.yaml"
        self.noise_patterns = DEFAULT_NOISE_PATTERNS.copy()
        self.error_indicators = DEFAULT_ERROR_INDICATORS.copy()

        self._load_config()

    def _load_config(self):
        """Load patterns from YAML config file with fallback to defaults."""
        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found at {self.config_path}, using default patterns")
            return

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config:
                logger.warning(f"Empty config file at {self.config_path}, using defaults")
                return

            # Load noise patterns if provided
            if 'noise_patterns' in config:
                if isinstance(config['noise_patterns'], list):
                    self.noise_patterns = config['noise_patterns']
                    logger.info(f"Loaded {len(self.noise_patterns)} noise patterns from config")
                else:
                    logger.warning("Invalid noise_patterns format in config, using defaults")

            # Load error indicators if provided
            if 'error_indicators' in config:
                if isinstance(config['error_indicators'], list):
                    self.error_indicators = config['error_indicators']
                    logger.info(f"Loaded {len(self.error_indicators)} error indicators from config")
                else:
                    logger.warning("Invalid error_indicators format in config, using defaults")

        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {self.config_path}: {e}, using defaults")
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}, using defaults")

    def parse(self, response: Dict, operation_type: str = "unknown") -> Dict:
        """
        Parse wrapper response with intelligent error detection.

        Args:
            response: Response dict from ClaudeClient.query()
            operation_type: Type of operation (for error context)

        Returns:
            Dict with:
                - success: bool (True if operation succeeded)
                - error_message: str (if failure, first 3 error lines)
                - errors: List[str] (if failure, all error lines)
                - status: str (if success, "completed")
        """
        # Check for stderr content first and analyze it
        stderr = response.get('stderr', '')
        generic_error = response.get('error', '')

        if stderr:
            # Analyze stderr for real errors vs noise
            real_errors = self._extract_real_errors(stderr)

            if real_errors:
                # Found real errors in stderr - use these instead of generic error
                error_message = "\n".join(real_errors[:3])  # First 3 lines
                return {
                    "success": False,
                    "error_message": f"[{operation_type}] {error_message}",
                    "errors": real_errors
                }
            # else: only noise in stderr, continue to check other error sources

        # Check for explicit error in response (after stderr analysis)
        if generic_error and not stderr:
            # Only use generic error if no stderr available
            return {
                "success": False,
                "error_message": f"[{operation_type}] {generic_error}",
                "errors": [generic_error]
            }

        # No stderr or only noise - check success flag
        if response.get('success'):
            return {"success": True, "status": "completed"}

        # Have generic error but only noise in stderr - use generic error
        if generic_error:
            return {
                "success": False,
                "error_message": f"[{operation_type}] {generic_error}",
                "errors": [generic_error]
            }

        # No clear success indicator
        return {
            "success": False,
            "error_message": f"[{operation_type}] Unknown error - no clear success indicator",
            "errors": []
        }

    def _extract_real_errors(self, stderr: str) -> List[str]:
        """
        Extract real error lines from stderr, filtering out noise.

        Args:
            stderr: Stderr output string

        Returns:
            List of real error lines (empty if only noise)
        """
        if not stderr:
            return []

        lines = stderr.split('\n')
        real_errors = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip if line contains noise patterns
            if self._is_noise(line):
                continue

            # Check if line contains error indicators
            if any(indicator in line for indicator in self.error_indicators):
                # Truncate to prevent log flooding
                truncated_line = line[:500] if len(line) > 500 else line
                real_errors.append(truncated_line)

        return real_errors

    def _is_noise(self, line: str) -> bool:
        """
        Check if a line matches noise patterns.

        Args:
            line: Single line from stderr

        Returns:
            True if line is noise, False if potentially meaningful
        """
        # Efficient substring matching (not regex) for common patterns
        return any(pattern in line for pattern in self.noise_patterns)
