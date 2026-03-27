from __future__ import annotations

import base64

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from sentinel._exceptions import SignatureVerificationError


class SignatureVerifier:
    # X.509 SubjectPublicKeyInfo prefix for Ed25519 (OID 1.3.101.112)
    _SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")

    def __init__(self, base64_public_key: str) -> None:
        try:
            key_bytes = base64.b64decode(base64_public_key)
            if key_bytes[:12] == self._SPKI_PREFIX:
                raw_key = key_bytes[12:]
            else:
                raw_key = key_bytes
            self._verify_key = VerifyKey(raw_key)
        except Exception as e:
            raise ValueError(f"Invalid Ed25519 public key: {e}") from e

    def verify(
        self,
        signature_base64: str | None,
        nonce: str,
        timestamp: int,
        expiration: str | None,
        server_count: int,
        max_servers: int,
        ip_count: int,
        max_ips: int,
        tier: str | None,
        entitlements: list[str] | None,
    ) -> None:
        if signature_base64 is None:
            raise SignatureVerificationError(
                "Response signature is null but signature verification is enabled"
            )

        canonical = self.build_canonical_payload(
            nonce=nonce,
            timestamp=timestamp,
            expiration=expiration,
            server_count=server_count,
            max_servers=max_servers,
            ip_count=ip_count,
            max_ips=max_ips,
            tier=tier,
            entitlements=entitlements,
        )

        try:
            sig_bytes = base64.b64decode(signature_base64)
            self._verify_key.verify(canonical.encode("utf-8"), sig_bytes)
        except BadSignatureError:
            raise SignatureVerificationError("Signature verification failed")
        except SignatureVerificationError:
            raise
        except Exception as e:
            raise SignatureVerificationError(f"Signature verification error: {e}") from e

    def build_canonical_payload(
        self,
        nonce: str,
        timestamp: int,
        expiration: str | None,
        server_count: int,
        max_servers: int,
        ip_count: int,
        max_ips: int,
        tier: str | None,
        entitlements: list[str] | None,
    ) -> str:
        parts: list[str] = ["{"]
        parts.append('"entitlements":')
        if entitlements is None:
            parts.append("null")
        else:
            sorted_ent = sorted(entitlements)
            parts.append("[")
            parts.append(",".join(_json_string(e) for e in sorted_ent))
            parts.append("]")
        parts.append(f',"expiration":{_json_string(expiration)}')
        parts.append(f',"ipCount":{ip_count}')
        parts.append(f',"maxIps":{max_ips}')
        parts.append(f',"maxServers":{max_servers}')
        parts.append(f',"nonce":{_json_string(nonce)}')
        parts.append(f',"serverCount":{server_count}')
        parts.append(f',"tier":{_json_string(tier)}')
        parts.append(f',"timestamp":{timestamp}')
        parts.append("}")
        return "".join(parts)


def _json_string(value: str | None) -> str:
    if value is None:
        return "null"
    result = ['"']
    for ch in value:
        if ch == '"':
            result.append('\\"')
        elif ch == "\\":
            result.append("\\\\")
        elif ch == "\n":
            result.append("\\n")
        elif ch == "\r":
            result.append("\\r")
        elif ch == "\t":
            result.append("\\t")
        elif ord(ch) < 0x20:
            result.append(f"\\u{ord(ch):04x}")
        else:
            result.append(ch)
    result.append('"')
    return "".join(result)
