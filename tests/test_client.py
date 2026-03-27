import base64
import time

import pytest
import respx
from nacl.signing import SigningKey

from sentinel._async_client import AsyncSentinelClient
from sentinel._client import SentinelClient
from sentinel._exceptions import (
    ReplayDetectedError,
    SignatureVerificationError,
)
from sentinel.models.requests import ValidationRequest

BASE = "https://sentinel.example.com"


def test_client_requires_base_url():
    with pytest.raises(ValueError, match="base_url"):
        SentinelClient(base_url="", api_key="key")


def test_client_requires_api_key():
    with pytest.raises(ValueError, match="api_key"):
        SentinelClient(base_url=BASE, api_key="")


def test_client_invalid_public_key():
    with pytest.raises(ValueError, match="Invalid"):
        SentinelClient(base_url=BASE, api_key="key", public_key="not-valid")


def test_client_context_manager():
    with SentinelClient(base_url=BASE, api_key="key") as client:
        assert client.licenses is not None


async def test_async_client_context_manager():
    async with AsyncSentinelClient(base_url=BASE, api_key="key") as client:
        assert client.licenses is not None


def _make_signed_validation_response(signing_key, nonce, timestamp):
    """Helper to build a signed validation response."""
    from sentinel._signature import SignatureVerifier

    spki_prefix = bytes.fromhex("302a300506032b6570032100")
    b64_key = base64.b64encode(spki_prefix + bytes(signing_key.verify_key)).decode()
    verifier = SignatureVerifier(b64_key)

    canonical = verifier.build_canonical_payload(
        nonce=nonce,
        timestamp=timestamp,
        expiration="2026-01-01T00:00:00Z",
        server_count=1,
        max_servers=5,
        ip_count=1,
        max_ips=10,
        tier="Premium",
        entitlements=["feature_a", "feature_b"],
    )
    signed = signing_key.sign(canonical.encode("utf-8"))
    sig_b64 = base64.b64encode(signed.signature).decode()

    return {
        "timestamp": timestamp,
        "status": "OK",
        "type": "SUCCESS",
        "message": "License validated.",
        "result": {
            "validation": {
                "nonce": nonce,
                "timestamp": timestamp,
                "signature": sig_b64,
                "details": {
                    "expiration": "2026-01-01T00:00:00Z",
                    "serverCount": 1,
                    "maxServers": 5,
                    "ipCount": 1,
                    "maxIps": 10,
                    "tier": "Premium",
                    "entitlements": ["feature_a", "feature_b"],
                },
            }
        },
    }, b64_key


class TestSignatureVerification:
    @respx.mock
    def test_valid_signature_passes(self):
        sk = SigningKey.generate()
        now_ms = int(time.time() * 1000)
        resp_json, b64_key = _make_signed_validation_response(sk, "nonce-1", now_ms)

        respx.post(f"{BASE}/api/v2/licenses/validate").respond(200, json=resp_json)

        client = SentinelClient(base_url=BASE, api_key="key", public_key=b64_key)
        result = client.licenses.validate(ValidationRequest(product="p", server="s"))
        assert result.is_valid

    @respx.mock
    def test_tampered_response_fails(self):
        sk = SigningKey.generate()
        now_ms = int(time.time() * 1000)
        resp_json, b64_key = _make_signed_validation_response(sk, "nonce-2", now_ms)
        resp_json["result"]["validation"]["details"]["maxServers"] = 999

        respx.post(f"{BASE}/api/v2/licenses/validate").respond(200, json=resp_json)

        client = SentinelClient(base_url=BASE, api_key="key", public_key=b64_key)
        with pytest.raises(SignatureVerificationError):
            client.licenses.validate(ValidationRequest(product="p", server="s"))


class TestReplayProtection:
    @respx.mock
    def test_duplicate_nonce_rejected(self):
        sk = SigningKey.generate()
        now_ms = int(time.time() * 1000)
        resp_json, b64_key = _make_signed_validation_response(sk, "same-nonce", now_ms)

        respx.post(f"{BASE}/api/v2/licenses/validate").respond(200, json=resp_json)

        client = SentinelClient(base_url=BASE, api_key="key", public_key=b64_key)
        client.licenses.validate(ValidationRequest(product="p", server="s"))
        with pytest.raises(ReplayDetectedError, match="Duplicate nonce"):
            client.licenses.validate(ValidationRequest(product="p", server="s"))
