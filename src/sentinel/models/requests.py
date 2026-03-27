from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sentinel.models.license import SubUser


class _ClearValue:
    """Sentinel indicating a field should be cleared in the API."""

    _instance: _ClearValue | None = None

    def __new__(cls) -> _ClearValue:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "CLEAR"


CLEAR: Any = _ClearValue()
"""Pass as a field value in :class:`UpdateLicenseRequest` to clear the stored value.
Sends the appropriate empty/reset value per field type (empty string for text fields,
empty collection for collection fields, epoch for expiration)."""

CLEAR_EXPIRATION = datetime(1970, 1, 1, tzinfo=UTC)
"""Pass as ``expiration`` in :class:`UpdateLicenseRequest` to clear a license's expiration
(i.e. set it to never expire). The API interprets the Unix epoch as "no expiration"."""


@dataclass(frozen=True)
class CreateLicenseRequest:
    product: str
    key: str | None = None
    tier: str | None = None
    expiration: datetime | None = None
    max_servers: int | None = None
    max_ips: int | None = None
    note: str | None = None
    connections: dict[str, str] | None = None
    additional_entitlements: set[str] | None = None

    def to_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {"product": self.product}
        if self.key is not None:
            body["key"] = self.key
        if self.tier is not None:
            body["tier"] = self.tier
        if self.expiration is not None:
            body["expiration"] = self.expiration.isoformat()
        if self.max_servers is not None:
            body["maxServers"] = self.max_servers
        if self.max_ips is not None:
            body["maxIps"] = self.max_ips
        if self.note is not None:
            body["note"] = self.note
        if self.connections is not None:
            body["connections"] = self.connections
        if self.additional_entitlements is not None:
            body["additionalEntitlements"] = list(self.additional_entitlements)
        return body


_CLEAR_JSON_VALUES: dict[str, Any] = {
    "connections": {},
    "subUsers": [],
    "servers": [],
    "ips": [],
    "additionalEntitlements": [],
    "expiration": datetime(1970, 1, 1, tzinfo=UTC).isoformat(),
}

_FIELD_TO_JSON: dict[str, str] = {
    "product": "product",
    "tier": "tier",
    "expiration": "expiration",
    "max_servers": "maxServers",
    "max_ips": "maxIps",
    "note": "note",
    "blacklist_reason": "blacklistReason",
    "connections": "connections",
    "sub_users": "subUsers",
    "servers": "servers",
    "ips": "ips",
    "additional_entitlements": "additionalEntitlements",
}


@dataclass
class UpdateLicenseRequest:
    product: str | None = None
    tier: str | None = None
    expiration: datetime | None = None
    max_servers: int | None = None
    max_ips: int | None = None
    note: str | None = None
    blacklist_reason: str | None = None
    connections: dict[str, str] | None = None
    sub_users: list[SubUser] | None = None
    servers: set[str] | None = None
    ips: set[str] | None = None
    additional_entitlements: set[str] | None = None

    def to_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            json_key = _FIELD_TO_JSON.get(f.name, f.name)
            if isinstance(value, _ClearValue):
                body[json_key] = _CLEAR_JSON_VALUES.get(json_key, "")
            elif value is not None:
                if isinstance(value, datetime):
                    body[json_key] = value.isoformat()
                elif isinstance(value, set):
                    body[json_key] = list(value)
                elif isinstance(value, list):
                    body[json_key] = [
                        item.model_dump() if hasattr(item, "model_dump") else item
                        for item in value
                    ]
                else:
                    body[json_key] = value
        return body


@dataclass(frozen=True)
class ListLicensesRequest:
    product: str | None = None
    status: str | None = None
    query: str | None = None
    platform: str | None = None
    value: str | None = None
    server: str | None = None
    ip: str | None = None
    page: int = 0
    size: int = 50

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.product is not None:
            params["product"] = self.product
        if self.status is not None:
            params["status"] = self.status
        if self.query is not None:
            params["query"] = self.query
        if self.platform is not None:
            params["platform"] = self.platform
        if self.value is not None:
            params["value"] = self.value
        if self.server is not None:
            params["server"] = self.server
        if self.ip is not None:
            params["ip"] = self.ip
        params["page"] = str(self.page)
        params["size"] = str(self.size)
        return params


@dataclass(frozen=True)
class ValidationRequest:
    product: str
    key: str | None = None
    server: str | None = None
    ip: str | None = None
    connection_platform: str | None = None
    connection_value: str | None = None

    def to_body(self) -> dict[str, str]:
        body: dict[str, str] = {"product": self.product}
        if self.key is not None:
            body["key"] = self.key
        if self.server is not None:
            body["server"] = self.server
        if self.ip is not None:
            body["ip"] = self.ip
        if self.connection_platform is not None:
            body["connectionPlatform"] = self.connection_platform
        if self.connection_value is not None:
            body["connectionValue"] = self.connection_value
        return body
