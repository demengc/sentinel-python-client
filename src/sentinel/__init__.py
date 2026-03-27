"""Sentinel Python Client - Official client for the Sentinel v2 API."""

from sentinel._async_client import AsyncSentinelClient
from sentinel._client import SentinelClient
from sentinel._exceptions import (
    LicenseValidationError,
    ReplayDetectedError,
    SentinelApiError,
    SentinelConnectionError,
    SentinelError,
    SignatureVerificationError,
)
from sentinel.models.license import (
    BlacklistInfo,
    License,
    LicenseIssuer,
    LicenseProduct,
    LicenseTier,
    SubUser,
)
from sentinel.models.page import Page
from sentinel.models.requests import (
    CLEAR,
    CLEAR_EXPIRATION,
    CreateLicenseRequest,
    ListLicensesRequest,
    UpdateLicenseRequest,
    ValidationRequest,
)
from sentinel.models.validation import (
    BlacklistFailureDetails,
    ExcessiveIpsFailureDetails,
    ExcessiveServersFailureDetails,
    FailureDetails,
    ValidationDetails,
    ValidationResult,
    ValidationResultType,
)

__all__ = [
    "SentinelClient",
    "AsyncSentinelClient",
    "SentinelError",
    "SentinelApiError",
    "SentinelConnectionError",
    "LicenseValidationError",
    "SignatureVerificationError",
    "ReplayDetectedError",
    "License",
    "LicenseProduct",
    "LicenseTier",
    "LicenseIssuer",
    "SubUser",
    "BlacklistInfo",
    "ValidationResult",
    "ValidationResultType",
    "ValidationDetails",
    "FailureDetails",
    "BlacklistFailureDetails",
    "ExcessiveServersFailureDetails",
    "ExcessiveIpsFailureDetails",
    "CreateLicenseRequest",
    "UpdateLicenseRequest",
    "ListLicensesRequest",
    "ValidationRequest",
    "CLEAR",
    "CLEAR_EXPIRATION",
    "Page",
]
