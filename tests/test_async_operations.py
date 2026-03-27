import pytest
import respx

from sentinel._http import AsyncSentinelHttpClient
from sentinel.services._async_operations import (
    AsyncLicenseConnectionOperations,
    AsyncLicenseServerOperations,
)
from tests.conftest import SAMPLE_API_SUCCESS

BASE = "https://sentinel.example.com"


@pytest.fixture
def http_client():
    return AsyncSentinelHttpClient(base_url=BASE, api_key="test-key")


class TestAsyncConnectionOperations:
    @respx.mock
    async def test_add(self, http_client):
        respx.post(f"{BASE}/api/v2/licenses/KEY-1/connections").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        ops = AsyncLicenseConnectionOperations(http_client)
        lic = await ops.add("KEY-1", {"discord": "123"})
        assert lic.key == "KEY-ABC-123"


class TestAsyncServerOperations:
    @respx.mock
    async def test_add(self, http_client):
        respx.post(f"{BASE}/api/v2/licenses/KEY-1/servers").respond(200, json=SAMPLE_API_SUCCESS)
        ops = AsyncLicenseServerOperations(http_client)
        lic = await ops.add("KEY-1", {"server-1"})
        assert lic.key == "KEY-ABC-123"
