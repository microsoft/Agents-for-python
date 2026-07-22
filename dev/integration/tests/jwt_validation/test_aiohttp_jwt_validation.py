# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from aiohttp import web

from microsoft_agents.hosting.aiohttp import jwt_authorization_middleware

from ._helpers import load_auth_config


@pytest.mark.asyncio
async def test_aiohttp_jwt_allows_anonymous_request_from_env_config(aiohttp_client):
    async def handler(request):
        identity = request["claims_identity"]
        return web.json_response(
            {
                "authenticated": identity.is_authenticated,
                "authentication_type": identity.authentication_type,
            }
        )

    app = web.Application(middlewares=[jwt_authorization_middleware])
    app["agent_configuration"] = load_auth_config("jwt_anonymous.env")
    app.router.add_get("/", handler)

    client = await aiohttp_client(app)
    response = await client.get("/")

    assert response.status == 200
    assert await response.json() == {
        "authenticated": False,
        "authentication_type": "Anonymous",
    }


@pytest.mark.asyncio
async def test_aiohttp_jwt_rejects_missing_authorization_header(aiohttp_client):
    async def handler(request):
        return web.json_response({"called": True})

    app = web.Application(middlewares=[jwt_authorization_middleware])
    app["agent_configuration"] = load_auth_config("jwt_required.env")
    app.router.add_get("/", handler)

    client = await aiohttp_client(app)
    response = await client.get("/")

    assert response.status == 401
    assert await response.json() == {"error": "Authorization header not found"}


@pytest.mark.asyncio
async def test_aiohttp_jwt_rejects_invalid_bearer_token(aiohttp_client):
    async def handler(request):
        return web.json_response({"called": True})

    app = web.Application(middlewares=[jwt_authorization_middleware])
    app["agent_configuration"] = load_auth_config("jwt_required.env")
    app.router.add_get("/", handler)

    client = await aiohttp_client(app)
    response = await client.get("/", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status == 401
    assert await response.json() == {
        "error": "Invalid token or authentication failed."
    }
