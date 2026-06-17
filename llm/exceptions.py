class LlmError(Exception):
    """Base error for local LLM communication and response parsing."""


class LlmJsonError(LlmError):
    """Raised when an LLM response does not contain a valid JSON object."""
