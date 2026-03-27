from __future__ import annotations

import httpx

_CHECKIP_URL = "https://checkip.amazonaws.com"
_TIMEOUT = 5.0


def get_public_ip() -> str | None:
    try:
        response = httpx.get(_CHECKIP_URL, timeout=_TIMEOUT)
        if response.status_code != 200:
            return None
        ip = response.text.strip()
        return ip if ip else None
    except Exception:
        return None


async def async_get_public_ip() -> str | None:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(_CHECKIP_URL)
        if response.status_code != 200:
            return None
        ip = response.text.strip()
        return ip if ip else None
    except Exception:
        return None
