# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from starlette.types import ASGIApp, Receive, Scope, Send
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    JwtTokenValidator,
)

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

        if not auth_config:
            response = JSONResponse(
                {"error": "Agent Authentication configuration not found"},
                status_code=500,
            )
            await response(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        token_validator = JwtTokenValidator(auth_config)
        auth_header = request.headers.get("Authorization")

        if auth_header:
            parts = auth_header.split(" ")
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                try:
                    claims = await token_validator.validate_token(token)
                    request.state.claims_identity = claims
                except ValueError as e:
                    logger.warning("JWT validation error: %s", e)
                    response = JSONResponse(
                        {"error": "Invalid token or authentication failed."},
                        status_code=401,
                    )
                    await response(scope, receive, send)
                    return
            else:
                response = JSONResponse(
                    {"error": "Invalid authorization header format"},
                    status_code=401,
                )
                await response(scope, receive, send)
                return
        else:
            if auth_config.ANONYMOUS_ALLOWED:
                request.state.claims_identity = token_validator.get_anonymous_claims()
            else:
                response = JSONResponse(
                    {"error": "Authorization header not found"},
                    status_code=401,
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


def jwt_authorization_decorator(func):
    """
    JWT Authorization Decorator for FastAPI endpoints. Until a SDK solution is made available,
    this decorator can be applied to any FastAPI route handler to enforce JWT validation using the Microsoft Agents SDK's JwtTokenValidator.
    """

    @functools.wraps(func)
    async def wrapper(request: Request):
        if request is None:
            return JSONResponse({"error": "Request object not found"}, status_code=500)

        auth_config: AgentAuthConfiguration | None = getattr(
            request.app.state, "agent_configuration", None
        )

        if auth_config is None:
            return JSONResponse(
                {"error": "Agent Authentication configuration not found"},
                status_code=500,
            )

        token_validator = JwtTokenValidator(auth_config)
        auth_header = request.headers.get("Authorization")

        if auth_header:
            parts = auth_header.split(" ")
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                try:
                    claims = await token_validator.validate_token(token)
                    request.state.claims_identity = claims
                except ValueError:
                    return JSONResponse(
                        {"error": "Invalid token or authentication failed."},
                        status_code=401,
                    )
            else:
                return JSONResponse(
                    {"error": "Invalid authorization header format"},
                    status_code=401,
                )
        else:
            return JSONResponse(
                {"error": "Authorization header not found"},
                status_code=401,
            )

        return await func(request)

    return wrapper
