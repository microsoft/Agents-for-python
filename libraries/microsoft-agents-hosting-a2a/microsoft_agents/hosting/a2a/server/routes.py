# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from a2a.server.routes import (
    create_jsonrpc_routes as _create_jsonrpc_routes,
    create_rest_routes as _create_rest_routes,
)
from a2a.server.request_handlers import RequestHandler

from starlette.routing import BaseRoute, Route

from .sdk_server_call_context_builder import SDKServerCallContextBuilder

from microsoft_agents.hosting.fastapi import JwtAuthorizationMiddleware


def create_jsonrpc_routes(
    request_handler: RequestHandler,
    rpc_url: str,
    enable_v0_3_compat: bool = False,
) -> list[Route]:
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
    return _create_rest_routes(
        request_handler,
        context_builder=SDKServerCallContextBuilder(),
        enable_v0_3_compat=enable_v0_3_compat,
        path_prefix=path_prefix,
    )

def add_jwt_middleware(routes: list[BaseRoute]) -> list[BaseRoute]:
    # Implement the JWT middleware addition logic here
    return routes