from __future__ import annotations

from datetime import timedelta

from sentinel._http import AsyncSentinelHttpClient
from sentinel._replay import ReplayProtector
from sentinel._signature import SignatureVerifier
from sentinel.services._async_license import AsyncLicenseService


class AsyncSentinelClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        public_key: str | None = None,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
        replay_protection_window: timedelta = timedelta(seconds=30),
        nonce_cache_size: int = 1000,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        if not api_key:
            raise ValueError("api_key is required")

        self._http = AsyncSentinelHttpClient(
            base_url=base_url,
            api_key=api_key,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
        )

        sig: SignatureVerifier | None = None
        replay: ReplayProtector | None = None
        if public_key is not None:
            sig = SignatureVerifier(public_key)
            replay = ReplayProtector(
                window_seconds=replay_protection_window.total_seconds(),
                max_size=nonce_cache_size,
            )

        self.licenses = AsyncLicenseService(
            http_client=self._http,
            signature_verifier=sig,
            replay_protector=replay,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncSentinelClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
