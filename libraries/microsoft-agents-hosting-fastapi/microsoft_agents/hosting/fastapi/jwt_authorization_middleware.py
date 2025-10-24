from fastapi import Request
from fastapi.responses import JSONResponse
import logging
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
        auth_config: AgentAuthConfiguration = getattr(
            state, "agent_configuration", None
        )

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
            if not auth_config or not auth_config.CLIENT_ID:
                request.state.claims_identity = (
                    await token_validator.get_anonymous_claims()
                )
            else:
                response = JSONResponse(
                    {"error": "Authorization header not found"},
                    status_code=401,
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
