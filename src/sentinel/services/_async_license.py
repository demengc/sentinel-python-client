from __future__ import annotations

from datetime import datetime

from sentinel._exceptions import SentinelApiError
from sentinel._http import ApiResponse, AsyncSentinelHttpClient
from sentinel._replay import ReplayProtector
from sentinel._signature import SignatureVerifier
from sentinel.models.license import License
from sentinel.models.page import Page
from sentinel.models.requests import (
    CreateLicenseRequest,
    ListLicensesRequest,
    UpdateLicenseRequest,
    ValidationRequest,
)
from sentinel.models.validation import (
    ValidationDetails,
    ValidationResult,
    ValidationResultType,
)
from sentinel.services._async_operations import (
    AsyncLicenseConnectionOperations,
    AsyncLicenseIpOperations,
    AsyncLicenseServerOperations,
    AsyncLicenseSubUserOperations,
)
from sentinel.services._license import _parse_failure_details

_BASE_PATH = "/api/v2/licenses"


class AsyncLicenseService:
    def __init__(
        self,
        http_client: AsyncSentinelHttpClient,
        signature_verifier: SignatureVerifier | None = None,
        replay_protector: ReplayProtector | None = None,
    ) -> None:
        self._http = http_client
        self._sig = signature_verifier
        self._replay = replay_protector
        self.connections = AsyncLicenseConnectionOperations(http_client)
        self.servers = AsyncLicenseServerOperations(http_client)
        self.ips = AsyncLicenseIpOperations(http_client)
        self.sub_users = AsyncLicenseSubUserOperations(http_client)

    async def validate(self, request: ValidationRequest) -> ValidationResult:
        body = request.to_body()
        if "server" not in body:
            import asyncio

            from sentinel.util.fingerprint import generate_fingerprint

            body["server"] = await asyncio.to_thread(generate_fingerprint)

        resp = await self._http.request(
            "POST", f"{_BASE_PATH}/validate", json_body=body, allowed_statuses={403}
        )

        if resp.http_status == 200:
            return self._parse_validation_success(resp)
        if resp.http_status == 403:
            return self._parse_validation_failure(resp)
        raise SentinelApiError(
            http_status=resp.http_status,
            type=resp.type,
            message=resp.message or "Unknown error",
        )

    async def create(self, request: CreateLicenseRequest) -> License:
        resp = await self._http.request("POST", _BASE_PATH, json_body=request.to_body())
        return License.model_validate(resp.require_result()["license"])

    async def get(self, key: str) -> License:
        resp = await self._http.request("GET", f"{_BASE_PATH}/{key}")
        return License.model_validate(resp.require_result()["license"])

    async def list(self, request: ListLicensesRequest) -> Page[License]:
        resp = await self._http.request("GET", _BASE_PATH, query_params=request.to_query_params())
        page_data = resp.require_result()["page"]
        licenses = [License.model_validate(item) for item in page_data["content"]]
        meta = page_data["page"]
        return Page(
            content=licenses,
            size=meta["size"],
            number=meta["number"],
            total_elements=meta["totalElements"],
            total_pages=meta["totalPages"],
        )

    async def update(self, key: str, request: UpdateLicenseRequest) -> License:
        resp = await self._http.request(
            "PATCH", f"{_BASE_PATH}/{key}", json_body=request.to_body()
        )
        return License.model_validate(resp.require_result()["license"])

    async def delete(self, key: str) -> None:
        await self._http.request("DELETE", f"{_BASE_PATH}/{key}")

    async def regenerate_key(self, key: str, new_key: str | None = None) -> License:
        params = {"newKey": new_key} if new_key else None
        resp = await self._http.request(
            "POST", f"{_BASE_PATH}/{key}/regenerate-key", query_params=params
        )
        return License.model_validate(resp.require_result()["license"])

    def _parse_validation_success(self, resp: ApiResponse) -> ValidationResult:
        validation = resp.require_result()["validation"]
        nonce = validation["nonce"]
        timestamp = validation["timestamp"]
        signature = validation.get("signature")
        details_data = validation["details"]

        expiration_str = details_data.get("expiration")
        expiration = datetime.fromisoformat(expiration_str) if expiration_str else None
        server_count = details_data["serverCount"]
        max_servers = details_data["maxServers"]
        ip_count = details_data["ipCount"]
        max_ips = details_data["maxIps"]
        tier = details_data.get("tier")

        raw_entitlements = details_data.get("entitlements")
        entitlements_list: list[str] | None = None
        entitlements_set: set[str] = set()
        if raw_entitlements is not None:
            entitlements_list = list(raw_entitlements)
            entitlements_set = set(raw_entitlements)

        details = ValidationDetails(
            expiration=expiration,
            server_count=server_count,
            max_servers=max_servers,
            ip_count=ip_count,
            max_ips=max_ips,
            tier=tier,
            entitlements=entitlements_set,
        )
        result = ValidationResult.success(details=details, message=resp.message or "")

        if self._sig is not None:
            self._sig.verify(
                signature_base64=signature,
                nonce=nonce,
                timestamp=timestamp,
                expiration=expiration_str,
                server_count=server_count,
                max_servers=max_servers,
                ip_count=ip_count,
                max_ips=max_ips,
                tier=tier,
                entitlements=entitlements_list,
            )
            if self._replay is not None:
                self._replay.check(nonce, timestamp)

        return result

    def _parse_validation_failure(self, resp: ApiResponse) -> ValidationResult:
        result_type = ValidationResultType.from_string(resp.type)
        if result_type == ValidationResultType.UNKNOWN:
            raise SentinelApiError(
                http_status=resp.http_status,
                type=resp.type,
                message=resp.message or "Unknown error",
            )
        failure_details = _parse_failure_details(result_type, resp.result)
        return ValidationResult.failure(
            type=result_type,
            message=resp.message or "",
            failure_details=failure_details,
        )
