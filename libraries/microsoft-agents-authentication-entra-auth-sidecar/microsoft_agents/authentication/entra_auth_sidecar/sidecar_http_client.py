# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import os
from urllib.parse import quote, urlparse

import httpx

from ._models import (
    DEFAULT_RETRY_COUNT,
    DEFAULT_SIDECAR_BASE_URL,
    SidecarProblemDetails,
    SidecarRequestOptions,
    SidecarTokenResult,
)
from .errors import (
    SidecarAuthError,
    SidecarConfigurationError,
    SidecarUnavailableError,
)
from .errors.error_resources import SidecarAuthErrorResources as _Errors

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30.0
_HTTP_TIMEOUT_408 = 408
_HTTP_TOO_MANY_REQUESTS_429 = 429
_HTTP_NOT_FOUND_404 = 404
_HTTP_UNAUTHORIZED_401 = 401
_HTTP_BAD_REQUEST_400 = 400


class SidecarHttpClient:
    """
    Reusable HTTP client for communicating with the Microsoft Entra ID Agent
    Container (sidecar).

    Handles URL construction, query-parameter building, response parsing, retry
    with exponential backoff, and error handling.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_backoff_base: float = 2.0,
        bypass_local_network_restriction: bool = False,
    ):
        self._base_url = (base_url or self.resolve_base_url()).rstrip("/")
        # SSRF safety: validate the base URL on construction so direct users of
        # the (publicly exported) client get the same loopback/private guard that
        # ``SidecarAuth`` applies, before any agent identity context is sent.
        self.validate_base_url(self._base_url, bypass_local_network_restriction)
        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS
        self._retry_count = max(0, retry_count if retry_count is not None else 0)
        self._retry_backoff_base = retry_backoff_base
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout)
        )

    @staticmethod
    def resolve_base_url(configured_url: str | None = None) -> str:
        """
        Resolve the sidecar base URL.

        Resolution order: ``SIDECAR_URL`` environment variable > the configured
        value > the default (``http://localhost:5178``). Blank/whitespace values
        are treated as unset.
        """
        env_url = os.environ.get("SIDECAR_URL")
        if env_url and env_url.strip():
            return env_url.strip()
        if configured_url and configured_url.strip():
            return configured_url.strip()
        return DEFAULT_SIDECAR_BASE_URL

    @staticmethod
    def validate_base_url(
        resolved_url: str, bypass_local_network_restriction: bool
    ) -> None:
        """
        Validate that the resolved sidecar base URL is safe to call.

        The host must be a loopback or private network address unless
        ``bypass_local_network_restriction`` is set. A public/routable address is
        rejected to avoid sending agent credentials off-box (SSRF safety).
        """
        parsed = urlparse(resolved_url) if resolved_url else None
        if not parsed or not parsed.scheme or not parsed.hostname:
            raise SidecarAuthError(str(_Errors.InvalidBaseUrl.format(resolved_url)))

        if parsed.scheme not in ("http", "https"):
            raise SidecarAuthError(str(_Errors.InvalidBaseUrl.format(resolved_url)))

        if parsed.username or parsed.password:
            raise SidecarAuthError(
                str(_Errors.BaseUrlMustNotContainUserInfo.format(resolved_url))
            )

        if bypass_local_network_restriction:
            return

        if SidecarHttpClient._is_loopback_or_private_host(parsed.hostname):
            return

        raise SidecarAuthError(
            str(_Errors.BaseUrlNotLoopbackOrPrivate.format(resolved_url))
        )

    @staticmethod
    def _is_loopback_or_private_host(host: str) -> bool:
        lowered = host.lower()
        if lowered == "localhost" or lowered.endswith(".localhost"):
            return True

        # Strip IPv6 brackets if present.
        candidate = host
        if candidate.startswith("[") and candidate.endswith("]"):
            candidate = candidate[1:-1]

        try:
            ip = ipaddress.ip_address(candidate)
        except ValueError:
            # Any other DNS name cannot be verified as private here and must be
            # opted into via explicit configuration.
            return False

        return ip.is_loopback or ip.is_private or ip.is_link_local

    async def get_authorization_header_unauthenticated(
        self,
        service_name: str,
        options: SidecarRequestOptions | None = None,
    ) -> SidecarTokenResult:
        """
        Call ``GET /AuthorizationHeaderUnauthenticated/{serviceName}`` with the
        specified options. Used for app-only and agentic token acquisition.
        """
        url = self._build_url(
            f"/AuthorizationHeaderUnauthenticated/{quote(service_name, safe='')}",
            options,
        )
        return await self._send_and_parse(url)

    async def is_healthy(self) -> bool:
        """Check sidecar availability via ``GET /healthz``."""
        try:
            response = await self._http_client.get(
                f"{self._base_url}/healthz", timeout=self._timeout
            )
            return response.is_success
        except httpx.HTTPError:
            return False

    async def aclose(self) -> None:
        """Close the underlying HTTP client when this client owns it."""
        if self._owns_client:
            await self._http_client.aclose()

    def _build_url(self, path: str, options: SidecarRequestOptions | None) -> str:
        url = f"{self._base_url}{path}"
        if options is None:
            return url

        # AgentUsername (UPN) and AgentUserId (object id) are mutually exclusive
        # per the sidecar contract. Enforce the invariant centrally.
        if options.agent_username and options.agent_user_id:
            raise SidecarAuthError(str(_Errors.AgentUserIdAndUsernameMutuallyExclusive))

        query_params = self._build_query_params(options)
        if query_params:
            url += "?" + "&".join(query_params)

        return url

    @staticmethod
    def _build_query_params(options: SidecarRequestOptions) -> list[str]:
        query_params: list[str] = []

        if options.agent_identity:
            query_params.append(
                f"AgentIdentity={quote(options.agent_identity, safe='')}"
            )

        if options.agent_username:
            query_params.append(
                f"AgentUsername={quote(options.agent_username, safe='')}"
            )

        if options.agent_user_id:
            query_params.append(f"AgentUserId={quote(options.agent_user_id, safe='')}")

        for scope in options.scopes or []:
            if scope and scope.strip():
                query_params.append(f"optionsOverride.Scopes={quote(scope, safe='')}")

        if options.request_app_token is True:
            query_params.append("optionsOverride.RequestAppToken=true")

        if options.tenant:
            query_params.append(
                "optionsOverride.AcquireTokenOptions.Tenant="
                f"{quote(options.tenant, safe='')}"
            )

        if options.force_refresh is True:
            query_params.append("optionsOverride.AcquireTokenOptions.ForceRefresh=true")

        return query_params

    async def _send_and_parse(self, url: str) -> SidecarTokenResult:
        max_attempts = self._retry_count + 1
        request_path = urlparse(url).path

        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self._http_client.get(url, timeout=self._timeout)
            except (httpx.ConnectError, httpx.TimeoutException) as ex:
                if attempt >= max_attempts:
                    logger.error(
                        "Sidecar request to %s failed after %d attempt(s).",
                        request_path,
                        attempt,
                    )
                    raise SidecarUnavailableError(
                        str(_Errors.SidecarRequestFailed.format(attempt, str(ex)))
                    ) from ex
                logger.warning(
                    "Sidecar request to %s failed (attempt %d/%d); retrying.",
                    request_path,
                    attempt,
                    max_attempts,
                )
                await self._delay_before_retry(attempt)
                continue
            except httpx.HTTPError as ex:
                raise SidecarUnavailableError(
                    str(_Errors.SidecarRequestFailed.format(attempt, str(ex)))
                ) from ex

            status = response.status_code
            if not response.is_success:
                error_content = response.text
                if self._is_transient_status(status) and attempt < max_attempts:
                    logger.warning(
                        "Sidecar returned transient status %d from %s "
                        "(attempt %d/%d); retrying.",
                        status,
                        request_path,
                        attempt,
                        max_attempts,
                    )
                    await self._delay_before_retry(attempt)
                    continue

                self._raise_for_error(status, request_path, error_content)

            return self._parse_token_response(response.text)

    @staticmethod
    def _is_transient_status(status: int) -> bool:
        return (
            status == _HTTP_TIMEOUT_408
            or status == _HTTP_TOO_MANY_REQUESTS_429
            or status >= 500
        )

    async def _delay_before_retry(self, attempt: int) -> None:
        # Exponential backoff: base, base*2, base*4, ...
        delay = self._retry_backoff_base * (2 ** (attempt - 1))
        await asyncio.sleep(delay)

    @staticmethod
    def _raise_for_error(status: int, request_path: str, content: str) -> None:
        problem = SidecarHttpClient._try_parse_problem_details(content)
        title = (
            problem.title if problem and problem.title else f"Sidecar returned {status}"
        )

        # Never surface problem.detail or the raw body: the sidecar can echo request
        # parameters (UPN, object id, tenant) into them. Log and raise only the
        # non-sensitive title and status.
        logger.error(
            "Sidecar returned error. Status: %d, Path: %s, Title: %s",
            status,
            request_path,
            problem.title if problem else "(none)",
        )

        full_message = str(_Errors.SidecarReturnedError.format(status, title))
        if status == _HTTP_NOT_FOUND_404:
            raise SidecarConfigurationError(full_message)
        if status == _HTTP_UNAUTHORIZED_401:
            raise SidecarAuthError(full_message)
        if status == _HTTP_BAD_REQUEST_400:
            raise ValueError(full_message)
        raise SidecarAuthError(full_message)

    @staticmethod
    def _parse_token_response(response_content: str) -> SidecarTokenResult:
        try:
            document = json.loads(response_content)
        except (json.JSONDecodeError, TypeError) as ex:
            raise SidecarAuthError(str(_Errors.SidecarResponseUnparsable)) from ex

        header_value = (
            document.get("authorizationHeader") if isinstance(document, dict) else None
        )
        if isinstance(header_value, str):
            trimmed = header_value.strip()
            if trimmed:
                scheme, separator, token = trimmed.partition(" ")
                if separator:
                    # "{scheme} {token}" form: the token after the separator must be
                    # non-empty.
                    token = token.strip()
                    if token:
                        return SidecarTokenResult(scheme, token)
                elif not SidecarHttpClient._is_known_auth_scheme(trimmed):
                    # No separator: treat the whole value as a raw token and default the
                    # scheme to Bearer. A lone scheme name (e.g. "Bearer") is not a valid
                    # token and falls through to the error below.
                    return SidecarTokenResult("Bearer", trimmed)

        raise SidecarAuthError(str(_Errors.SidecarResponseMissingHeader))

    @staticmethod
    def _is_known_auth_scheme(value: str) -> bool:
        return value.lower() in ("bearer", "pop")

    @staticmethod
    def _try_parse_problem_details(content: str) -> SidecarProblemDetails | None:
        if not content:
            return None
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return SidecarProblemDetails.from_dict(data)
        except (json.JSONDecodeError, TypeError):
            return None
        return None
