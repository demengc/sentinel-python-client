from __future__ import annotations

from sentinel._http import SentinelHttpClient
from sentinel.models.license import License, SubUser

_BASE_PATH = "/api/v2/licenses"


class LicenseConnectionOperations:
    def __init__(self, http_client: SentinelHttpClient) -> None:
        self._http = http_client

    def add(self, key: str, connections: dict[str, str]) -> License:
        resp = self._http.request("POST", f"{_BASE_PATH}/{key}/connections", json_body=connections)
        return License.model_validate(resp.result["license"])

    def remove(self, key: str, platforms: set[str]) -> License:
        resp = self._http.request(
            "DELETE",
            f"{_BASE_PATH}/{key}/connections",
            multi_query_params={"platforms": sorted(platforms)},
        )
        return License.model_validate(resp.result["license"])


class LicenseServerOperations:
    def __init__(self, http_client: SentinelHttpClient) -> None:
        self._http = http_client

    def add(self, key: str, identifiers: set[str]) -> License:
        resp = self._http.request(
            "POST", f"{_BASE_PATH}/{key}/servers", json_body=sorted(identifiers)
        )
        return License.model_validate(resp.result["license"])

    def remove(self, key: str, identifiers: set[str]) -> License:
        resp = self._http.request(
            "DELETE",
            f"{_BASE_PATH}/{key}/servers",
            multi_query_params={"servers": sorted(identifiers)},
        )
        return License.model_validate(resp.result["license"])


class LicenseIpOperations:
    def __init__(self, http_client: SentinelHttpClient) -> None:
        self._http = http_client

    def add(self, key: str, addresses: set[str]) -> License:
        resp = self._http.request("POST", f"{_BASE_PATH}/{key}/ips", json_body=sorted(addresses))
        return License.model_validate(resp.result["license"])

    def remove(self, key: str, addresses: set[str]) -> License:
        resp = self._http.request(
            "DELETE",
            f"{_BASE_PATH}/{key}/ips",
            multi_query_params={"ips": sorted(addresses)},
        )
        return License.model_validate(resp.result["license"])


class LicenseSubUserOperations:
    def __init__(self, http_client: SentinelHttpClient) -> None:
        self._http = http_client

    def add(self, key: str, sub_users: list[SubUser]) -> License:
        body = [su.model_dump() for su in sub_users]
        resp = self._http.request("POST", f"{_BASE_PATH}/{key}/sub-users", json_body=body)
        return License.model_validate(resp.result["license"])

    def remove(self, key: str, sub_users: list[SubUser]) -> License:
        body = [su.model_dump() for su in sub_users]
        resp = self._http.request("POST", f"{_BASE_PATH}/{key}/sub-users/remove", json_body=body)
        return License.model_validate(resp.result["license"])
