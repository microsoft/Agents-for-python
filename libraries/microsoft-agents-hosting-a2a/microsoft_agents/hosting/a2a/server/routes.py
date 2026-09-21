# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from a2a.server.routes import (
    create_jsonrpc_routes as _create_jsonrpc_routes,
    create_rest_routes as _create_rest_routes,
)
from a2a.server.request_handlers import RequestHandler

from starlette.routing import BaseRoute, Mount, Route

from microsoft_agents.hosting.fastapi import JwtAuthorizationMiddleware

from .sdk_server_call_context_builder import SDKServerCallContextBuilder


def create_jsonrpc_routes(
    request_handler: RequestHandler,
    rpc_url: str,
    enable_v0_3_compat: bool = False,
) -> list[Route]:
    """Create JSON-RPC routes with the given request handler and RPC URL.

    :param request_handler: The request handler to use for the JSON-RPC routes.
    :param rpc_url: The URL for the JSON-RPC endpoint.
    :param enable_v0_3_compat: Whether to enable compatibility with version 0.3.
    :return: A list of Route objects representing the JSON-RPC routes.
    """
    return _create_jsonrpc_routes(
        request_handler,
        rpc_url,
        context_builder=SDKServerCallContextBuilder(),
        enable_v0_3_compat=enable_v0_3_compat,
    )


def create_rest_routes(
    request_handler: RequestHandler,
    path_prefix: str = "",
    enable_v0_3_compat: bool = False,
) -> list[BaseRoute]:
    """Create REST routes with the given request handler and path prefix.

    :param request_handler: The request handler to use for the REST routes.
    :param path_prefix: The prefix to prepend to all REST route paths.
    :param enable_v0_3_compat: Whether to enable compatibility with version 0.3.
    :return: A list of BaseRoute objects representing the REST routes.
    """
    return _create_rest_routes(
        request_handler,
        context_builder=SDKServerCallContextBuilder(),
        enable_v0_3_compat=enable_v0_3_compat,
        path_prefix=path_prefix,
    )

def use_jwt_middleware(routes: list[BaseRoute]) -> None:
    """Wrap all routes with JWT authorization middleware.
    
    :param routes: A list of BaseRoute objects to wrap with JWT authorization middleware.
    """
    wrapped: set[int] = set()

    def wrap(route: BaseRoute) -> None:
        if isinstance(route, Mount):
            for child in route.routes:
                wrap(child)
        elif isinstance(route, Route) and id(route) not in wrapped:
            route.app = JwtAuthorizationMiddleware(route.app)
            wrapped.add(id(route))

    for route in routes:
        wrap(route)

    return routes