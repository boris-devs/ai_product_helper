from typing import Any


class AppError(Exception):
    status_code: int = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    status_code = 404


class InsufficientDataError(AppError):
    status_code = 422


class LLMError(AppError):
    status_code = 502


class LLMConfigError(LLMError):
    status_code = 503


class LLMResponseError(LLMError):
    pass
