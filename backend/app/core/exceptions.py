"""Application errors returned as JSON responses without stack traces."""


class AppError(Exception):
    """Error with a client-safe message and an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InvalidPdfError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class EmptyPdfError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


class EmbeddingConfigError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)


class EmbeddingAPIError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=502)


class DatabaseUnavailableError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)


class LLMConfigError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)


class LLMAPIError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=502)


class LLMTimeoutError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=504)
