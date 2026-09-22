# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from a2a.types import AgentInterface
from a2a.utils.constants import TransportProtocol
from fastapi import FastAPI

from microsoft_agents.hosting.a2a import add_a2a as exported_add_a2a
from microsoft_agents.hosting.a2a.add_a2a import add_a2a

add_a2a_module = importlib.import_module("microsoft_agents.hosting.a2a.add_a2a")


def _adapter(*interfaces):
    return SimpleNamespace(
        agent_interfaces=list(interfaces),
        a2a_request_handler=MagicMock(),
        get_agent_card=MagicMock(),
    )


def test_add_a2a_registers_jsonrpc_and_http_interfaces_with_jwt():
    app = FastAPI()
    agent = MagicMock()
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
    jsonrpc_routes = [MagicMock()]
    jsonrpc_card_routes = [MagicMock()]
    rest_routes = [MagicMock()]
    rest_card_routes = [MagicMock()]

    with (
        patch.object(
            add_a2a_module,
            "_create_jsonrpc_interface_routes",
            return_value=(jsonrpc_routes, jsonrpc_card_routes),
        ) as create_jsonrpc,
        patch.object(
            add_a2a_module,
            "_create_http_interface_routes",
            return_value=(rest_routes, rest_card_routes),
        ) as create_http,
        patch.object(add_a2a_module, "_use_jwt_middleware") as use_jwt,
        patch.object(
            add_a2a_module,
            "add_a2a_routes_to_fastapi",
        ) as register_routes,
    ):
        add_a2a(app, agent, adapter)

    create_jsonrpc.assert_called_once_with(adapter, adapter.agent_interfaces[0])
    create_http.assert_called_once_with(adapter, adapter.agent_interfaces[1])
    assert use_jwt.call_args_list == [
        call(jsonrpc_card_routes + rest_card_routes),
        call(jsonrpc_routes),
        call(rest_routes),
    ]
    register_routes.assert_called_once_with(
        app,
        agent_card_routes=jsonrpc_card_routes + rest_card_routes,
        jsonrpc_routes=jsonrpc_routes,
        rest_routes=rest_routes,
    )


def test_add_a2a_can_skip_jwt_middleware():
    app = FastAPI()
    adapter = _adapter()

    with (
        patch.object(add_a2a_module, "_use_jwt_middleware") as use_jwt,
        patch.object(add_a2a_module, "add_a2a_routes_to_fastapi"),
    ):
        add_a2a(app, MagicMock(), adapter, use_jwt_middleware=False)

    use_jwt.assert_not_called()


def test_add_a2a_is_exported_from_package():
    assert exported_add_a2a is add_a2a
