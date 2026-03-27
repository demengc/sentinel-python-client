import httpx
import respx

from sentinel.util.public_ip import async_get_public_ip, get_public_ip

CHECKIP_URL = "https://checkip.amazonaws.com"


class TestSyncPublicIp:
    @respx.mock
    def test_success(self):
        respx.get(CHECKIP_URL).respond(200, text="203.0.113.42\n")
        assert get_public_ip() == "203.0.113.42"

    @respx.mock
    def test_returns_none_on_error(self):
        respx.get(CHECKIP_URL).respond(500)
        assert get_public_ip() is None

    @respx.mock
    def test_returns_none_on_timeout(self):
        respx.get(CHECKIP_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
        assert get_public_ip() is None

    @respx.mock
    def test_returns_none_on_empty(self):
        respx.get(CHECKIP_URL).respond(200, text="   \n")
        assert get_public_ip() is None


class TestAsyncPublicIp:
    @respx.mock
    async def test_success(self):
        respx.get(CHECKIP_URL).respond(200, text="203.0.113.42\n")
        assert await async_get_public_ip() == "203.0.113.42"

    @respx.mock
    async def test_returns_none_on_error(self):
        respx.get(CHECKIP_URL).respond(500)
        assert await async_get_public_ip() is None
