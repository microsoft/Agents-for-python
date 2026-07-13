# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from microsoft_agents.hosting.core import (
    AccessTokenProviderBase,
    AgentAuthConfiguration,
)

from ._models import SidecarConnectionSettings, SidecarRequestOptions
from ._token_expiry import SidecarTokenExpiry
from .errors.error_resources import SidecarAuthErrorResources as _Errors
from .sidecar_http_client import SidecarHttpClient

logger = logging.getLogger(__name__)

# Refresh slightly ahead of the real expiry so callers never receive a token
# that expires mid-flight.
_EXPIRY_BUFFER = timedelta(seconds=30)

# Hard upper bound on cached entries; protects memory when many distinct
# identities are served.
_MAX_CACHE_ENTRIES = 500


class _CachedToken:
    __slots__ = ("token", "expires_on")

    def __init__(self, token: str, expires_on: datetime):
        self.token = token
        self.expires_on = expires_on


class SidecarAuth(AccessTokenProviderBase):
    """
    Authentication provider that delegates token acquisition to the Microsoft
    Entra ID Agent Container (sidecar).

    Implements :class:`microsoft_agents.hosting.core.AccessTokenProviderBase` by
    translating each SDK token call into a sidecar request. The sidecar owns the
    agent credential and performs the full agentic identity chain
    (Blueprint -> Instance -> agentic User) internally, so this provider never
    handles secrets, certificates, or keys.
    """

    def __init__(
        self,
        configuration: AgentAuthConfiguration,
        *,
        sidecar_client: SidecarHttpClient | None = None,
    ):
        self._configuration = configuration
        self._settings = SidecarConnectionSettings.from_configuration(configuration)

        if sidecar_client is not None:
            self._sidecar_client = sidecar_client
        else:
            resolved_url = SidecarHttpClient.resolve_base_url(
                self._settings.sidecar_base_url
            )
            # SSRF safety: validate the resolved URL before sending any agent
            # identity context to it.
            SidecarHttpClient.validate_base_url(
                resolved_url, self._settings.bypass_local_network_restriction
            )
            self._sidecar_client = SidecarHttpClient(
                resolved_url,
                timeout=self._settings.request_timeout,
                retry_count=self._settings.retry_count,
                bypass_local_network_restriction=(
                    self._settings.bypass_local_network_restriction
                ),
            )

        self._token_cache: dict[str, _CachedToken] = {}

    @property
    def configuration(self) -> AgentAuthConfiguration:
        """The auth configuration this provider was created from.

        Exposed so provider-agnostic SDK code (e.g. the agentic token path in
        ``RestChannelServiceClientFactory``) can read connection-level settings
        such as the alternate-blueprint connection name without depending on a
        specific provider implementation.
        """
        return self._configuration

    @property
    def _service_name(self) -> str:
        return self._settings.service_name

    @property
    def _blueprint_service_name(self) -> str:
        return self._settings.blueprint_service_name

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        """
        Acquire a connection-level app-only access token from the sidecar.
        """
        options = SidecarRequestOptions(
            scopes=scopes,
            request_app_token=True,
            force_refresh=force_refresh,
        )
        return await self._get_cached_token(self._service_name, options)

    async def get_agentic_application_token(
        self, tenant_id: str, agent_app_instance_id: str
    ) -> str | None:
        """
        Acquire the Blueprint (agent application) token from the sidecar.
        """
        if not agent_app_instance_id:
            raise ValueError(str(_Errors.AgentApplicationInstanceIdRequired))

        options = SidecarRequestOptions(
            agent_identity=agent_app_instance_id,
            tenant=tenant_id,
        )
        return await self._get_cached_token(self._blueprint_service_name, options)

    async def get_agentic_instance_token(
        self, tenant_id: str, agent_app_instance_id: str
    ) -> tuple[str, str]:
        """
        Acquire the autonomous agent (instance) token for the configured resource.

        The sidecar performs the full Blueprint -> Instance chain internally and
        returns an app-only resource token.

        :return: A tuple of (instance token, instance token). The second element
            exists for protocol compatibility (SDK consumers unpack ``token, _``);
            there is no distinct blueprint token in the delegated model.
        """
        if not agent_app_instance_id:
            raise ValueError(str(_Errors.AgentApplicationInstanceIdRequired))

        options = SidecarRequestOptions(
            agent_identity=agent_app_instance_id,
            request_app_token=True,
            tenant=tenant_id,
            scopes=self._settings.scopes,
        )
        token = await self._get_cached_token(self._service_name, options)
        return token, token

    async def get_agentic_user_token(
        self,
        tenant_id: str,
        agent_app_instance_id: str,
        agentic_user_id: str,
        scopes: list[str],
    ) -> str | None:
        """
        Acquire an agentic user token for the configured resource.

        The sidecar performs the full agentic identity chain internally and
        returns the resource token for the agentic user. The user is identified by
        object id (``AgentUserId``) when ``agentic_user_id`` is a GUID, otherwise by
        UPN (``AgentUsername``).
        """
        if not agent_app_instance_id or not agentic_user_id:
            raise ValueError(str(_Errors.AgentApplicationInstanceIdAndUserIdRequired))

        is_object_id = self._is_guid(agentic_user_id)
        options = SidecarRequestOptions(
            agent_identity=agent_app_instance_id,
            agent_username=None if is_object_id else agentic_user_id,
            agent_user_id=agentic_user_id if is_object_id else None,
            tenant=tenant_id,
            scopes=scopes or self._settings.scopes,
        )
        return await self._get_cached_token(self._service_name, options)

    async def is_healthy(self) -> bool:
        """Check sidecar availability via the ``/healthz`` endpoint."""
        return await self._sidecar_client.is_healthy()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._sidecar_client.aclose()

    async def _get_cached_token(
        self, service_name: str, options: SidecarRequestOptions
    ) -> str:
        force_refresh = options.force_refresh is True
        cache_key = self._build_cache_key(service_name, options)

        cached = self._cache_get(cache_key, force_refresh)
        if cached is not None:
            return cached.token

        result = await self._sidecar_client.get_authorization_header_unauthenticated(
            service_name, options
        )
        self._cache_set(
            cache_key,
            _CachedToken(result.token, SidecarTokenExpiry.resolve(result.token)),
        )
        return result.token

    def _cache_get(self, cache_key: str, force_refresh: bool) -> _CachedToken | None:
        cached = self._token_cache.get(cache_key)
        if cached is not None:
            if (
                not force_refresh
                and cached.expires_on >= datetime.now(timezone.utc) + _EXPIRY_BUFFER
            ):
                return cached
            # Token is being force-refreshed or is at/near expiry; flush it.
            self._token_cache.pop(cache_key, None)
        return None

    def _cache_set(self, cache_key: str, token: _CachedToken) -> None:
        self._token_cache[cache_key] = token

        if len(self._token_cache) > _MAX_CACHE_ENTRIES:
            self._prune_expired_entries()
            if len(self._token_cache) > _MAX_CACHE_ENTRIES:
                self._evict_nearest_expiry()

    def _prune_expired_entries(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [
            key for key, value in self._token_cache.items() if value.expires_on <= now
        ]
        for key in expired:
            self._token_cache.pop(key, None)

    def _evict_nearest_expiry(self) -> None:
        overflow = len(self._token_cache) - _MAX_CACHE_ENTRIES
        if overflow <= 0:
            return
        nearest = sorted(
            self._token_cache.items(), key=lambda item: item[1].expires_on
        )[:overflow]
        for key, _ in nearest:
            self._token_cache.pop(key, None)

    @staticmethod
    def _build_cache_key(service_name: str, options: SidecarRequestOptions) -> str:
        if options.scopes:
            scopes = " ".join(sorted(set(options.scopes)))
        else:
            scopes = ""
        return "|".join(
            [
                service_name or "",
                options.agent_identity or "",
                options.agent_username or "",
                options.agent_user_id or "",
                options.tenant or "",
                "app" if options.request_app_token is True else "user",
                scopes,
            ]
        )

    @staticmethod
    def _is_guid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False
