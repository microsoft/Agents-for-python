# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib
import json
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web

from microsoft_agents.hosting.aiohttp.jwt_authorization_middleware import (
    jwt_authorization_decorator,
)
from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    ClaimsIdentity,
)
from microsoft_agents.hosting.core.http import HttpResponse

_jwt_middleware_module = importlib.import_module(
    "microsoft_agents.hosting.aiohttp.jwt_authorization_middleware"
)


class _RequestStub:
    def __init__(
        self, auth_config: AgentAuthConfiguration, authorization: str | None = None
    ):
        self.app = {"agent_configuration": auth_config}
        self.headers = {}
        if authorization is not None:
            self.headers["Authorization"] = authorization
        self._items = {}

    def __getitem__(self, key):
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[key] = value


def _response_json(response):
    return json.loads(response.body.decode())


@pytest.mark.asyncio
async def test_aiohttp_middleware_stores_claims_and_calls_handler():
    auth_config = AgentAuthConfiguration()
    claims = ClaimsIdentity({"aud": "app-id"}, True)

    async def handler(request):
        return web.json_response({"aud": request["claims_identity"].claims["aud"]})

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        response = await _jwt_middleware_module._jwt_authorization_middleware(
            _RequestStub(auth_config, "Bearer token"), handler
        )

    assert response.status == 200
    assert _response_json(response) == {"aud": "app-id"}
    authorize.assert_awaited_once_with("Bearer token", auth_config)


@pytest.mark.asyncio
async def test_aiohttp_middleware_converts_http_response():
    auth_config = AgentAuthConfiguration()
    handler = AsyncMock(return_value=web.json_response({"called": True}))

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Invalid token or authentication failed."},
                status_code=401,
            )
        ),
    ) as authorize:
        response = await _jwt_middleware_module._jwt_authorization_middleware(
            _RequestStub(auth_config, "Bearer token"), handler
        )

    assert response.status == 401
    assert _response_json(response) == {
        "error": "Invalid token or authentication failed."
    }
    handler.assert_not_awaited()
    authorize.assert_awaited_once_with("Bearer token", auth_config)


@pytest.mark.asyncio
async def test_aiohttp_decorator_uses_authorization_helper():
    auth_config = AgentAuthConfiguration()
    claims = ClaimsIdentity({"aud": "decorator-app"}, True)

    @jwt_authorization_decorator
    async def handler(request):
        return web.json_response({"aud": request["claims_identity"].claims["aud"]})

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(return_value=claims),
    ) as authorize:
        response = await handler(_RequestStub(auth_config, "Bearer token"))

    assert response.status == 200
    assert _response_json(response) == {"aud": "decorator-app"}
    authorize.assert_awaited_once_with("Bearer token", auth_config)


@pytest.mark.asyncio
async def test_aiohttp_decorator_converts_http_response():
    auth_config = AgentAuthConfiguration()

    @jwt_authorization_decorator
    async def handler(request):
        return web.json_response({"called": True})

    with patch.object(
        _jwt_middleware_module,
        "_authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Authorization header not found"},
                status_code=401,
            )
        ),
    ) as authorize:
        response = await handler(_RequestStub(auth_config))

    assert response.status == 401
    assert _response_json(response) == {"error": "Authorization header not found"}
    authorize.assert_awaited_once_with(None, auth_config)
