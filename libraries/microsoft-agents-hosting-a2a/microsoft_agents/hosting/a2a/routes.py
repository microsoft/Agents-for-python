from a2a.server.agent_execution import RequestHandler
from a2a.server.routes import (
    create_jsonrpc_routes as _create_jsonrpc_routes,
    create_rest_routes as _create_rest_routes,
)

from starlette.routing import BaseRoute, Mount, Route

def create_jsonrpc_routes(
    request_handler: RequestHandler,
    enable_v0_3_compat: bool = False,
    path_prefix: str = ""
) -> list[BaseRoute]:

    
    
    return _create_jsonrpc_routes(
        request_handler,
        enable_v0_3_compat=enable_v0_3_compat,
        context_builder=context_builder,
        path_prefix=path_prefix
    )