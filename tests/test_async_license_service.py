import pytest
import respx

from sentinel._http import AsyncSentinelHttpClient
from sentinel.models.requests import CreateLicenseRequest, ListLicensesRequest, ValidationRequest
from sentinel.models.validation import ValidationResultType
from sentinel.services._async_license import AsyncLicenseService
from tests.conftest import (
    SAMPLE_API_SUCCESS,
    SAMPLE_PAGE_JSON,
    SAMPLE_VALIDATION_FAILURE_JSON,
    SAMPLE_VALIDATION_SUCCESS_JSON,
)

BASE = "https://sentinel.example.com"


@pytest.fixture
def http_client():
    return AsyncSentinelHttpClient(base_url=BASE, api_key="test-key")


@pytest.fixture
def service(http_client):
    return AsyncLicenseService(http_client=http_client)


class TestAsyncValidate:
    @respx.mock
    async def test_success(self, service):
        respx.post(f"{BASE}/api/v2/licenses/validate").respond(
            200, json=SAMPLE_VALIDATION_SUCCESS_JSON
        )
        result = await service.validate(ValidationRequest(product="prod_1", server="s1"))
        assert result.is_valid

    @respx.mock
    async def test_failure(self, service):
        respx.post(f"{BASE}/api/v2/licenses/validate").respond(
            403, json=SAMPLE_VALIDATION_FAILURE_JSON
        )
        result = await service.validate(ValidationRequest(product="prod_1", server="s1"))
        assert not result.is_valid
        assert result.type == ValidationResultType.EXPIRED_LICENSE


class TestAsyncCrud:
    @respx.mock
    async def test_create(self, service):
        respx.post(f"{BASE}/api/v2/licenses").respond(200, json=SAMPLE_API_SUCCESS)
        lic = await service.create(CreateLicenseRequest(product="prod_1"))
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    async def test_get(self, service):
        respx.get(f"{BASE}/api/v2/licenses/KEY-1").respond(200, json=SAMPLE_API_SUCCESS)
        lic = await service.get("KEY-1")
        assert lic.id == "lic_123"

    @respx.mock
    async def test_delete(self, service):
        respx.delete(f"{BASE}/api/v2/licenses/KEY-1").respond(204)
        await service.delete("KEY-1")

    @respx.mock
    async def test_list(self, service):
        respx.get(url__startswith=f"{BASE}/api/v2/licenses").respond(
            200,
            json={"type": "SUCCESS", "message": "OK", "result": SAMPLE_PAGE_JSON},
        )
        page = await service.list(ListLicensesRequest())
        assert page.total_elements == 1
