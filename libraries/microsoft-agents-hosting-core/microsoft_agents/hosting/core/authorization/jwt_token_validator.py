# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import logging
import jwt

from jwt import PyJWKClient, PyJWK, decode, get_unverified_header

from .agent_auth_configuration import AgentAuthConfiguration
from .claims_identity import ClaimsIdentity

logger = logging.getLogger(__name__)

class JwtTokenValidator:

    _jwk_clients_cache: dict[str, PyJWKClient] = {}

    def __init__(self, configuration: AgentAuthConfiguration):
        self.configuration = configuration

    @staticmethod
    def _get_jwk_client(jwks_uri: str) -> PyJWKClient:
        if jwks_uri not in JwtTokenValidator._jwk_clients_cache:
            JwtTokenValidator._jwk_clients_cache[jwks_uri] = PyJWKClient(jwks_uri)
        return JwtTokenValidator._jwk_clients_cache[jwks_uri]

    async def validate_token(self, token: str) -> ClaimsIdentity:

        logger.debug("Validating JWT token.")
        key = await self._get_public_key_or_secret(token)
        decoded_token = jwt.decode(
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
        logger.debug("Returning anonymous claims identity.")
        return ClaimsIdentity({}, False, authentication_type="Anonymous")

    async def _get_public_key_or_secret(self, token: str) -> PyJWK:
        header = get_unverified_header(token)
        unverified_payload: dict = decode(token, options={"verify_signature": False})

        jwksUri = (
            "https://login.botframework.com/v1/.well-known/keys"
            if unverified_payload.get("iss") == "https://api.botframework.com"
            else f"https://login.microsoftonline.com/{self.configuration.TENANT_ID}/discovery/v2.0/keys"
        )
        jwks_client = JwtTokenValidator._get_jwk_client(jwksUri)        
        key = await asyncio.to_thread(jwks_client.get_signing_key, header["kid"])

        return key
