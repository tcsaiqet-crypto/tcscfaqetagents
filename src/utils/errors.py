"""Shared fail-fast exception types for AI-required agent stages."""

from typing import Any, Dict


class AIRequiredFailureException(Exception):
    """Raised when a stage requires a real AI response and none could be obtained.

    Carries structured diagnostics so the API layer can surface a detailed
    error to the UI instead of silently substituting deterministic/sample data.
    """

    def __init__(self, error_code: str, error_message: str, diagnostics: Dict[str, Any]):
        super().__init__(error_message)
        self.error_code = error_code
        self.error_message = error_message
        self.diagnostics = diagnostics
