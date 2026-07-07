# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from microsoft_agents.hosting.core import ChannelApiHandlerProtocol
from microsoft_agents.hosting.core.http import ChannelServiceRoutes


class StarletteRequestAdapter:
    """Adapter for Starlette requests to use with ChannelServiceRoutes."""

    def __init__(self, request: Request):
        self._request = request

    @property
    def method(self) -> str:
        return self._request.method

    @property
    def headers(self):
        return self._request.headers

    async def json(self):
        return await self._request.json()

    def get_claims_identity(self):
        return getattr(self._request.state, "claims_identity", None)

    def get_path_param(self, name: str) -> str:
        return self._request.path_params.get(name, "")


# Table of channel-service endpoints: (path, http_method, ChannelServiceRoutes
# method name, returns_body). ``returns_body`` is False for endpoints that reply
# with a bare status code (no JSON body).
_ROUTES = [
    (
        "/v3/conversations/{conversation_id}/activities",
        "POST",
        "send_to_conversation",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/activities/{activity_id}",
        "POST",
        "reply_to_activity",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/activities/{activity_id}",
        "PUT",
        "update_activity",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/activities/{activity_id}",
        "DELETE",
        "delete_activity",
        False,
    ),
    (
        "/v3/conversations/{conversation_id}/activities/{activity_id}/members",
        "GET",
        "get_activity_members",
        True,
    ),
    ("/", "POST", "create_conversation", True),
    ("/", "GET", "get_conversations", True),
    (
        "/v3/conversations/{conversation_id}/members",
        "GET",
        "get_conversation_members",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/members/{member_id}",
        "GET",
        "get_conversation_member",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/pagedmembers",
        "GET",
        "get_conversation_paged_members",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/members/{member_id}",
        "DELETE",
        "delete_conversation_member",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/activities/history",
        "POST",
        "send_conversation_history",
        True,
    ),
    (
        "/v3/conversations/{conversation_id}/attachments",
        "POST",
        "upload_attachment",
        True,
    ),
]


def _make_endpoint(
    service_routes: ChannelServiceRoutes, method_name: str, returns_body: bool
):
    """Build a Starlette endpoint that dispatches to a ChannelServiceRoutes method."""
    service_method = getattr(service_routes, method_name)

    async def endpoint(request: Request):
        result = await service_method(StarletteRequestAdapter(request))
        if returns_body:
            return JSONResponse(content=result)
        return Response(status_code=200)

    return endpoint


def channel_service_routes(
    handler: ChannelApiHandlerProtocol, base_url: str = ""
) -> list[Route]:
    """Create the list of Starlette routes for the Channel Service API.

    The returned routes can be passed to a ``Starlette`` application (via the
    ``routes=`` argument) or mounted under a sub-path with ``starlette.routing.Mount``.

    Args:
        handler: The handler that implements the Channel API protocol.
        base_url: Optional base URL prefix for all routes.

    Returns:
        A list of ``starlette.routing.Route`` for all channel service endpoints.
    """
    service_routes = ChannelServiceRoutes(handler, base_url)
    return [
        Route(
            base_url + path,
            _make_endpoint(service_routes, method_name, returns_body),
            methods=[http_method],
        )
        for path, http_method, method_name, returns_body in _ROUTES
    ]
