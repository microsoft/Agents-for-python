# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools
import inspect
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.jwt import _authorize_request, JwtTokenValidator
from microsoft_agents.hosting.core.http import HttpResponse

def _get_or_create_cached_validator(app) -> JwtTokenValidator:
    """Gets or creates a cached JwtTokenValidator instance in the FastAPI application.

    :param app: The FastAPI application instance.
    :param auth_config: The authentication configuration.
    :return: A JwtTokenValidator instance.
    """
    state = getattr(app, "state")
    if not hasattr(state, "jwt_validator") and state is not None:
        base_auth_config = getattr(state, "agent_configuration", None)
        if isinstance(base_auth_config, AgentAuthConfiguration):
            app.state.jwt_validator = JwtTokenValidator(base_auth_config)
        else:
            auth_config: Configuration | None = Configuration(base_auth_config)
            app.state.jwt_validator = JwtTokenValidator(auth_config)
    return app.state.jwt_validator

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
        validator = _get_or_create_cached_validator(app)

        request = Request(scope, receive=receive)
        res = await _authorize_request(
            request.headers.get("Authorization"), validator=validator
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

        auth_header = request.headers.get("Authorization")
        validator = _get_or_create_cached_validator(request.app)

        res = await _authorize_request(auth_header, validator=validator)
        if isinstance(res, HttpResponse):
            return JSONResponse(content=res.body, status_code=res.status_code)
        request.state.claims_identity = res
        return await func(request, *args, **kwargs)

    # FastAPI relies on inspect.signature for dependency injection and docs.
    wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]

    return wrapper
