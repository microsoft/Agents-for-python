# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web

from microsoft_agents.hosting.aiohttp.jwt_authorization_middleware import (
    jwt_authorization_decorator,
    jwt_authorization_middleware,
)
from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.http import HttpResponse


def _set_agent_configuration(app: web.Application, auth_config: AgentAuthConfiguration):
    app._state["agent_configuration"] = auth_config


@pytest.mark.asyncio
async def test_aiohttp_middleware_stores_claims_and_calls_handler(aiohttp_client):
    auth_config = AgentAuthConfiguration()
    claims = ClaimsIdentity({"aud": "app-id"}, True)

    async def handler(request):
        return web.json_response({"aud": request["claims_identity"].claims["aud"]})

    app = web.Application(middlewares=[jwt_authorization_middleware])
    _set_agent_configuration(app, auth_config)
    app.router.add_get("/", handler)

    with patch(
        "microsoft_agents.hosting.aiohttp.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        client = await aiohttp_client(app)
        response = await client.get("/", headers={"Authorization": "Bearer token"})

    assert response.status == 200
    assert await response.json() == {"aud": "app-id"}
    authorize.assert_awaited_once_with("Bearer token", auth_config)


@pytest.mark.asyncio
async def test_aiohttp_middleware_converts_http_response(aiohttp_client):
    auth_config = AgentAuthConfiguration()

    async def handler(request):
        return web.json_response({"called": True})

    app = web.Application(middlewares=[jwt_authorization_middleware])
    _set_agent_configuration(app, auth_config)
    app.router.add_get("/", handler)

    with patch(
        "microsoft_agents.hosting.aiohttp.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Invalid token or authentication failed."},
                status_code=401,
            )
        ),
    ) as authorize:
        client = await aiohttp_client(app)
        response = await client.get("/", headers={"Authorization": "Bearer bad"})

    assert response.status == 401
    assert await response.json() == {"error": "Invalid token or authentication failed."}
    authorize.assert_awaited_once_with("Bearer bad", auth_config)


@pytest.mark.asyncio
async def test_aiohttp_decorator_uses_authorization_helper(aiohttp_client):
    auth_config = AgentAuthConfiguration()
    claims = ClaimsIdentity({"aud": "decorator-app"}, True)

    @jwt_authorization_decorator
    async def handler(request):
        return web.json_response({"aud": request["claims_identity"].claims["aud"]})

    app = web.Application()
    _set_agent_configuration(app, auth_config)
    app.router.add_get("/", handler)

    with patch(
        "microsoft_agents.hosting.aiohttp.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        client = await aiohttp_client(app)
        response = await client.get("/", headers={"Authorization": "Bearer token"})

    assert response.status == 200
    assert await response.json() == {"aud": "decorator-app"}
    authorize.assert_awaited_once_with("Bearer token", auth_config)


@pytest.mark.asyncio
async def test_aiohttp_decorator_converts_http_response(aiohttp_client):
    auth_config = AgentAuthConfiguration()

    @jwt_authorization_decorator
    async def handler(request):
        return web.json_response({"called": True})

    app = web.Application()
    _set_agent_configuration(app, auth_config)
    app.router.add_get("/", handler)

    with patch(
        "microsoft_agents.hosting.aiohttp.jwt_authorization_middleware._authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Authorization header not found"},
                status_code=401,
            )
        ),
    ) as authorize:
        client = await aiohttp_client(app)
        response = await client.get("/")

    assert response.status == 401
    assert await response.json() == {"error": "Authorization header not found"}
    authorize.assert_awaited_once_with(None, auth_config)
