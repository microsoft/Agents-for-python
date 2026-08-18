# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import logging
import threading
from typing import Any
from dataclasses import dataclass

from jwt import PyJWKClient, PyJWK, decode, get_unverified_header

from ..agent_auth_configuration import AgentAuthConfiguration
from ..authentication_constants import AuthenticationConstants
from ..claims_identity import ClaimsIdentity
from .._entra_issuers import (
    BOTFRAMEWORK_JWKS_URIS,
    effective_tenant,
    entra_issuer_info,
    is_gov_authority,
    jwks_login_host,
    well_known_first_party_issuers,
)

logger = logging.getLogger(__name__)


@dataclass
class _JwkClientCacheEntry:

    jwk_client: PyJWKClient
    lock: threading.Lock


class _JwkClientManager:
    """Helper class to manage PyJWKClient instances for different JWKS URIs, with caching and async-safety"""

    _cache: dict[str, _JwkClientCacheEntry]

    def __init__(self):
        self._cache = {}

    def _get_jwk_client(self, jwks_uri: str) -> _JwkClientCacheEntry:
        """Retrieves a PyJWKClient for the given JWKS URI, using a cache to
        avoid creating multiple clients for the same URI."""
        if jwks_uri not in self._cache:
            self._cache[jwks_uri] = _JwkClientCacheEntry(
                PyJWKClient(jwks_uri), threading.Lock()
            )
        return self._cache[jwks_uri]

    async def get_signing_key(self, jwks_uri: str, header: dict[str, Any]) -> PyJWK:
        """Retrieves the signing key from the JWK client for the given token header."""

        jwk_cache_entry = self._get_jwk_client(jwks_uri)

        # locking and creating a new thread seems strange,
        # but PyJWKClient.get_signing_key is synchronous, so we spawn another thread
        # to make the call non-blocking, allowing other queued coroutines to run in the meantime.
        # Meanwhile, the lock ensures safety for the PyJWKClient's underlying cache and
        # prevents duplicate calls to the JWKS endpoint for the same URI when multiple
        # coroutines are trying to get signing keys concurrently.

        def _helper():
            with jwk_cache_entry.lock:
                return jwk_cache_entry.jwk_client.get_signing_key(
                    header[AuthenticationConstants.KEY_ID_HEADER]
                )

        key = await asyncio.to_thread(_helper)
        return key


class JwtTokenValidator:
    """Utility class for validating JWT tokens using the PyJWT library and JWKs from a specified URI."""

    _jwk_client_manager = _JwkClientManager()

    def __init__(self, configuration: AgentAuthConfiguration):
        """Initializes the JwtTokenValidator with the given configuration.

        :param configuration: An instance of AgentAuthConfiguration containing the necessary settings for token validation.
        """
        self.configuration = configuration

    async def validate_token(self, token: str) -> ClaimsIdentity:
        """Validates a JWT token.

        The unverified token is used only to select the matching configured
        connection (by audience) for JWKS/tenant routing. All acceptance
        checks -- audience, tid-to-issuer binding (when the issuer is a
        recognized Entra issuer with a GUID tenant), and, when the matched
        connection opts in via ``VALIDATE_ISSUER``, the issuer allow-list --
        are evaluated against the signature-verified claims.

        :param token: The JWT token to validate.
        :return: A ClaimsIdentity object containing the token's claims if validation is successful.
        :raises ValueError: If the token, audience, tenant binding, or (when opted in) issuer is not valid.
        """

        logger.debug("Validating JWT token.")
        header = get_unverified_header(token)
        unverified_payload: dict = decode(token, options={"verify_signature": False})

        # Route by the unverified audience only where the selected connection's
        # cloud affects JWKS lookup. Public-cloud routing retains the legacy
        # root-configuration endpoint for backward-compatible network egress.
        # This is routing only -- final acceptance is checked against the
        # signature-verified claims below.
        routing_config = (
            self.configuration._jwt_patch_find_connection(
                unverified_payload.get(AuthenticationConstants.AUDIENCE_CLAIM)
            )
            or self.configuration
        )
        jwks_uri = _build_jwks_uri(
            unverified_payload.get(AuthenticationConstants.ISSUER_CLAIM),
            self.configuration,
            routing_config,
        )
        key = await self._jwk_client_manager.get_signing_key(jwks_uri, header)

        decoded_token = decode(
            token,
            key=key,
            algorithms=["RS256"],
            leeway=300.0,
            options={"verify_aud": False},
        )

        aud = decoded_token.get(AuthenticationConstants.AUDIENCE_CLAIM, "")
        if not self.configuration._jwt_patch_is_valid_aud(aud):
            logger.warning("JWT audience not accepted.")
            raise ValueError("Invalid audience.")

        matched_config = (
            self.configuration._jwt_patch_find_connection(aud) or routing_config
        )

        # Issuer allow-list validation is explicit opt-in
        # (AgentAuthConfiguration.VALIDATE_ISSUER) to preserve backward
        # compatibility for existing deployments. Tid-to-issuer binding,
        # however, is always enforced per issue #626: it only engages when
        # the (verified) issuer is itself a recognized Entra issuer carrying
        # a GUID tenant, so Bot Framework/non-Entra and tenant-alias issuers
        # are unaffected, and a missing ``tid`` claim skips the check rather
        # than failing closed.
        if matched_config.VALIDATE_ISSUER:
            _validate_issuer(
                decoded_token.get(AuthenticationConstants.ISSUER_CLAIM), matched_config
            )
        _validate_tenant_binding(
            decoded_token.get(AuthenticationConstants.ISSUER_CLAIM),
            decoded_token.get(AuthenticationConstants.TENANT_ID_CLAIM),
        )

        logger.debug("JWT token validated successfully.")
        return ClaimsIdentity(decoded_token, security_token=token)

    def get_anonymous_claims(self) -> ClaimsIdentity:
        """Returns a ClaimsIdentity for an anonymous user."""
        logger.debug("Returning anonymous claims identity.")
        return ClaimsIdentity()


def _build_jwks_uri(
    iss: Any,
    root_config: AgentAuthConfiguration,
    routing_config: AgentAuthConfiguration,
) -> str:
    """Builds the JWKS URI for the (unverified, routing-only) issuer and the
    root and audience-selected connection configurations.

    Recognizes the Bot Framework public/US Government issuers directly;
    US Government Entra connections use the audience-selected connection's
    effective tenant. Public-cloud Entra routing deliberately preserves the
    pre-existing endpoint based on the root validator configuration's
    ``TENANT_ID`` so existing multi-connection and network-egress deployments
    do not begin contacting a different discovery URL.

    A non-string ``iss`` (e.g. a malformed array/object claim) is never a
    recognized Bot Framework issuer and is never used as a dict key here --
    it falls through to the default (non-Bot-Framework) routing instead of
    risking a dict-lookup/hash failure on an unhashable value.
    """
    bf_uri = BOTFRAMEWORK_JWKS_URIS.get(iss) if isinstance(iss, str) else None
    if bf_uri:
        return bf_uri

    if is_gov_authority(routing_config.AUTHORITY):
        host = jwks_login_host(routing_config.AUTHORITY)
        tenant = (
            effective_tenant(routing_config.TENANT_ID, routing_config.AUTHORITY)
            or "common"
        )
        return f"{host}/{tenant}/discovery/v2.0/keys"

    return (
        "https://login.microsoftonline.com/"
        f"{root_config.TENANT_ID or 'common'}/discovery/v2.0/keys"
    )


def _get_valid_issuers(config: AgentAuthConfiguration) -> set[str]:
    """Case-insensitive union of the connection's configured/default issuers
    (``AgentAuthConfiguration.ISSUERS``) and the always-trusted Microsoft
    first-party issuers for the connection's cloud."""
    combined = list(config.ISSUERS) + well_known_first_party_issuers(config.AUTHORITY)
    return {issuer.lower() for issuer in combined}


def _is_multi_tenant(config: AgentAuthConfiguration) -> bool:
    """A connection configured for the Entra ``common``/``organizations``
    meta-tenant ("blueprint" agent) has no single known calling tenant at
    configuration time, so :func:`_is_acceptable_tenant_issuer` is used instead
    of the strict allow-list. The token's tenant is still bound to its ``tid``
    claim by :func:`_validate_tenant_binding` and anchored by the signature and
    audience checks.

    The effective tenant (authority-embedded segment when present, otherwise
    TENANT_ID; see :func:`effective_tenant`) is used so a connection whose
    AUTHORITY embeds ``common``/``organizations`` (rather than TENANT_ID) is
    still recognized as multi-tenant.
    """
    tenant = (effective_tenant(config.TENANT_ID, config.AUTHORITY) or "").lower()
    return tenant in ("common", "organizations")


def _is_acceptable_tenant_issuer(iss: str, config: AgentAuthConfiguration) -> bool:
    """Whether ``iss`` is a canonical Entra issuer acceptable for a multi-tenant
    connection: it must carry a tenant GUID and, for cloud-specific v2 issuers,
    match the connection's cloud (public vs US Government). The cloud-agnostic
    v1 ``sts.windows.net`` issuer is accepted for either cloud."""
    info = entra_issuer_info(iss)
    if info is None:
        return False
    return info.gov is None or info.gov == is_gov_authority(config.AUTHORITY)


def _validate_issuer(iss: Any, config: AgentAuthConfiguration) -> None:
    """Validates that the token's ``iss`` claim is accepted for the matched
    connection: either present in the connection's issuer allow-list, or, for
    a multi-tenant (``common``/``organizations``) connection, a canonical
    Entra issuer for the connection's cloud."""
    if isinstance(iss, str):
        if iss.lower() in _get_valid_issuers(config):
            return
        if _is_multi_tenant(config) and _is_acceptable_tenant_issuer(iss, config):
            return
    logger.warning("JWT issuer not accepted for this connection.")
    raise ValueError("Invalid issuer.")


def _validate_tenant_binding(iss: Any, tid: Any) -> None:
    """Validates that an Entra token's ``tid`` claim matches the tenant GUID
    embedded in its ``iss`` claim, preventing a token whose issuer was
    allow-listed (e.g. one of the always-trusted Microsoft first-party
    tenants) from being accepted on behalf of a different tenant.

    The binding only applies when ``iss`` is a recognized Entra issuer
    carrying a GUID tenant; Bot Framework/non-Entra issuers (no ``tid``
    claim) and tenant-alias issuers are skipped. A missing ``tid`` claim also
    skips the binding rather than failing closed, so tokens/issuers that do
    not carry one remain unaffected.
    """
    if not isinstance(iss, str):
        return
    info = entra_issuer_info(iss)
    if info is None or not isinstance(tid, str):
        return
    if tid.lower() != info.tenant:
        logger.warning("JWT tenant binding mismatch.")
        raise ValueError("Invalid issuer.")
