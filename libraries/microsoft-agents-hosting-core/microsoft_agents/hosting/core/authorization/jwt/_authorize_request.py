# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from jwt import PyJWTError
from typing import Any, Mapping
from weakref import WeakKeyDictionary

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core.http import HttpResponse

from ..agent_auth_configuration import AgentAuthConfiguration
from ..claims_identity import ClaimsIdentity
from .jwt_token_validator import JwtTokenValidator

logger = logging.getLogger(__name__)

_TOKEN_VALIDATION_CACHE: WeakKeyDictionary[Any, JwtTokenValidator] = WeakKeyDictionary()

def _resolve_token_validator(
    auth_config: Mapping | AgentAuthConfiguration | None,
    cache_key: Any = None,
) -> JwtTokenValidator | None:

    if cache_key is not None and cache_key in _TOKEN_VALIDATION_CACHE:
        return _TOKEN_VALIDATION_CACHE[cache_key]

    if auth_config is not None:
        config: Configuration | AgentAuthConfiguration = auth_config
        if not isinstance(auth_config, AgentAuthConfiguration):
            config = Configuration(auth_config)
        validator = JwtTokenValidator(config)
        if cache_key is not None:
            _TOKEN_VALIDATION_CACHE[cache_key] = validator
        return validator
    return None

async def _authorize_request(
    authorization_header: str | None,
    auth_config: Mapping | AgentAuthConfiguration | None,
    *,
    cache_key: Any = None
) -> ClaimsIdentity | HttpResponse:
    """
    Authorizes a request based on the provided JWT token in the Authorization header.

    :param authorization_header: The value of the Authorization header from the request.
    :param auth_config: The AgentAuthConfiguration instance containing authentication settings.
    :return: A ClaimsIdentity object if the token is valid, or an HttpResponse with an
        error message and status code if the token is invalid or missing.
    """
    validator = _resolve_token_validator(
        auth_config,
        cache_key
    )

    if not validator:
        return HttpResponse(
            body={"error": "Agent Authentication configuration not found"},
            status_code=500,
        )

    if not authorization_header:
        if auth_config.config.anonymous_allowed:
            claims_identity = validator.get_anonymous_claims()
            return claims_identity
        return HttpResponse(
            body={"error": "Authorization header not found"},
            status_code=401,
        )

    parts = authorization_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return HttpResponse(
            body={"error": "Invalid authorization header format"},
            status_code=401,
        )

    try:
        claims = await validator.validate_token(parts[1])
        return claims
    except (PyJWTError, ValueError) as e:
        # Log only the exception type -- the message/claims are not surfaced
        # to the caller (or the logs) to avoid leaking validation internals.
        logger.warning("JWT validation error: %s", type(e).__name__)
        return HttpResponse(
            body={"error": "Invalid token or authentication failed."},
            status_code=401,
        )
