import pytest
import respx

from sentinel._http import SentinelHttpClient
from sentinel.models.requests import (
    CreateLicenseRequest,
    ListLicensesRequest,
    UpdateLicenseRequest,
    ValidationRequest,
)
from sentinel.models.validation import ValidationResultType
from sentinel.services._license import LicenseService
from tests.conftest import (
    SAMPLE_API_SUCCESS,
    SAMPLE_PAGE_JSON,
    SAMPLE_VALIDATION_FAILURE_JSON,
    SAMPLE_VALIDATION_SUCCESS_JSON,
)

BASE = "https://sentinel.example.com"


@pytest.fixture
def http_client():
    return SentinelHttpClient(base_url=BASE, api_key="test-key")


@pytest.fixture
def service(http_client):
    return LicenseService(http_client=http_client)


class TestValidate:
    @respx.mock
    def test_success(self, service):
        respx.post(f"{BASE}/api/v2/licenses/validate").respond(
            200, json=SAMPLE_VALIDATION_SUCCESS_JSON
        )
        result = service.validate(ValidationRequest(product="prod_1", server="s1"))
        assert result.is_valid
        assert result.details is not None
        assert result.details.max_servers == 5

    @respx.mock
    def test_failure(self, service):
        respx.post(f"{BASE}/api/v2/licenses/validate").respond(
            403, json=SAMPLE_VALIDATION_FAILURE_JSON
        )
        result = service.validate(ValidationRequest(product="prod_1", server="s1"))
        assert not result.is_valid
        assert result.type == ValidationResultType.EXPIRED_LICENSE


class TestCrud:
    @respx.mock
    def test_create(self, service):
        respx.post(f"{BASE}/api/v2/licenses").respond(200, json=SAMPLE_API_SUCCESS)
        lic = service.create(CreateLicenseRequest(product="prod_1"))
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    def test_get(self, service):
        respx.get(f"{BASE}/api/v2/licenses/KEY-1").respond(200, json=SAMPLE_API_SUCCESS)
        lic = service.get("KEY-1")
        assert lic.id == "lic_123"

    @respx.mock
    def test_list(self, service):
        respx.get(url__startswith=f"{BASE}/api/v2/licenses").respond(
            200,
            json={
                "type": "SUCCESS",
                "message": "OK",
                "result": SAMPLE_PAGE_JSON,
            },
        )
        page = service.list(ListLicensesRequest())
        assert page.total_elements == 1
        assert len(page.content) == 1

    @respx.mock
    def test_update(self, service):
        respx.patch(f"{BASE}/api/v2/licenses/KEY-1").respond(200, json=SAMPLE_API_SUCCESS)
        lic = service.update("KEY-1", UpdateLicenseRequest(max_servers=10))
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    def test_delete(self, service):
        respx.delete(f"{BASE}/api/v2/licenses/KEY-1").respond(204)
        service.delete("KEY-1")

    @respx.mock
    def test_regenerate_key(self, service):
        respx.post(url__startswith=f"{BASE}/api/v2/licenses/KEY-1/regenerate-key").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        lic = service.regenerate_key("KEY-1")
        assert lic.key == "KEY-ABC-123"

    @respx.mock
    def test_regenerate_key_with_new_key(self, service):
        respx.post(url__startswith=f"{BASE}/api/v2/licenses/KEY-1/regenerate-key").respond(
            200, json=SAMPLE_API_SUCCESS
        )
        lic = service.regenerate_key("KEY-1", new_key="NEW-KEY")
        assert lic.key == "KEY-ABC-123"
