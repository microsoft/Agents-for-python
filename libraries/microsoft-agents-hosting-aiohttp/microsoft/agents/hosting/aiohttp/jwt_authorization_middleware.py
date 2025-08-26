import functools
from aiohttp.web import Request, middleware, json_response

from microsoft.agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    JwtTokenValidator,
)


@middleware
async def jwt_authorization_middleware(request: Request, handler):
    auth_config: AgentAuthConfiguration = request.app["agent_configuration"]
    token_validator = JwtTokenValidator(auth_config)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        # Extract the token from the Authorization header
        token = auth_header.split(" ")[1]
        try:
            claims = token_validator.validate_token(token)
            request["claims_identity"] = claims
        except ValueError as e:
            print(f"JWT validation error: {e}")
            return json_response({"error": str(e)}, status=401)
    else:
        if not auth_config or not auth_config.CLIENT_ID:
            # TODO: Refine anonymous strategy
            request["claims_identity"] = token_validator.get_anonymous_claims()
        else:
            return json_response(
                {"error": "Authorization header not found"}, status=401
            )

    return await handler(request)


def jwt_authorization_decorator(func):
    @functools.wraps(func)
    async def wrapper(request):
        auth_config: AgentAuthConfiguration = request.app["agent_configuration"]
        token_validator = JwtTokenValidator(auth_config)
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Extract the token from the Authorization header
            token = auth_header.split(" ")[1]
            try:
                claims = token_validator.validate_token(token)
                request["claims_identity"] = claims
            except ValueError as e:
                print(f"JWT validation error: {e}")
                return json_response({"error": str(e)}, status=401)
        else:
            if not auth_config.CLIENT_ID:
                # TODO: Refine anonymous strategy
                request["claims_identity"] = token_validator.get_anonymous_claims()
            else:
                return json_response(
                    {"error": "Authorization header not found"}, status=401
                )

        return await func(request)

    return wrapper
