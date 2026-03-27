from sentinel._exceptions import (
    LicenseValidationError,
    ReplayDetectedError,
    SentinelApiError,
    SentinelConnectionError,
    SentinelError,
    SignatureVerificationError,
)


def test_sentinel_error_is_base():
    err = SentinelError("test")
    assert str(err) == "test"
    assert isinstance(err, Exception)


def test_all_exceptions_inherit_from_sentinel_error():
    assert issubclass(SentinelApiError, SentinelError)
    assert issubclass(SentinelConnectionError, SentinelError)
    assert issubclass(LicenseValidationError, SentinelError)
    assert issubclass(SignatureVerificationError, SentinelError)
    assert issubclass(ReplayDetectedError, SentinelError)


def test_sentinel_api_error_fields():
    err = SentinelApiError(
        http_status=429,
        type="RATE_LIMITED",
        message="Too many requests",
        retry_after_seconds=30,
    )
    assert err.http_status == 429
    assert err.type == "RATE_LIMITED"
    assert str(err) == "Too many requests"
    assert err.retry_after_seconds == 30


def test_sentinel_api_error_defaults():
    err = SentinelApiError(http_status=500, type=None, message="Server error")
    assert err.retry_after_seconds is None


def test_sentinel_connection_error():
    cause = OSError("Connection refused")
    err = SentinelConnectionError("Failed to connect", cause)
    assert str(err) == "Failed to connect"
    assert err.__cause__ is cause


def test_license_validation_error():
    from sentinel.models.validation import ValidationResultType

    err = LicenseValidationError(
        type=ValidationResultType.EXPIRED_LICENSE,
        message="License has expired",
    )
    assert err.type == ValidationResultType.EXPIRED_LICENSE
    assert str(err) == "License has expired"
