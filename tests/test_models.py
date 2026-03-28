from datetime import UTC, datetime

from sentinel.models.license import (
    BlacklistInfo,
    License,
    LicenseIssuer,
    LicenseProduct,
    LicenseTier,
    SubUser,
)


def test_license_product_from_json():
    data = {
        "id": "prod_1",
        "name": "Test Product",
        "description": "A test product",
        "logoUrl": "https://example.com/logo.png",
    }
    product = LicenseProduct.model_validate(data)
    assert product.id == "prod_1"
    assert product.name == "Test Product"
    assert product.description == "A test product"
    assert product.logo_url == "https://example.com/logo.png"


def test_license_product_nullable_fields():
    data = {"id": "prod_1", "name": "Test"}
    product = LicenseProduct.model_validate(data)
    assert product.description is None
    assert product.logo_url is None


def test_license_tier_from_json():
    data = {"name": "Premium", "entitlements": ["a", "b"]}
    tier = LicenseTier.model_validate(data)
    assert tier.name == "Premium"
    assert tier.entitlements == {"a", "b"}


def test_license_issuer_from_json():
    data = {"type": "USER", "id": "user_1", "displayName": "Admin"}
    issuer = LicenseIssuer.model_validate(data)
    assert issuer.type == "USER"
    assert issuer.id == "user_1"
    assert issuer.display_name == "Admin"


def test_sub_user_from_json():
    data = {"platform": "discord", "value": "123456789"}
    sub_user = SubUser.model_validate(data)
    assert sub_user.platform == "discord"
    assert sub_user.value == "123456789"


def test_blacklist_info_from_json():
    data = {"timestamp": "2025-06-01T00:00:00Z", "reason": "Violation"}
    info = BlacklistInfo.model_validate(data)
    assert info.timestamp == datetime(2025, 6, 1, tzinfo=UTC)
    assert info.reason == "Violation"


def test_blacklist_info_null_reason():
    data = {"timestamp": "2025-06-01T00:00:00Z", "reason": None}
    info = BlacklistInfo.model_validate(data)
    assert info.reason is None


def test_full_license_from_json(sample_license_json):
    lic = License.model_validate(sample_license_json["license"])
    assert lic.id == "lic_123"
    assert lic.key == "KEY-ABC-123"
    assert lic.product.name == "Test Product"
    assert lic.tier is not None
    assert lic.tier.name == "Premium"
    assert lic.issuer.display_name == "Admin"
    assert lic.created_at == datetime(2025, 1, 1, tzinfo=UTC)
    assert lic.expiration == datetime(2026, 1, 1, tzinfo=UTC)
    assert lic.max_servers == 5
    assert lic.max_ips == 10
    assert lic.note == "Test license"
    assert lic.connections == {"discord": "123456789"}
    assert len(lic.sub_users) == 1
    assert lic.sub_users[0].platform == "discord"
    assert lic.servers == {"server-1": datetime(2025, 1, 1, tzinfo=UTC)}
    assert lic.ips == {"192.168.1.1": datetime(2025, 1, 1, tzinfo=UTC)}
    assert "extra_feature" in lic.additional_entitlements
    assert "feature_a" in lic.entitlements
    assert lic.blacklist is None


def test_license_null_optional_fields():
    data = {
        "id": "lic_1",
        "key": "KEY-1",
        "product": {"id": "p1", "name": "P"},
        "tier": None,
        "issuer": {"type": "API", "id": "api_1", "displayName": "API Key"},
        "createdAt": "2025-01-01T00:00:00Z",
        "expiration": None,
        "maxServers": 0,
        "maxIps": 0,
        "note": None,
        "connections": {},
        "subUsers": [],
        "servers": {},
        "ips": {},
        "additionalEntitlements": [],
        "entitlements": [],
        "blacklist": None,
    }
    lic = License.model_validate(data)
    assert lic.tier is None
    assert lic.expiration is None
    assert lic.note is None
    assert lic.connections == {}
    assert lic.sub_users == []


def test_license_model_is_frozen():
    data = {
        "id": "lic_1",
        "key": "KEY-1",
        "product": {"id": "p1", "name": "P"},
        "tier": None,
        "issuer": {"type": "API", "id": "api_1", "displayName": "API Key"},
        "createdAt": "2025-01-01T00:00:00Z",
        "expiration": None,
        "maxServers": 0,
        "maxIps": 0,
        "note": None,
        "connections": {},
        "subUsers": [],
        "servers": {},
        "ips": {},
        "additionalEntitlements": [],
        "entitlements": [],
        "blacklist": None,
    }
    lic = License.model_validate(data)
    import pytest

    with pytest.raises(Exception):
        lic.key = "NEW"  # type: ignore[misc]
