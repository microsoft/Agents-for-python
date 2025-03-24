from aiohttp.web import Request, middleware, json_response

from microsoft.agents.authentication import AgentAuthConfiguration, JwtTokenValidator


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
            return json_response({"error": str(e)}, status=401)
    else:
        if (not auth_config.CLIENT_ID) and (request.app["env"] == "DEV"):
            # TODO: Define anonymous strategy
            request["user"] = {"name": "anonymous"}
        else:
            return json_response(
                {"error": "Authorization header not found"}, status=401
            )

    return await handler(request)
