# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools

from typing import cast

from aiohttp.web import Request, middleware, json_response

from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request
from microsoft_agents.hosting.core.http import HttpResponse


async def _jwt_authorization_middleware(request: Request, handler):
    """
    JWT Authorization Middleware for aiohttp endpoints.
    """
    auth_config = cast(
        AgentAuthConfiguration | None, request.app["agent_configuration"]
    )
    auth_header = request.headers.get("Authorization")

    res = await _authorize_request(auth_header, auth_config)

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
