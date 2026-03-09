# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import logging
from typing import Any
from dataclasses import dataclass

from jwt import PyJWKClient, PyJWK, decode, get_unverified_header

from .agent_auth_configuration import AgentAuthConfiguration
from .claims_identity import ClaimsIdentity

logger = logging.getLogger(__name__)

@dataclass
class _JwkClientCacheEntry:

    jwk_client: PyJWKClient
    lock: asyncio.Lock

class _JwkClientManager:
    """Helper class to manage PyJWKClient instances for different JWKS URIs, with caching and async-safety"""

    _cache: dict[str, _JwkClientCacheEntry]

    def __init__(self):
        self._cache = {}

    def _get_jwk_client(self, jwks_uri: str) -> _JwkClientCacheEntry:
        """Retrieves a PyJWKClient for the given JWKS URI, using a cache to avoid creating multiple clients for the same URI."""
        if jwks_uri not in self._cache:
            self._cache[jwks_uri] = _JwkClientCacheEntry(PyJWKClient(jwks_uri), asyncio.Lock())
        return self._cache[jwks_uri]
        
    async def get_signing_key(self, jwks_uri: str, header: dict[str, Any]) -> PyJWK:
        """Retrieves the signing key from the JWK client for the given token header."""

        jwk_cache_entry = self._get_jwk_client(jwks_uri)
        async with jwk_cache_entry.lock:
            # locking and creating a new thread seems strange,
            # but PyJWKClient.get_signing_key is synchronous, so we spawn another thread
            # to make the call non-blocking, allowing other queued coroutines to run in the meantime.
            # Meanwhile, the lock ensures safety for the PyJWKClient's underlying cache and
            # prevents duplicate calls to the JWKS endpoint for the same URI when multiple
            # coroutines are trying to get signing keys concurrently.
            key = await asyncio.to_thread(jwk_cache_entry.jwk_client.get_signing_key, header["kid"])
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

        :param token: The JWT token to validate.
        :return: A ClaimsIdentity object containing the token's claims if validation is successful.
        :raises ValueError: If the token is invalid or if the audience claim is not valid
        """

        logger.debug("Validating JWT token.")
        key = await self._get_public_key_or_secret(token)
        decoded_token = decode(
            token,
            key=key,
            algorithms=["RS256"],
            leeway=300.0,
            options={"verify_aud": False},
        )
        if not self.configuration._jwt_patch_is_valid_aud(decoded_token["aud"]):
            logger.error(f"Invalid audience: {decoded_token['aud']}", stack_info=True)
            raise ValueError("Invalid audience.")

        # This probably should return a ClaimsIdentity
        logger.debug("JWT token validated successfully.")
        return ClaimsIdentity(decoded_token, True, security_token=token)

    def get_anonymous_claims(self) -> ClaimsIdentity:
        """Returns a ClaimsIdentity for an anonymous user."""
        logger.debug("Returning anonymous claims identity.")
        return ClaimsIdentity({}, False, authentication_type="Anonymous")

    async def _get_public_key_or_secret(self, token: str) -> PyJWK:
        """Retrieves the public key or secret for validating the JWT token."""
        header = get_unverified_header(token)
        unverified_payload: dict = decode(token, options={"verify_signature": False})

        jwks_uri = (
            "https://login.botframework.com/v1/.well-known/keys"
            if unverified_payload.get("iss") == "https://api.botframework.com"
            else f"https://login.microsoftonline.com/{self.configuration.TENANT_ID}/discovery/v2.0/keys"
        )

        key = await self._jwk_client_manager.get_signing_key(jwks_uri, header)

        return key
