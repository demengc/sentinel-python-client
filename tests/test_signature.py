import base64

import pytest
from nacl.signing import SigningKey

from sentinel._exceptions import SignatureVerificationError
from sentinel._signature import SignatureVerifier


@pytest.fixture
def signing_key():
    return SigningKey.generate()


@pytest.fixture
def verifier(signing_key):
    public_key_bytes = bytes(signing_key.verify_key)
    # Ed25519 public key in X.509/SPKI DER encoding:
    # 30 2a 30 05 06 03 2b 65 70 03 21 00 + 32-byte key
    spki_prefix = bytes.fromhex("302a300506032b6570032100")
    spki_bytes = spki_prefix + public_key_bytes
    b64_key = base64.b64encode(spki_bytes).decode()
    return SignatureVerifier(b64_key)


def _sign(signing_key, payload: str) -> str:
    signed = signing_key.sign(payload.encode("utf-8"))
    return base64.b64encode(signed.signature).decode()


def test_verify_valid_signature(signing_key, verifier):
    canonical = verifier.build_canonical_payload(
        nonce="abc123",
        timestamp=1741262400000,
        expiration="2026-01-01T00:00:00Z",
        server_count=1,
        max_servers=5,
        ip_count=2,
        max_ips=10,
        tier="Premium",
        entitlements=["feature_b", "feature_a"],
    )
    sig = _sign(signing_key, canonical)
    verifier.verify(
        signature_base64=sig,
        nonce="abc123",
        timestamp=1741262400000,
        expiration="2026-01-01T00:00:00Z",
        server_count=1,
        max_servers=5,
        ip_count=2,
        max_ips=10,
        tier="Premium",
        entitlements=["feature_b", "feature_a"],
    )


def test_verify_tampered_signature(signing_key, verifier):
    canonical = verifier.build_canonical_payload(
        nonce="abc123",
        timestamp=1741262400000,
        expiration="2026-01-01T00:00:00Z",
        server_count=1,
        max_servers=5,
        ip_count=2,
        max_ips=10,
        tier="Premium",
        entitlements=["feature_a"],
    )
    sig = _sign(signing_key, canonical)
    with pytest.raises(SignatureVerificationError):
        verifier.verify(
            signature_base64=sig,
            nonce="abc123",
            timestamp=1741262400000,
            expiration="2026-01-01T00:00:00Z",
            server_count=999,
            max_servers=5,
            ip_count=2,
            max_ips=10,
            tier="Premium",
            entitlements=["feature_a"],
        )


def test_verify_null_signature(verifier):
    with pytest.raises(SignatureVerificationError, match="null"):
        verifier.verify(
            signature_base64=None,
            nonce="abc",
            timestamp=0,
            expiration=None,
            server_count=0,
            max_servers=0,
            ip_count=0,
            max_ips=0,
            tier=None,
            entitlements=None,
        )


def test_canonical_payload_sorted_keys(verifier):
    payload = verifier.build_canonical_payload(
        nonce="n",
        timestamp=100,
        expiration=None,
        server_count=0,
        max_servers=0,
        ip_count=0,
        max_ips=0,
        tier=None,
        entitlements=None,
    )
    assert payload == (
        '{"entitlements":null,"expiration":null,"ipCount":0,"maxIps":0,'
        '"maxServers":0,"nonce":"n","serverCount":0,"tier":null,"timestamp":100}'
    )


def test_canonical_payload_sorted_entitlements(verifier):
    payload = verifier.build_canonical_payload(
        nonce="n",
        timestamp=100,
        expiration=None,
        server_count=0,
        max_servers=0,
        ip_count=0,
        max_ips=0,
        tier=None,
        entitlements=["z", "a", "m"],
    )
    assert '"entitlements":["a","m","z"]' in payload


def test_canonical_payload_escapes_special_chars(verifier):
    payload = verifier.build_canonical_payload(
        nonce='a"b\\c\nd',
        timestamp=100,
        expiration=None,
        server_count=0,
        max_servers=0,
        ip_count=0,
        max_ips=0,
        tier=None,
        entitlements=None,
    )
    assert '"nonce":"a\\"b\\\\c\\nd"' in payload


def test_invalid_public_key():
    with pytest.raises(ValueError, match="Invalid"):
        SignatureVerifier("not-a-valid-key")
