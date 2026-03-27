import httpx
import pytest
import respx

from sentinel._exceptions import SentinelApiError, SentinelConnectionError
from sentinel._http import AsyncSentinelHttpClient, SentinelHttpClient

BASE = "https://sentinel.example.com"


class TestSentinelHttpClient:
    def _make_client(self, transport=None):
        http_client = httpx.Client(transport=transport) if transport else None
        return SentinelHttpClient(
            base_url=BASE,
            api_key="test-key",
            connect_timeout=5.0,
            read_timeout=10.0,
            http_client=http_client,
        )

    @respx.mock
    def test_get_request(self):
        route = respx.get(f"{BASE}/api/v2/licenses/KEY-1").respond(
            200,
            json={
                "type": "SUCCESS",
                "message": "OK",
                "result": {"license": {"id": "1"}},
            },
        )
        client = self._make_client()
        resp = client.request("GET", "/api/v2/licenses/KEY-1")
        assert resp.type == "SUCCESS"
        assert resp.result["license"]["id"] == "1"
        assert route.called

    @respx.mock
    def test_post_with_body(self):
        route = respx.post(f"{BASE}/api/v2/licenses").respond(
            200,
            json={"type": "SUCCESS", "message": "Created", "result": {"license": {"id": "2"}}},
        )
        client = self._make_client()
        resp = client.request("POST", "/api/v2/licenses", json_body={"product": "p1"})
        assert resp.type == "SUCCESS"
        req = route.calls[0].request
        assert req.headers["content-type"] == "application/json"
        assert req.headers["authorization"] == "Bearer test-key"

    @respx.mock
    def test_query_params(self):
        route = respx.get(url__startswith=f"{BASE}/api/v2/licenses").respond(
            200,
            json={"type": "SUCCESS", "message": "OK", "result": None},
        )
        client = self._make_client()
        client.request("GET", "/api/v2/licenses", query_params={"page": "0", "size": "50"})
        assert "page=0" in str(route.calls[0].request.url)

    @respx.mock
    def test_api_error_401(self):
        respx.get(f"{BASE}/api/v2/licenses/X").respond(
            401,
            json={"type": "UNAUTHORIZED", "message": "Bad API key", "result": None},
        )
        client = self._make_client()
        with pytest.raises(SentinelApiError) as exc_info:
            client.request("GET", "/api/v2/licenses/X")
        assert exc_info.value.http_status == 401

    @respx.mock
    def test_api_error_429_retry_after(self):
        respx.get(f"{BASE}/api/v2/licenses/X").respond(
            429,
            json={"type": "RATE_LIMITED", "message": "Slow down", "result": None},
            headers={"X-Rate-Limit-Retry-After-Seconds": "30"},
        )
        client = self._make_client()
        with pytest.raises(SentinelApiError) as exc_info:
            client.request("GET", "/api/v2/licenses/X")
        assert exc_info.value.retry_after_seconds == 30

    @respx.mock
    def test_allowed_status(self):
        respx.post(f"{BASE}/api/v2/licenses/validate").respond(
            403,
            json={"type": "EXPIRED_LICENSE", "message": "Expired", "result": None},
        )
        client = self._make_client()
        resp = client.request("POST", "/api/v2/licenses/validate", allowed_statuses={403})
        assert resp.http_status == 403
        assert resp.type == "EXPIRED_LICENSE"

    @respx.mock
    def test_delete_204(self):
        respx.delete(f"{BASE}/api/v2/licenses/KEY-1").respond(204)
        client = self._make_client()
        resp = client.request("DELETE", "/api/v2/licenses/KEY-1")
        assert resp.http_status == 204
        assert resp.result is None

    def test_strips_trailing_slash(self):
        client = SentinelHttpClient(
            base_url="https://sentinel.example.com/",
            api_key="key",
        )
        assert client._base_url == "https://sentinel.example.com"

    @respx.mock
    def test_connection_error(self):
        respx.get(f"{BASE}/api/v2/licenses/X").mock(side_effect=httpx.ConnectError("refused"))
        client = self._make_client()
        with pytest.raises(SentinelConnectionError, match="Failed to connect"):
            client.request("GET", "/api/v2/licenses/X")


class TestAsyncSentinelHttpClient:
    @respx.mock
    async def test_get_request(self):
        respx.get(f"{BASE}/api/v2/licenses/KEY-1").respond(
            200,
            json={"type": "SUCCESS", "message": "OK", "result": {"license": {"id": "1"}}},
        )
        client = AsyncSentinelHttpClient(base_url=BASE, api_key="test-key")
        resp = await client.request("GET", "/api/v2/licenses/KEY-1")
        assert resp.type == "SUCCESS"

    @respx.mock
    async def test_api_error(self):
        respx.get(f"{BASE}/api/v2/licenses/X").respond(
            500,
            json={"type": "INTERNAL_ERROR", "message": "Oops", "result": None},
        )
        client = AsyncSentinelHttpClient(base_url=BASE, api_key="test-key")
        with pytest.raises(SentinelApiError) as exc_info:
            await client.request("GET", "/api/v2/licenses/X")
        assert exc_info.value.http_status == 500
