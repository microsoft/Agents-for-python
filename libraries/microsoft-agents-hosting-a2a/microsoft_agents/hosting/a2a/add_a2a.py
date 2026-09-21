from fastapi import FastAPI

from a2a.server.routes import add_a2a_routes_to_fastapi

from microsoft_agents.hosting.core import Agent

from .a2a_adapter import A2AAdapter
from .server import (
    create_jsonrpc_routes,
    create_rest_routes,
    create_agent_card_routes,
    use_jwt_middleware as _use_jwt_middleware
)

def add_a2a(
    app: FastAPI,
    agent: Agent,
    adapter: A2AAdapter | None = None,
    *,
    default_path: str = "/a2a",
    use_jwt_middleware: bool = True,
):
    """Add A2A support to the given FastAPI app using the specified agent and adapter.

    :param app: The FastAPI app to which A2A support will be added.
    :param agent: The agent to use for A2A communication.
    :param adapter: An optional A2AAdapter instance. If not provided, a new one will be created using the agent.
    :param default_path: The default URL path for A2A routes.
    :param use_jwt_middleware: Whether to use JWT middleware for the routes.
    """

    adapter = adapter or A2AAdapter(agent)

    jsonrpc_routes = create_jsonrpc_routes(adapter.a2a_request_handler, rpc_url=default_path)
    rest_routes = create_rest_routes(adapter.a2a_request_handler, path_prefix=default_path)
    agent_card_routes = create_agent_card_routes(adapter.get_agent_card) 

    if use_jwt_middleware:
        _use_jwt_middleware(jsonrpc_routes)
        _use_jwt_middleware(rest_routes)
        _use_jwt_middleware(agent_card_routes)

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=agent_card_routes,
        jsonrpc_routes=jsonrpc_routes,
        rest_routes=rest_routes,
    )