import re
from unittest.mock import patch

from sentinel.util.fingerprint import _get_platform_id, generate_fingerprint


def test_fingerprint_format():
    result = generate_fingerprint()
    assert isinstance(result, str)
    assert len(result) == 32
    assert re.fullmatch(r"[0-9a-f]{32}", result)


def test_fingerprint_is_cached():
    a = generate_fingerprint()
    b = generate_fingerprint()
    assert a == b


def test_fingerprint_is_deterministic():
    a = generate_fingerprint()
    b = generate_fingerprint()
    assert a == b


@patch("sentinel.util.fingerprint._read_text_file")
@patch("platform.system", return_value="Linux")
def test_linux_machine_id(mock_sys, mock_read):
    mock_read.return_value = "abc123"
    result = _get_platform_id()
    assert result == "abc123"
    mock_read.assert_any_call("/etc/machine-id")


@patch("sentinel.util.fingerprint._read_text_file", return_value=None)
@patch("sentinel.util.fingerprint._run_command", return_value=None)
@patch("platform.system", return_value="Linux")
def test_falls_back_when_no_platform_id(mock_sys, mock_cmd, mock_read):
    result = _get_platform_id()
    assert result is not None
    assert len(result) > 0


def test_normalize_rejects_invalid_values():
    from sentinel.util.fingerprint import _normalize_identifier

    assert _normalize_identifier("unknown") is None
    assert _normalize_identifier("none") is None
    assert _normalize_identifier("  ") is None
    assert _normalize_identifier("To Be Filled By O.E.M.") is None
    assert _normalize_identifier("000000000000") is None
    assert _normalize_identifier("ab") is None


def test_normalize_accepts_valid_values():
    from sentinel.util.fingerprint import _normalize_identifier

    assert _normalize_identifier("abc123def456") == "abc123def456"
    assert _normalize_identifier("  Valid-UUID-Here  ") == "valid-uuid-here"
