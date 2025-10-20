import functools
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    JwtTokenValidator,
)


async def jwt_authorization_dependency(request: Request):
    """
    FastAPI dependency for JWT authorization.

    Usage:
        @app.post("/api/messages")
        async def messages(request: Request, _: None = Depends(jwt_authorization_dependency)):
            # Your handler code here
    """
    # Get auth configuration from app state
    auth_config: AgentAuthConfiguration = getattr(
        request.app.state, "agent_configuration", None
    )
    if not auth_config:
        raise HTTPException(status_code=500, detail="Agent configuration not found")

    token_validator = JwtTokenValidator(auth_config)
    auth_header = request.headers.get("Authorization")

    if auth_header:
        # Extract the token from the Authorization header
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Invalid authorization header format"
            )

        token = parts[1]
        try:
            claims = token_validator.validate_token(token)
            request.state.claims_identity = claims
        except ValueError as e:
            print(f"JWT validation error: {e}")
            raise HTTPException(status_code=401, detail=str(e))
    else:
        if not auth_config or not auth_config.CLIENT_ID:
            # TODO: Refine anonymous strategy
            request.state.claims_identity = token_validator.get_anonymous_claims()
        else:
            raise HTTPException(
                status_code=401, detail="Authorization header not found"
            )


def jwt_authorization_decorator(func: Callable):
    """
    Decorator for JWT authorization on individual route functions.

    Usage:
        @jwt_authorization_decorator
        async def messages(request: Request):
            # Your handler code here
    """

    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Get auth configuration from app state
        auth_config: AgentAuthConfiguration = getattr(
            request.app.state, "agent_configuration", None
        )
        if not auth_config:
            raise HTTPException(status_code=500, detail="Agent configuration not found")

        token_validator = JwtTokenValidator(auth_config)
        auth_header = request.headers.get("Authorization")

        if auth_header:
            # Extract the token from the Authorization header
            parts = auth_header.split(" ")
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise HTTPException(
                    status_code=401, detail="Invalid authorization header format"
                )

            token = parts[1]
            try:
                claims = token_validator.validate_token(token)
                request.state.claims_identity = claims
            except ValueError as e:
                print(f"JWT validation error: {e}")
                raise HTTPException(status_code=401, detail=str(e))
        else:
            if not auth_config.CLIENT_ID:
                # TODO: Refine anonymous strategy
                request.state.claims_identity = token_validator.get_anonymous_claims()
            else:
                raise HTTPException(
                    status_code=401, detail="Authorization header not found"
                )

        return await func(request, *args, **kwargs)

    return wrapper


class JwtAuthorizationMiddleware:
    """
    Middleware class for JWT authorization in FastAPI.

    Usage:
        from fastapi import FastAPI
        from fastapi.middleware.base import BaseHTTPMiddleware

        app = FastAPI()
        app.add_middleware(BaseHTTPMiddleware, dispatch=JwtAuthorizationMiddleware())
    """

    def __init__(self):
        pass

    async def __call__(self, request: Request, call_next):
        # Get auth configuration from app state
        auth_config: AgentAuthConfiguration = getattr(
            request.app.state, "agent_configuration", None
        )

        if auth_config:
            token_validator = JwtTokenValidator(auth_config)
            auth_header = request.headers.get("Authorization")

            if auth_header:
                # Extract the token from the Authorization header
                parts = auth_header.split(" ")
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                    try:
                        claims = token_validator.validate_token(token)
                        request.state.claims_identity = claims
                    except ValueError as e:
                        logging.warning(f"JWT validation error: {e}")
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
                if not auth_config.CLIENT_ID:
                    # TODO: Refine anonymous strategy
                    request.state.claims_identity = (
                        token_validator.get_anonymous_claims()
                    )
                else:
                    return JSONResponse(
                        {"error": "Authorization header not found"}, status_code=401
                    )

        response = await call_next(request)
        return response
