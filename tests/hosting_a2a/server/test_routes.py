# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.routing import Mount, Route

from microsoft_agents.hosting.fastapi import JwtAuthorizationMiddleware
from microsoft_agents.hosting.a2a.server import routes
from microsoft_agents.hosting.a2a.server.sdk_server_call_context_builder import (
    SDKServerCallContextBuilder,
)


def test_create_jsonrpc_routes_supplies_sdk_context_builder():
    request_handler = MagicMock()
    expected_routes = [MagicMock(spec=Route)]

    with patch.object(
        routes,
        "_create_jsonrpc_routes",
        return_value=expected_routes,
    ) as create_routes:
        result = routes.create_jsonrpc_routes(
            request_handler,
            "/a2a",
            enable_v0_3_compat=True,
        )

    assert result is expected_routes
    create_routes.assert_called_once()
    assert create_routes.call_args.args == (request_handler, "/a2a")
    assert isinstance(
        create_routes.call_args.kwargs["context_builder"],
        SDKServerCallContextBuilder,
    )
    assert create_routes.call_args.kwargs["enable_v0_3_compat"] is True


def test_create_rest_routes_supplies_sdk_context_builder():
    request_handler = MagicMock()
    expected_routes = [MagicMock(spec=Route)]

    with patch.object(
        routes,
        "_create_rest_routes",
        return_value=expected_routes,
    ) as create_routes:
        result = routes.create_rest_routes(
            request_handler,
            path_prefix="/a2a",
            enable_v0_3_compat=True,
        )

    assert result is expected_routes
    create_routes.assert_called_once()
    assert create_routes.call_args.args == (request_handler,)
    assert isinstance(
        create_routes.call_args.kwargs["context_builder"],
        SDKServerCallContextBuilder,
    )
    assert create_routes.call_args.kwargs["path_prefix"] == "/a2a"
    assert create_routes.call_args.kwargs["enable_v0_3_compat"] is True


@pytest.mark.asyncio
async def test_create_agent_card_routes_adapts_request_and_uses_interface_prefix():
    get_agent_card = AsyncMock(return_value=MagicMock())
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

    with patch.object(routes, "agent_card_to_dict", return_value={"name": "agent"}):
        response = await route.endpoint(request)

    assert route.path == "/a2a/.well-known/agent-card.json"
    assert response.status_code == 200
    assert response.body == b'{"name":"agent"}'
    get_agent_card.assert_awaited_once()
    assert get_agent_card.call_args.args[1] == "/a2a"


def test_use_jwt_middleware_wraps_shared_mounted_route_once():
    async def endpoint(request):
        return None

    route = Route("/messages", endpoint=endpoint)
    original_app = route.app
    mounted = Mount("/tenant", routes=[route])

    routes.use_jwt_middleware([route, mounted])

    assert isinstance(route.app, JwtAuthorizationMiddleware)
    assert route.app.app is original_app
