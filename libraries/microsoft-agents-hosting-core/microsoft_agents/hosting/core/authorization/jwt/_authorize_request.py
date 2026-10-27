# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from collections.abc import Mapping
from typing import Any
from weakref import WeakKeyDictionary

from jwt import PyJWTError

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core.http import HttpResponse

from ..connections.agent_auth_configuration import AgentAuthConfiguration
from ..claims_identity import ClaimsIdentity
from .jwt_token_validator import JwtTokenValidator

logger = logging.getLogger(__name__)

_TOKEN_VALIDATOR_CACHE: WeakKeyDictionary[Any, JwtTokenValidator] = WeakKeyDictionary()


async def _authorize_request(
    authorization_header: str | None,
    auth_config: Mapping[str, Any] | AgentAuthConfiguration | None = None,
    *,
    validator: JwtTokenValidator | None = None,
    cache_key: Any = None,
) -> ClaimsIdentity | HttpResponse:
    """
    Authorizes a request based on the provided JWT token in the Authorization header.

    :param authorization_header: The value of the Authorization header from the request.
    :param auth_config: Application Configuration for token validation, or a
        deprecated AgentAuthConfiguration instance.
    :param validator: Explicit validator, taking precedence over the cache.
    :param cache_key: Weak-referenceable, hashable cache owner. When omitted,
        validators are constructed per call. Configuration changes require
        replacing the cache owner or invalidating its cached validator.
    :return: A ClaimsIdentity object if the token is valid, or an HttpResponse with an
        error message and status code if the token is invalid or missing.
    :raises TypeError: If cache_key is not weak-referenceable or hashable.
    """

    if validator is None and cache_key is not None:
        validator = _TOKEN_VALIDATOR_CACHE.get(cache_key)

    if validator is None:
        if auth_config is None and cache_key is None:
            return HttpResponse(
                body={"error": "Agent Authentication configuration not found"},
                status_code=500,
            )
        config = (
            auth_config
            if isinstance(auth_config, AgentAuthConfiguration)
            else Configuration(auth_config)
        )
        validator = JwtTokenValidator(config)
        if cache_key is not None:
            _TOKEN_VALIDATOR_CACHE[cache_key] = validator

    if not authorization_header:
        if validator.config.anonymous_allowed:
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
