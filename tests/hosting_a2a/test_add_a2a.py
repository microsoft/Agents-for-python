# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from a2a.types import AgentCapabilities, AgentCard, AgentInterface
from a2a.utils.constants import TransportProtocol
from fastapi import FastAPI

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.http import HttpResponse
from microsoft_agents.hosting.a2a import add_a2a as exported_add_a2a
from microsoft_agents.hosting.a2a.add_a2a import add_a2a


def _adapter(*interfaces):
    return SimpleNamespace(
        agent_interfaces=list(interfaces),
        a2a_request_handler=MagicMock(),
        get_agent_card=AsyncMock(
            return_value=AgentCard(
                name="Test agent",
                description="Test agent description",
                version="1.0.0",
                supported_interfaces=[],
                capabilities=AgentCapabilities(),
            )
        ),
    )


@pytest.mark.asyncio
async def test_add_a2a_exposes_configured_jsonrpc_and_http_interfaces():
    app = FastAPI()
    adapter = _adapter(
        AgentInterface(
            url="/rpc",
            protocol_binding=TransportProtocol.JSONRPC,
        ),
        AgentInterface(
            url="/rest",
            protocol_binding=TransportProtocol.HTTP_JSON,
        ),
    )
    add_a2a(app, MagicMock(), adapter, use_jwt_middleware=False)

    paths = {route.path for route in app.routes}
    assert {
        "/rpc",
        "/rpc/.well-known/agent-card.json",
        "/rest/message:send",
        "/rest/tasks",
        "/rest/.well-known/agent-card.json",
    }.issubset(paths)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        rpc_card = await client.get("/rpc/.well-known/agent-card.json")
        rest_card = await client.get("/rest/.well-known/agent-card.json")

    assert rpc_card.status_code == 200
    assert rest_card.status_code == 200
    assert rpc_card.json()["name"] == "Test agent"
    assert rest_card.json()["name"] == "Test agent"
    assert {
        "/rpc",
        "/rpc/.well-known/agent-card.json",
        "/rest/message:send",
        "/rest/tasks",
        "/rest/.well-known/agent-card.json",
    }.issubset(app.openapi()["paths"])


@pytest.mark.asyncio
async def test_add_a2a_applies_jwt_middleware_to_registered_routes():
    app = FastAPI()
    app.state.agent_configuration = AgentAuthConfiguration()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    adapter = _adapter(
        AgentInterface(
            url="/rpc",
            protocol_binding=TransportProtocol.JSONRPC,
        )
    )
    add_a2a(app, MagicMock(), adapter)

    with patch(
        "microsoft_agents.hosting.fastapi.jwt_authorization_middleware."
        "_authorize_request",
        new=AsyncMock(
            return_value=HttpResponse(
                body={"error": "Authentication required"},
                status_code=401,
            )
        ),
    ) as authorize:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            health_response = await client.get("/health")
            card_response = await client.get("/rpc/.well-known/agent-card.json")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert card_response.status_code == 401
    assert card_response.json() == {"error": "Authentication required"}
    authorize.assert_awaited_once()


def test_add_a2a_rejects_adapter_without_interfaces():
    with pytest.raises(ValueError, match="No agent interfaces found"):
        add_a2a(FastAPI(), MagicMock(), _adapter())


def test_add_a2a_rejects_adapter_without_supported_interfaces():
    adapter = _adapter(
        AgentInterface(
            url="/grpc",
            protocol_binding=TransportProtocol.GRPC,
        )
    )

    with pytest.raises(ValueError, match="unsupported protocol bindings"):
        add_a2a(FastAPI(), MagicMock(), adapter, use_jwt_middleware=False)


def test_add_a2a_ignores_unsupported_interfaces_when_supported_ones_exist():
    app = FastAPI()
    adapter = _adapter(
        AgentInterface(
            url="/grpc",
            protocol_binding=TransportProtocol.GRPC,
        ),
        AgentInterface(
            url="/rpc",
            protocol_binding=TransportProtocol.JSONRPC,
        ),
    )

    add_a2a(app, MagicMock(), adapter, use_jwt_middleware=False)

    paths = {route.path for route in app.routes}
    assert "/rpc" in paths
    assert "/rpc/.well-known/agent-card.json" in paths
    assert "/grpc" not in paths
    assert "/grpc/.well-known/agent-card.json" not in paths


def test_add_a2a_is_exported_from_package():
    assert exported_add_a2a is add_a2a
