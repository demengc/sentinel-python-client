from datetime import UTC, datetime

from sentinel.models.requests import (
    CLEAR,
    CLEAR_EXPIRATION,
    CreateLicenseRequest,
    ListLicensesRequest,
    UpdateLicenseRequest,
    ValidationRequest,
)


class TestCreateLicenseRequest:
    def test_minimal(self):
        req = CreateLicenseRequest(product="prod_1")
        assert req.product == "prod_1"
        assert req.key is None

    def test_full(self):
        req = CreateLicenseRequest(
            product="prod_1",
            key="KEY-123",
            tier="tier_1",
            expiration=datetime(2026, 1, 1, tzinfo=UTC),
            max_servers=5,
            max_ips=10,
            note="Test",
            connections={"discord": "123"},
            additional_entitlements={"extra"},
        )
        assert req.key == "KEY-123"
        assert req.max_servers == 5

    def test_to_body_omits_none(self):
        req = CreateLicenseRequest(product="prod_1")
        body = req.to_body()
        assert body == {"product": "prod_1"}

    def test_to_body_includes_set_fields(self):
        req = CreateLicenseRequest(
            product="prod_1",
            key="KEY-1",
            expiration=datetime(2026, 1, 1, tzinfo=UTC),
        )
        body = req.to_body()
        assert body["product"] == "prod_1"
        assert body["key"] == "KEY-1"
        assert body["expiration"] == "2026-01-01T00:00:00+00:00"


class TestUpdateLicenseRequest:
    def test_tracks_set_fields(self):
        req = UpdateLicenseRequest(max_servers=10, note="Updated")
        body = req.to_body()
        assert body == {"maxServers": 10, "note": "Updated"}
        assert "product" not in body

    def test_allows_null_values(self):
        req = UpdateLicenseRequest(note=None)
        body = req.to_body()
        assert "note" not in body

    def test_clear_expiration(self):
        req = UpdateLicenseRequest(expiration=CLEAR_EXPIRATION)
        body = req.to_body()
        assert body["expiration"] == "1970-01-01T00:00:00+00:00"

    def test_clear_sends_empty_string_for_text_fields(self):
        req = UpdateLicenseRequest(note=CLEAR, blacklist_reason=CLEAR)
        body = req.to_body()
        assert body["note"] == ""
        assert body["blacklistReason"] == ""

    def test_clear_sends_empty_collection_for_collection_fields(self):
        req = UpdateLicenseRequest(
            connections=CLEAR,
            servers=CLEAR,
            ips=CLEAR,
            additional_entitlements=CLEAR,
        )
        body = req.to_body()
        assert body["connections"] == {}
        assert body["servers"] == []
        assert body["ips"] == []
        assert body["additionalEntitlements"] == []

    def test_clear_sends_epoch_for_expiration(self):
        req = UpdateLicenseRequest(expiration=CLEAR)
        body = req.to_body()
        assert body["expiration"] == "1970-01-01T00:00:00+00:00"

    def test_clear_mixed_with_values(self):
        req = UpdateLicenseRequest(note=CLEAR, max_servers=10)
        body = req.to_body()
        assert body["note"] == ""
        assert body["maxServers"] == 10
        assert "product" not in body

    def test_clear_is_singleton(self):
        from sentinel.models.requests import _ClearValue

        assert CLEAR is _ClearValue()

    def test_empty_request(self):
        req = UpdateLicenseRequest()
        body = req.to_body()
        assert body == {}


class TestListLicensesRequest:
    def test_defaults(self):
        req = ListLicensesRequest()
        params = req.to_query_params()
        assert params["page"] == "0"
        assert params["size"] == "50"

    def test_with_filters(self):
        req = ListLicensesRequest(product="prod_1", status="ACTIVE", page=2, size=25)
        params = req.to_query_params()
        assert params["product"] == "prod_1"
        assert params["status"] == "ACTIVE"
        assert params["page"] == "2"
        assert params["size"] == "25"

    def test_omits_none_filters(self):
        req = ListLicensesRequest()
        params = req.to_query_params()
        assert "product" not in params
        assert "query" not in params


class TestValidationRequest:
    def test_minimal(self):
        req = ValidationRequest(product="prod_1")
        assert req.product == "prod_1"
        assert req.key is None
        assert req.server is None

    def test_to_body(self):
        req = ValidationRequest(product="prod_1", key="KEY-1", server="server-1")
        body = req.to_body()
        assert body["product"] == "prod_1"
        assert body["key"] == "KEY-1"
        assert body["server"] == "server-1"

    def test_to_body_omits_none(self):
        req = ValidationRequest(product="prod_1")
        body = req.to_body()
        assert "key" not in body
        assert "ip" not in body
