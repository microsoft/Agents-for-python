# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from a2a.server.request_handlers import RequestHandler
from a2a.types import AgentCapabilities, AgentCard, ListTasksResponse
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from microsoft_agents.hosting.core import AgentAuthConfiguration, ClaimsIdentity
from microsoft_agents.hosting.a2a.server import routes
from microsoft_agents.hosting.a2a.server._constants import _CLAIMS_IDENTITY_KEY


async def _request_with_identity(app, identity, method, path, **kwargs):
    async def authenticated_app(scope, receive, send):
        scope.setdefault("state", {})["claims_identity"] = identity
        await app(scope, receive, send)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=authenticated_app),
        base_url="http://testserver",
    ) as client:
        return await client.request(method, path, **kwargs)


@pytest.mark.asyncio
async def test_jsonrpc_routes_forward_authenticated_identity_to_request_handler():
    request_handler = MagicMock(spec=RequestHandler)
    request_handler.on_list_tasks.return_value = ListTasksResponse(tasks=[])
    identity = ClaimsIdentity({"sub": "agent-1"})
    app = Starlette(routes=routes.create_jsonrpc_routes(request_handler, "/a2a"))

    response = await _request_with_identity(
        app,
        identity,
        "POST",
        "/a2a",
        headers={"A2A-Version": "1.0"},
        json={
            "jsonrpc": "2.0",
            "id": "request-1",
            "method": "ListTasks",
            "params": {},
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["tasks"] == []
    context = request_handler.on_list_tasks.call_args.args[1]
    assert context.state[_CLAIMS_IDENTITY_KEY] is identity
    assert context.state["headers"]["a2a-version"] == "1.0"


@pytest.mark.asyncio
async def test_rest_routes_forward_authenticated_identity_to_request_handler():
    request_handler = MagicMock(spec=RequestHandler)
    request_handler.on_list_tasks.return_value = ListTasksResponse(tasks=[])
    identity = ClaimsIdentity({"sub": "agent-1"})
    app = Starlette(
        routes=routes.create_rest_routes(
            request_handler,
            path_prefix="/a2a",
        )
    )

    response = await _request_with_identity(
        app,
        identity,
        "GET",
        "/a2a/tasks",
        headers={"A2A-Version": "1.0"},
    )

    assert response.status_code == 200
    assert response.json()["tasks"] == []
    context = request_handler.on_list_tasks.call_args.args[1]
    assert context.state[_CLAIMS_IDENTITY_KEY] is identity
    assert context.state["headers"]["a2a-version"] == "1.0"


@pytest.mark.asyncio
async def test_create_agent_card_routes_adapts_request_and_uses_interface_prefix():
    observed = {}

    async def get_agent_card(request, prefix):
        observed["request"] = request
        observed["prefix"] = prefix
        return AgentCard(
            name="Test agent",
            description="Test description",
            version="1.0.0",
            supported_interfaces=[],
            capabilities=AgentCapabilities(),
        )

    route = routes.create_agent_card_routes(
        get_agent_card,
        "/a2a/.well-known/agent-card.json",
    )[0]
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/a2a/.well-known/agent-card.json",
            "raw_path": b"/a2a/.well-known/agent-card.json",
            "query_string": b"",
            "headers": [],
            "scheme": "https",
            "server": ("example.com", 443),
            "client": ("127.0.0.1", 1234),
        }
    )

    response = await route.endpoint(request)

    assert route.path == "/a2a/.well-known/agent-card.json"
    assert response.status_code == 200
    assert response.body == (
        b'{"name":"Test agent","description":"Test description",'
        b'"version":"1.0.0","capabilities":{}}'
    )
    assert (
        observed["request"].url == "https://example.com/a2a/.well-known/agent-card.json"
    )
    assert observed["prefix"] == "/a2a"


@pytest.mark.asyncio
async def test_create_agent_card_routes_uses_custom_url_as_prefix():
    observed = {}

    async def get_agent_card(request, prefix):
        observed["prefix"] = prefix
        return AgentCard(
            name="Test agent",
            description="Test description",
            version="1.0.0",
            supported_interfaces=[],
            capabilities=AgentCapabilities(),
        )

    route = routes.create_agent_card_routes(
        get_agent_card,
        "/custom-agent-card",
    )[0]
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/custom-agent-card",
            "raw_path": b"/custom-agent-card",
            "query_string": b"",
            "headers": [],
            "scheme": "https",
            "server": ("example.com", 443),
            "client": ("127.0.0.1", 1234),
        }
    )

    response = await route.endpoint(request)

    assert response.status_code == 200
    assert observed["prefix"] == "/custom-agent-card"


@pytest.mark.asyncio
async def test_use_jwt_middleware_authorizes_shared_mounted_route_once():
    async def endpoint(request):
        return JSONResponse({"ok": True})

    route = Route("/messages", endpoint=endpoint)
    mounted = Mount("/tenant", routes=[route])
    routes.use_jwt_middleware([route, mounted])
    app = Starlette(routes=[route])
    app.state.agent_configuration = AgentAuthConfiguration()

    with patch(
        "microsoft_agents.hosting.fastapi.jwt_authorization_middleware."
        "_authorize_request",
        new=AsyncMock(return_value=ClaimsIdentity({"sub": "agent-1"})),
    ) as authorize:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/messages")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    authorize.assert_awaited_once()
