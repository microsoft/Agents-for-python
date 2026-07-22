# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from starlette.types import ASGIApp, Receive, Scope, Send

from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    ClaimsIdentity,
    JwtTokenValidator,
    HttpResponse,
)
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request

logger = logging.getLogger(__name__)


class JwtAuthorizationMiddleware:
    """Starlette-compatible ASGI middleware for JWT authorization.

    Usage:
        from fastapi import FastAPI

        app = FastAPI()
        app.add_middleware(JwtAuthorizationMiddleware)
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return

        app = scope.get("app")
        state = getattr(app, "state", None) if app else None
        auth_config: AgentAuthConfiguration | None = getattr(
            state, "agent_configuration", None
        )

        request = Request(scope, receive=receive)
        res = await _authorize_request(
            request.headers.get("Authorization"), auth_config
        )

        if isinstance(res, HttpResponse):
            response = JSONResponse(body=res.body, status_code=res.status_code)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def jwt_authorization_decorator(func):
    """
    JWT Authorization Decorator for FastAPI endpoints. Until a SDK solution is made available,
    this decorator can be applied to any FastAPI route handler to enforce JWT validation using the Microsoft Agents SDK's JwtTokenValidator.
    """

    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if request is None:
            return JSONResponse({"error": "Request object not found"}, status_code=500)

        auth_config: AgentAuthConfiguration | None = getattr(
            request.app.state, "agent_configuration", None
        )

        auth_header = request.headers.get("Authorization")

        res = await _authorize_request(auth_header, auth_config)
        if isinstance(res, HttpResponse):
            return JSONResponse(body=res.body, status_code=res.status_code)
        return await func(request, *args, **kwargs)

    return wrapper
