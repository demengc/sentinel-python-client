import pytest
import respx

from sentinel._http import SentinelHttpClient
from sentinel.models.license import SubUser
from sentinel.services._operations import (
    LicenseConnectionOperations,
    LicenseIpOperations,
    LicenseServerOperations,
    LicenseSubUserOperations,
)
from tests.conftest import SAMPLE_API_SUCCESS

BASE = "https://sentinel.example.com"


@pytest.fixture
def http_client():
    return SentinelHttpClient(base_url=BASE, api_key="test-key")


class TestConnectionOperations:
    @respx.mock
    def test_add(self, http_client):
        respx.post(f"{BASE}/api/v2/licenses/KEY-1/connections").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        ops = LicenseConnectionOperations(http_client)
        lic = ops.add("KEY-1", {"discord": "123"})
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    def test_remove(self, http_client):
        respx.delete(url__startswith=f"{BASE}/api/v2/licenses/KEY-1/connections").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        ops = LicenseConnectionOperations(http_client)
        lic = ops.remove("KEY-1", {"discord"})
        assert lic.key == "KEY-ABC-123"


class TestServerOperations:
    @respx.mock
    def test_add(self, http_client):
        respx.post(f"{BASE}/api/v2/licenses/KEY-1/servers").respond(200, json=SAMPLE_API_SUCCESS)
        ops = LicenseServerOperations(http_client)
        lic = ops.add("KEY-1", {"server-1"})
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    def test_remove(self, http_client):
        respx.delete(url__startswith=f"{BASE}/api/v2/licenses/KEY-1/servers").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        ops = LicenseServerOperations(http_client)
        lic = ops.remove("KEY-1", {"server-1"})
        assert lic.key == "KEY-ABC-123"


class TestIpOperations:
    @respx.mock
    def test_add(self, http_client):
        respx.post(f"{BASE}/api/v2/licenses/KEY-1/ips").respond(200, json=SAMPLE_API_SUCCESS)
        ops = LicenseIpOperations(http_client)
        lic = ops.add("KEY-1", {"192.168.1.1"})
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    def test_remove(self, http_client):
        respx.delete(url__startswith=f"{BASE}/api/v2/licenses/KEY-1/ips").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        ops = LicenseIpOperations(http_client)
        lic = ops.remove("KEY-1", {"192.168.1.1"})
        assert lic.key == "KEY-ABC-123"


class TestSubUserOperations:
    @respx.mock
    def test_add(self, http_client):
        respx.post(f"{BASE}/api/v2/licenses/KEY-1/sub-users").respond(200, json=SAMPLE_API_SUCCESS)
        ops = LicenseSubUserOperations(http_client)
        lic = ops.add("KEY-1", [SubUser(platform="discord", value="123")])
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    def test_remove(self, http_client):
        respx.post(f"{BASE}/api/v2/licenses/KEY-1/sub-users/remove").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        ops = LicenseSubUserOperations(http_client)
        lic = ops.remove("KEY-1", [SubUser(platform="discord", value="123")])
        assert lic.key == "KEY-ABC-123"
