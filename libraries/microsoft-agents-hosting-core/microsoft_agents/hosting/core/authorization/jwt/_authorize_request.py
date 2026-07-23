# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from jwt import PyJWTError

from microsoft_agents.hosting.core.http import HttpResponse

from ..agent_auth_configuration import AgentAuthConfiguration
from ..claims_identity import ClaimsIdentity
from .jwt_token_validator import JwtTokenValidator

logger = logging.getLogger(__name__)


async def _authorize_request(
    authorization_header: str | None, auth_config: AgentAuthConfiguration | None
) -> ClaimsIdentity | HttpResponse:
    """
    Authorizes a request based on the provided JWT token in the Authorization header.

    :param authorization_header: The value of the Authorization header from the request.
    :param auth_config: The AgentAuthConfiguration instance containing authentication settings.
    :return: A ClaimsIdentity object if the token is valid, or an HttpResponse with an error message and status code if the token is invalid or missing.
    """

    if auth_config is None:
        return HttpResponse(
            body={"error": "Agent Authentication configuration not found"},
            status_code=500,
        )
    validator = JwtTokenValidator(auth_config)

    if not authorization_header:
        if auth_config.ANONYMOUS_ALLOWED:
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
        logger.warning("JWT validation error: %s", e)
        return HttpResponse(
            body={"error": "Invalid token or authentication failed."},
            status_code=401,
        )
