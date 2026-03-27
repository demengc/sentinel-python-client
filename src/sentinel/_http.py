from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from sentinel._exceptions import SentinelApiError, SentinelConnectionError


@dataclass
class ApiResponse:
    http_status: int
    type: str | None
    message: str | None
    result: dict[str, Any] | None


def _parse_response(
    status_code: int,
    body: str,
    headers: httpx.Headers,
    allowed_statuses: set[int] | None,
) -> ApiResponse:
    if status_code == 204:
        return ApiResponse(http_status=204, type=None, message=None, result=None)

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError) as e:
        raise SentinelApiError(
            http_status=status_code, type=None, message="Failed to parse response body"
        ) from e

    resp_type = data.get("type")
    message = data.get("message")
    result = data.get("result") if isinstance(data.get("result"), dict) else None

    if 200 <= status_code < 300:
        return ApiResponse(http_status=status_code, type=resp_type, message=message, result=result)

    if allowed_statuses and status_code in allowed_statuses:
        return ApiResponse(http_status=status_code, type=resp_type, message=message, result=result)

    retry_after: float | None = None
    if status_code == 429:
        raw = headers.get("X-Rate-Limit-Retry-After-Seconds")
        if raw is not None:
            try:
                retry_after = int(raw)
            except ValueError:
                pass

    raise SentinelApiError(
        http_status=status_code,
        type=resp_type,
        message=message or "Unknown error",
        retry_after_seconds=retry_after,
    )


def _build_url(
    base_url: str,
    path: str,
    query_params: dict[str, str] | None = None,
    multi_query_params: dict[str, list[str]] | None = None,
) -> str:
    url = base_url + path
    if multi_query_params:
        parts: list[str] = []
        for key in sorted(multi_query_params):
            for val in sorted(multi_query_params[key]):
                parts.append(f"{urlencode({key: val})}")
        url += "?" + "&".join(parts)
        return url
    if query_params:
        sorted_params = sorted(query_params.items())
        url += "?" + urlencode(sorted_params)
    return url


class SentinelHttpClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        if http_client is not None:
            self._client = http_client
        else:
            self._client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=connect_timeout, read=read_timeout, write=5.0, pool=5.0
                ),
            )

    def request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | list[Any] | None = None,
        query_params: dict[str, str] | None = None,
        multi_query_params: dict[str, list[str]] | None = None,
        allowed_statuses: set[int] | None = None,
    ) -> ApiResponse:
        url = _build_url(self._base_url, path, query_params, multi_query_params)
        headers = {"Authorization": f"Bearer {self._api_key}"}
        kwargs: dict[str, Any] = {"headers": headers}

        if json_body is not None:
            headers["Content-Type"] = "application/json"
            kwargs["content"] = json.dumps(json_body)
        try:
            response = self._client.request(method, url, **kwargs)
        except httpx.TimeoutException as e:
            raise SentinelConnectionError("Failed to connect to Sentinel API", e) from e
        except httpx.NetworkError as e:
            raise SentinelConnectionError("Failed to connect to Sentinel API", e) from e

        return _parse_response(
            response.status_code, response.text, response.headers, allowed_statuses
        )

    def close(self) -> None:
        self._client.close()


class AsyncSentinelHttpClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        if http_client is not None:
            self._client = http_client
        else:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=connect_timeout, read=read_timeout, write=5.0, pool=5.0
                ),
            )

    async def request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | list[Any] | None = None,
        query_params: dict[str, str] | None = None,
        multi_query_params: dict[str, list[str]] | None = None,
        allowed_statuses: set[int] | None = None,
    ) -> ApiResponse:
        url = _build_url(self._base_url, path, query_params, multi_query_params)
        headers = {"Authorization": f"Bearer {self._api_key}"}
        kwargs: dict[str, Any] = {"headers": headers}

        if json_body is not None:
            headers["Content-Type"] = "application/json"
            kwargs["content"] = json.dumps(json_body)
        try:
            response = await self._client.request(method, url, **kwargs)
        except httpx.TimeoutException as e:
            raise SentinelConnectionError("Failed to connect to Sentinel API", e) from e
        except httpx.NetworkError as e:
            raise SentinelConnectionError("Failed to connect to Sentinel API", e) from e

        return _parse_response(
            response.status_code, response.text, response.headers, allowed_statuses
        )

    async def aclose(self) -> None:
        await self._client.aclose()
