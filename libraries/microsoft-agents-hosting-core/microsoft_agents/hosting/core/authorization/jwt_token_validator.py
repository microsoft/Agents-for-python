# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import jwt

from jwt import PyJWKClient, PyJWK, decode, get_unverified_header

from .agent_auth_configuration import AgentAuthConfiguration
from .claims_identity import ClaimsIdentity

logger = logging.getLogger(__name__)


class JwtTokenValidator:
    def __init__(self, configuration: AgentAuthConfiguration):
        self.configuration = configuration
        self._default_jwks_client = None
        self._tenant_jwks_client = None

    def validate_token(self, token: str) -> ClaimsIdentity:

        logger.debug("Validating JWT token.")
        key = self._get_public_key_or_secret(token)
        decoded_token = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            leeway=300.0,
            options={"verify_aud": False},
        )
        if decoded_token["aud"] != self.configuration.CLIENT_ID:
            logger.error(f"Invalid audience: {decoded_token['aud']}", stack_info=True)
            raise ValueError("Invalid audience.")

        # This probably should return a ClaimsIdentity
        logger.debug("JWT token validated successfully.")
        return ClaimsIdentity(decoded_token, True)

    def get_anonymous_claims(self) -> ClaimsIdentity:
        logger.debug("Returning anonymous claims identity.")
        return ClaimsIdentity({}, False, authentication_type="Anonymous")
    
    def _get_client(self, issuer: str) -> PyJWKClient:
        client = None
        if issuer == "https://api.botframework.com":
            client = self._default_jwks_client
        else:
            client = self._tenant_jwks_client
        if not client:
            raise RuntimeError("JWKS client is not initialized.")
        return client
    
    def _init_jwks_client(self, issuer: str) -> None:

        client_options = {
            "cache_keys": True
        }

        if issuer == "https://api.botframework.com":
            if self._default_jwks_client is None:
                self._default_jwks_client = PyJWKClient(
                    "https://login.botframework.com/v1/.well-known/keys",
                    **client_options
                )
        else:
            if self._tenant_jwks_client is None:
                self._tenant_jwks_client = PyJWKClient(
                    f"https://login.microsoftonline.com/{self.configuration.TENANT_ID}/discovery/v2.0/keys",
                    **client_options
                )

    def _get_public_key_or_secret(self, token: str) -> PyJWK:

        header = get_unverified_header(token)
        unverified_payload: dict = decode(token, options={"verify_signature": False})

        issuer = unverified_payload.get("iss")
        if not issuer:
            raise ValueError("Issuer (iss) claim is missing in the token.")
        self._init_jwks_client(issuer)

        key = self._get_client(issuer).get_signing_key(header["kid"])
        return key
