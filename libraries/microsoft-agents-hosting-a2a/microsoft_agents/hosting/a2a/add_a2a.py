# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from fastapi import FastAPI
from starlette.routing import BaseRoute, Route

from a2a.server.routes import add_a2a_routes_to_fastapi
from a2a.types import AgentInterface
from a2a.utils.constants import TransportProtocol, AGENT_CARD_WELL_KNOWN_PATH

from microsoft_agents.hosting.core import AgentApplication

from .a2a_adapter import A2AAdapter
from .server import (
    create_jsonrpc_routes,
    create_rest_routes,
    create_agent_card_routes,
    use_jwt_middleware as _use_jwt_middleware,
)

logger = logging.getLogger(__name__)


def _create_jsonrpc_interface_routes(
    adapter: A2AAdapter,
    interface: AgentInterface,
    _agent_card_cache_enabled: bool = False,
    agent_card_cache_max_age: int = 3600,
) -> tuple[list[Route], list[BaseRoute]]:
    """Create JSON-RPC interface routes for the given agent interface.

    :param adapter: The A2AAdapter instance used to handle requests.
    :param interface: The agent interface to add routes for.
    :param _agent_card_cache_enabled: Whether to enable caching for the agent card. Default is False.
    :param agent_card_cache_max_age: The maximum age (in seconds) for caching the agent card. Default is 3600 seconds (1 hour).
    """

    jsonrpc_routes = create_jsonrpc_routes(
        adapter.a2a_request_handler, rpc_url=interface.url
    )
    agent_card_routes = create_agent_card_routes(
        adapter.get_agent_card,
        f"{interface.url}{AGENT_CARD_WELL_KNOWN_PATH}",
        _cache_enabled=_agent_card_cache_enabled,
        cache_max_age=agent_card_cache_max_age,
    )
    return jsonrpc_routes, agent_card_routes


def _create_http_interface_routes(
    adapter: A2AAdapter,
    interface: AgentInterface,
    _agent_card_cache_enabled: bool = False,
    agent_card_cache_max_age: int = 3600,
) -> tuple[list[BaseRoute], list[BaseRoute]]:
    """Create HTTP interface routes for the given agent interface.

    :param adapter: The A2AAdapter instance used to handle requests.
    :param interface: The agent interface to add routes for.
    :param _agent_card_cache_enabled: Whether to enable caching for the agent card. Default is False.
    :param agent_card_cache_max_age: The maximum age (in seconds) for caching the agent card. Default is 3600 seconds (1 hour).
    """
    http_routes = create_rest_routes(
        adapter.a2a_request_handler, path_prefix=interface.url
    )
    agent_card_routes = create_agent_card_routes(
        adapter.get_agent_card,
        f"{interface.url}{AGENT_CARD_WELL_KNOWN_PATH}",
        _cache_enabled=_agent_card_cache_enabled,
        cache_max_age=agent_card_cache_max_age,
    )
    return http_routes, agent_card_routes


def add_a2a(
    app: FastAPI,
    agent: AgentApplication,
    adapter: A2AAdapter | None = None,
    *,
    use_jwt_middleware: bool = True,
    _agent_card_cache_enabled: bool = False,
    agent_card_cache_max_age: int = 3600,
):
    """Add A2A support to the given FastAPI app using the specified agent and adapter.

    :param app: The FastAPI app to which A2A support will be added.
    :param agent: The agent to use for A2A communication.
    :param adapter: An optional A2AAdapter instance. If not provided, a new one will be created using the agent.
    :param use_jwt_middleware: Whether to use JWT middleware for the routes.
    :param _agent_card_cache_enabled: Whether to enable caching for the agent card. Default is False.
    :param agent_card_cache_max_age: The maximum age (in seconds) for caching the agent card. Default is 3600 seconds (1 hour).
    """

    adapter = adapter or A2AAdapter(
        agent,
        agent_interfaces=[
            AgentInterface(
                url="/a2a",
                protocol_binding=TransportProtocol.JSONRPC,
            )
        ],
    )

    agent_card_routes: list[BaseRoute] = []
    jsonrpc_routes: list[BaseRoute] = []
    rest_routes: list[BaseRoute] = []

    interfaces = adapter.agent_interfaces
    if not interfaces:
        raise ValueError(
            "No agent interfaces found. Cannot add A2A routes to application."
        )

    unsupported_counter = 0
    for interface in interfaces:
        if interface.protocol_binding == TransportProtocol.JSONRPC:
            _jsonrpc_routes, _agent_card_routes = _create_jsonrpc_interface_routes(
                adapter,
                interface,
                _agent_card_cache_enabled=_agent_card_cache_enabled,
                agent_card_cache_max_age=agent_card_cache_max_age,
            )
            jsonrpc_routes.extend(_jsonrpc_routes)
            agent_card_routes.extend(_agent_card_routes)
        elif interface.protocol_binding == TransportProtocol.HTTP_JSON:
            _http_routes, _agent_card_routes = _create_http_interface_routes(
                adapter,
                interface,
                _agent_card_cache_enabled=_agent_card_cache_enabled,
                agent_card_cache_max_age=agent_card_cache_max_age,
            )
            rest_routes.extend(_http_routes)
            agent_card_routes.extend(_agent_card_routes)
        else:
            unsupported_counter += 1
            logger.warning(
                "Unsupported protocol binding: %s", interface.protocol_binding
            )

    if unsupported_counter == len(interfaces):
        raise ValueError(
            "All agent interfaces have unsupported protocol bindings. Cannot add A2A routes to application."
        )

    if use_jwt_middleware:
        _use_jwt_middleware(agent_card_routes)
        _use_jwt_middleware(jsonrpc_routes)
        _use_jwt_middleware(rest_routes)

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=agent_card_routes,
        jsonrpc_routes=jsonrpc_routes,
        rest_routes=rest_routes,
    )
