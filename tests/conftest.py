import pytest

SAMPLE_LICENSE_JSON = {
    "license": {
        "id": "lic_123",
        "key": "KEY-ABC-123",
        "product": {
            "id": "prod_1",
            "name": "Test Product",
            "description": "A test product",
            "logoUrl": "https://example.com/logo.png",
        },
        "tier": {
            "name": "Premium",
            "entitlements": ["feature_a", "feature_b"],
        },
        "issuer": {
            "type": "USER",
            "id": "user_1",
            "displayName": "Admin",
        },
        "createdAt": "2025-01-01T00:00:00Z",
        "expiration": "2026-01-01T00:00:00Z",
        "maxServers": 5,
        "maxIps": 10,
        "note": "Test license",
        "connections": {"discord": "123456789"},
        "subUsers": [{"platform": "discord", "value": "987654321"}],
        "servers": {"server-1": "2025-01-01T00:00:00Z"},
        "ips": {"192.168.1.1": "2025-01-01T00:00:00Z"},
        "additionalEntitlements": ["extra_feature"],
        "entitlements": ["feature_a", "feature_b", "extra_feature"],
        "blacklist": None,
    }
}

SAMPLE_VALIDATION_SUCCESS_JSON = {
    "timestamp": 1741262400000,
    "status": "OK",
    "type": "SUCCESS",
    "message": "License validated.",
    "result": {
        "validation": {
            "nonce": "abc123nonce",
            "timestamp": 1741262400000,
            "signature": None,
            "details": {
                "expiration": "2026-01-01T00:00:00Z",
                "serverCount": 1,
                "maxServers": 5,
                "ipCount": 1,
                "maxIps": 10,
                "tier": "Premium",
                "entitlements": ["feature_a", "feature_b"],
            },
        }
    },
}

SAMPLE_VALIDATION_FAILURE_JSON = {
    "timestamp": 1741262400000,
    "status": "FORBIDDEN",
    "type": "EXPIRED_LICENSE",
    "message": "License has expired.",
    "result": None,
}

SAMPLE_PAGE_JSON = {
    "page": {
        "content": [SAMPLE_LICENSE_JSON["license"]],
        "page": {
            "size": 50,
            "number": 0,
            "totalElements": 1,
            "totalPages": 1,
        },
    }
}

SAMPLE_API_SUCCESS = {
    "timestamp": 1741262400000,
    "status": "OK",
    "type": "SUCCESS",
    "message": "Operation successful.",
    "result": SAMPLE_LICENSE_JSON,
}


@pytest.fixture
def sample_license_json():
    return SAMPLE_LICENSE_JSON
