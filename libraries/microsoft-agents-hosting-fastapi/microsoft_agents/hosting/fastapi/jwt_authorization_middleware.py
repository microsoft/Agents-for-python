# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from starlette.types import ASGIApp, Receive, Scope, Send

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request
from microsoft_agents.hosting.core.http import HttpResponse

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
            response = JSONResponse(content=res.body, status_code=res.status_code)
            await response(scope, receive, send)
            return

        request.state.claims_identity = res
        await self.app(scope, receive, send)


def jwt_authorization_decorator(func):
    """
    :param func: The FastAPI route handler function to be decorated.
    :return: The decorated FastAPI route handler function.
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
            return JSONResponse(content=res.body, status_code=res.status_code)
        request.state.claims_identity = res
        return await func(request, *args, **kwargs)

    return wrapper
