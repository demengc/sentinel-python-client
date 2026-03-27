from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sentinel._exceptions import LicenseValidationError


class ValidationResultType(StrEnum):
    SUCCESS = "SUCCESS"
    INVALID_PRODUCT = "INVALID_PRODUCT"
    INVALID_LICENSE = "INVALID_LICENSE"
    INVALID_PLATFORM = "INVALID_PLATFORM"
    EXPIRED_LICENSE = "EXPIRED_LICENSE"
    BLACKLISTED_LICENSE = "BLACKLISTED_LICENSE"
    CONNECTION_MISMATCH = "CONNECTION_MISMATCH"
    EXCESSIVE_SERVERS = "EXCESSIVE_SERVERS"
    EXCESSIVE_IPS = "EXCESSIVE_IPS"
    UNKNOWN = "UNKNOWN"

    @staticmethod
    def from_string(value: str | None) -> ValidationResultType:
        if value is None:
            return ValidationResultType.UNKNOWN
        try:
            return ValidationResultType(value)
        except ValueError:
            return ValidationResultType.UNKNOWN


@dataclass(frozen=True)
class ValidationDetails:
    expiration: datetime | None
    server_count: int
    max_servers: int
    ip_count: int
    max_ips: int
    tier: str | None
    entitlements: set[str]


@dataclass(frozen=True)
class FailureDetails:
    pass


@dataclass(frozen=True)
class BlacklistFailureDetails(FailureDetails):
    timestamp: datetime
    reason: str | None


@dataclass(frozen=True)
class ExcessiveServersFailureDetails(FailureDetails):
    max_servers: int


@dataclass(frozen=True)
class ExcessiveIpsFailureDetails(FailureDetails):
    max_ips: int


@dataclass(frozen=True)
class ValidationResult:
    type: ValidationResultType
    message: str
    is_valid: bool
    details: ValidationDetails | None = None
    failure_details: FailureDetails | None = None

    @staticmethod
    def success(details: ValidationDetails, message: str) -> ValidationResult:
        return ValidationResult(
            type=ValidationResultType.SUCCESS,
            message=message,
            is_valid=True,
            details=details,
        )

    @staticmethod
    def failure(
        type: ValidationResultType,
        message: str,
        failure_details: FailureDetails | None = None,
    ) -> ValidationResult:
        return ValidationResult(
            type=type,
            message=message,
            is_valid=False,
            failure_details=failure_details,
        )

    def require_valid(self) -> ValidationDetails:
        if not self.is_valid:
            raise LicenseValidationError(
                type=self.type,
                message=self.message,
                failure_details=self.failure_details,
            )
        assert self.details is not None
        return self.details
