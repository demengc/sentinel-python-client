from datetime import UTC, datetime

import pytest

from sentinel._exceptions import LicenseValidationError
from sentinel.models.validation import (
    BlacklistFailureDetails,
    ExcessiveIpsFailureDetails,
    ExcessiveServersFailureDetails,
    ValidationDetails,
    ValidationResult,
    ValidationResultType,
)


def test_validation_result_type_values():
    assert ValidationResultType.SUCCESS == "SUCCESS"
    assert ValidationResultType.EXPIRED_LICENSE == "EXPIRED_LICENSE"
    assert ValidationResultType.UNKNOWN == "UNKNOWN"


def test_validation_result_type_from_string():
    assert ValidationResultType.from_string("SUCCESS") == ValidationResultType.SUCCESS
    assert (
        ValidationResultType.from_string("EXPIRED_LICENSE") == ValidationResultType.EXPIRED_LICENSE
    )
    assert ValidationResultType.from_string("bogus") == ValidationResultType.UNKNOWN
    assert ValidationResultType.from_string(None) == ValidationResultType.UNKNOWN


def test_validation_details():
    details = ValidationDetails(
        expiration=datetime(2026, 1, 1, tzinfo=UTC),
        server_count=1,
        max_servers=5,
        ip_count=2,
        max_ips=10,
        tier="Premium",
        entitlements={"feature_a"},
    )
    assert details.server_count == 1
    assert details.max_servers == 5
    assert details.tier == "Premium"


def test_validation_result_success():
    details = ValidationDetails(
        expiration=None,
        server_count=0,
        max_servers=5,
        ip_count=0,
        max_ips=10,
        tier="Free",
        entitlements=set(),
    )
    result = ValidationResult.success(details=details, message="License validated.")
    assert result.is_valid is True
    assert result.type == ValidationResultType.SUCCESS
    assert result.details is details
    assert result.failure_details is None
    assert result.require_valid() is details


def test_validation_result_failure():
    result = ValidationResult.failure(
        type=ValidationResultType.EXPIRED_LICENSE,
        message="License has expired.",
    )
    assert result.is_valid is False
    assert result.type == ValidationResultType.EXPIRED_LICENSE
    assert result.details is None


def test_validation_result_failure_with_details():
    fd = BlacklistFailureDetails(
        timestamp=datetime(2025, 6, 1, tzinfo=UTC),
        reason="Violation",
    )
    result = ValidationResult.failure(
        type=ValidationResultType.BLACKLISTED_LICENSE,
        message="License is blacklisted.",
        failure_details=fd,
    )
    assert result.failure_details is fd
    assert isinstance(result.failure_details, BlacklistFailureDetails)


def test_require_valid_raises_on_failure():
    result = ValidationResult.failure(
        type=ValidationResultType.EXPIRED_LICENSE,
        message="License has expired.",
    )
    with pytest.raises(LicenseValidationError) as exc_info:
        result.require_valid()
    assert exc_info.value.type == ValidationResultType.EXPIRED_LICENSE
    assert str(exc_info.value) == "License has expired."
    assert exc_info.value.failure_details is None


def test_require_valid_passes_failure_details():
    fd = BlacklistFailureDetails(
        timestamp=datetime(2025, 6, 1, tzinfo=UTC),
        reason="Violation",
    )
    result = ValidationResult.failure(
        type=ValidationResultType.BLACKLISTED_LICENSE,
        message="License is blacklisted.",
        failure_details=fd,
    )
    with pytest.raises(LicenseValidationError) as exc_info:
        result.require_valid()
    assert exc_info.value.failure_details is fd


def test_excessive_servers_failure_details():
    fd = ExcessiveServersFailureDetails(max_servers=5)
    assert fd.max_servers == 5


def test_excessive_ips_failure_details():
    fd = ExcessiveIpsFailureDetails(max_ips=10)
    assert fd.max_ips == 10
