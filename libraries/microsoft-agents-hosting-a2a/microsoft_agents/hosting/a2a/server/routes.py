# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import hashlib

from datetime import datetime, timezone
from email.utils import format_datetime
from typing import Awaitable, Callable, Sequence

from a2a.server.routes import (
    create_jsonrpc_routes as _create_jsonrpc_routes,
    create_rest_routes as _create_rest_routes,
)
from a2a.server.request_handlers import RequestHandler
from a2a.server.request_handlers.response_helpers import agent_card_to_dict
from a2a.types import AgentCard
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, Mount, Route

from microsoft_agents.hosting.core import HttpRequestProtocol
from microsoft_agents.hosting.fastapi import (
    JwtAuthorizationMiddleware,
    jwt_authorization_decorator,
)
from microsoft_agents.hosting.fastapi._fastapi_request_adapter import (
    FastApiRequestAdapter,
)

from .sdk_server_call_context_builder import SDKServerCallContextBuilder
from ._utils import _get_interface_route_path

_AGENT_CARD_CACHE_CONTROL_TEMPLATE = "public, max-age={}"


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
        _get_interface_route_path(rpc_url),
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
    routes = _create_rest_routes(
        request_handler,
        context_builder=SDKServerCallContextBuilder(),
        enable_v0_3_compat=enable_v0_3_compat,
        path_prefix=_get_interface_route_path(path_prefix),
    )
    return routes


def create_agent_card_routes(
    get_agent_card: Callable[[HttpRequestProtocol, str], Awaitable[AgentCard]],
    card_url: str = AGENT_CARD_WELL_KNOWN_PATH,
    *,
    _cache_enabled: bool = False,
    cache_max_age: int = 3600,  # seconds, so 1 hour
) -> list[BaseRoute]:
    """Create routes for serving the agent card.

    :param get_agent_card: A callable that takes an HttpRequestProtocol and returns an AgentCard.
    :param card_url: The URL path for the agent card endpoint.
    :param _cache_enabled: Whether to enable public caching for the agent card. Default is False.
    :param cache_max_age: The maximum age, in seconds, for caching the agent card.
    :return: A list of Route objects representing the agent card routes.
    """

    if cache_max_age < 0:
        raise ValueError("cache_max_age must be non-negative")

    prefix = card_url
    try:
        i = card_url.index(AGENT_CARD_WELL_KNOWN_PATH)
        prefix = card_url[:i]
    except ValueError:
        # not found
        pass

    last_modified = format_datetime(datetime.now(timezone.utc), usegmt=True)

    async def _get_agent_card(request: Request) -> Response:
        """Retruns the public AgentCard describing this agent's capabilities, supported transports, and skills."""
        card = await get_agent_card(FastApiRequestAdapter(request), prefix)
        response = JSONResponse(agent_card_to_dict(card))
        if _cache_enabled:
            etag = f'"{hashlib.sha256(response.body).hexdigest()}"'
            headers = {
                "Cache-Control": _AGENT_CARD_CACHE_CONTROL_TEMPLATE.format(
                    cache_max_age
                ),
                "ETag": etag,
                "Last-Modified": last_modified,
            }
            response.headers.update(headers)
        else:
            response.headers["Cache-Control"] = "no-store"
        return response

    return [Route(path=card_url, endpoint=_get_agent_card, methods=["GET"])]


def use_jwt_middleware(routes: Sequence[BaseRoute]) -> None:
    """Wrap all routes with JWT authorization middleware.

    :param routes: A list of BaseRoute objects to wrap with JWT authorization middleware.
    """
    wrapped: set[int] = set()

    def wrap(route: BaseRoute) -> None:
        """Wrap the given route with JWT authorization middleware if it hasn't been wrapped already."""
        if isinstance(route, Mount):
            for child in route.routes:
                wrap(child)
        elif isinstance(route, Route) and id(route) not in wrapped:
            route.endpoint = jwt_authorization_decorator(route.endpoint)
            route.app = JwtAuthorizationMiddleware(route.app)
            wrapped.add(id(route))

    for route in routes:
        wrap(route)
