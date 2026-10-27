# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools
import logging
from typing import cast
from weakref import WeakKeyDictionary

from aiohttp.web import Request, middleware, json_response, Application

from microsoft_agents.activity.config import Configuration, xpath
from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request, JwtTokenValidator
from microsoft_agents.hosting.core.http import HttpResponse

logger = logging.getLogger(__name__)

_GENERIC_AUTH_ERROR = {"error": "Invalid token or authentication failed."}

_TOKEN_VALIDATOR_CACHE: WeakKeyDictionary[Application, JwtTokenValidator] = WeakKeyDictionary()


def _extract_bearer_token(auth_header: str) -> str | None:
    """Extracts the bearer token from a raw Authorization header value.

    Surrounding whitespace on the token is ignored for backward compatibility.
    Returns None for anything malformed so callers can respond with a
    consistent 401 instead of raising.
    """
    parts = auth_header.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1].strip()
    return token if token and not any(char.isspace() for char in token) else None

def _get_or_create_cached_validator(app: Application) -> JwtTokenValidator:
    """Gets or creates a cached JwtTokenValidator instance in the aiohttp application.

    :param app: The aiohttp application instance.
    :param auth_config: The authentication configuration.
    :return: A JwtTokenValidator instance.
    """
    if app not in _TOKEN_VALIDATOR_CACHE:
        base_auth_config = app.get("agent_configuration", None)
        if isinstance(base_auth_config, AgentAuthConfiguration):
            _TOKEN_VALIDATOR_CACHE[app] = JwtTokenValidator(base_auth_config)
        else:
            auth_config = Configuration(base_auth_config)
            _TOKEN_VALIDATOR_CACHE[app] = JwtTokenValidator(auth_config)
    return _TOKEN_VALIDATOR_CACHE[app]

async def _jwt_authorization_middleware(request: Request, handler):
    """
    JWT Authorization Middleware for aiohttp endpoints.
    """

    auth_header = request.headers.get("Authorization")
    if auth_header is not None:
        # aiohttp-specific tolerance: trailing whitespace (spaces/tabs) after
        # the bearer token is ignored for backward compatibility, but internal
        # or extra non-whitespace content is rejected. Normalizing here keeps
        # the shared `_authorize_request` parsing (used identically by the
        # FastAPI adapter) strict and unchanged.
        token = _extract_bearer_token(auth_header)
        if token is None:
            logger.warning("Malformed authorization header.")
            return json_response(_GENERIC_AUTH_ERROR, status=401)
        auth_header = f"Bearer {token}"

    validator = _get_or_create_cached_validator(request.app)
    res = await _authorize_request(auth_header, validator=validator)

    if isinstance(res, HttpResponse):
        return json_response(res.body, status=res.status_code)

    request["claims_identity"] = res
    return await handler(request)


jwt_authorization_middleware = middleware(_jwt_authorization_middleware)


def jwt_authorization_decorator(func):
    """
    Decorator for aiohttp route handlers to enforce JWT validation using the Microsoft Agents SDK's JwtTokenValidator.

    :param func: The aiohttp route handler function to be decorated.
    :return: The decorated aiohttp route handler function.
    """

    @functools.wraps(func)
    async def wrapper(request):
        return await _jwt_authorization_middleware(request, func)

    return wrapper
