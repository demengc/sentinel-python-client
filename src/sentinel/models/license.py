from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
    )


class LicenseProduct(_CamelModel):
    id: str
    name: str
    description: str | None = None
    logo_url: str | None = None


class LicenseTier(_CamelModel):
    id: str
    name: str | None = None
    entitlements: set[str] = set()


class LicenseIssuer(_CamelModel):
    type: str
    id: str
    display_name: str


class SubUser(_CamelModel):
    platform: str
    value: str


class BlacklistInfo(_CamelModel):
    timestamp: datetime
    reason: str | None = None


class License(_CamelModel):
    id: str
    key: str
    product: LicenseProduct
    tier: LicenseTier | None = None
    issuer: LicenseIssuer
    created_at: datetime
    expiration: datetime | None = None
    max_servers: int
    max_ips: int
    note: str | None = None
    connections: dict[str, str] = {}
    sub_users: list[SubUser] = []
    servers: dict[str, datetime] = {}
    ips: dict[str, datetime] = {}
    additional_entitlements: set[str] = set()
    entitlements: set[str] = set()
    blacklist: BlacklistInfo | None = None
