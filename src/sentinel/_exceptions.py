from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinel.models.validation import ValidationResultType


class SentinelError(Exception):
    pass


class SentinelApiError(SentinelError):
    def __init__(
        self,
        http_status: int,
        type: str | None,
        message: str,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.type = type
        self.retry_after_seconds = retry_after_seconds


class SentinelConnectionError(SentinelError):
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        if cause is not None:
            self.__cause__ = cause


class LicenseValidationError(SentinelError):
    def __init__(
        self,
        type: ValidationResultType,
        message: str,
        failure_details: object | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.type = type
        self.failure_details = failure_details


class SignatureVerificationError(SentinelError):
    pass


class ReplayDetectedError(SentinelError):
    pass
