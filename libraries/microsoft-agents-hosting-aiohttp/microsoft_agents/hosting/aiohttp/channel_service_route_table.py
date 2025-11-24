# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import json

from aiohttp.web import RouteTableDef, Request, Response

from microsoft_agents.hosting.core import ChannelApiHandlerProtocol
from microsoft_agents.hosting.core.http import ChannelServiceRoutes


class AiohttpRequestAdapter:
    """Adapter for aiohttp requests to use with ChannelServiceRoutes."""

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
        return self._request.get("claims_identity")

    def get_path_param(self, name: str) -> str:
        return self._request.match_info[name]


def channel_service_route_table(
    handler: ChannelApiHandlerProtocol, base_url: str = ""
) -> RouteTableDef:
    """Create aiohttp route table for Channel Service API.

    Args:
        handler: The handler that implements the Channel API protocol.
        base_url: Optional base URL prefix for all routes.

    Returns:
        RouteTableDef with all channel service routes.
    """
    routes = RouteTableDef()
    service_routes = ChannelServiceRoutes(handler, base_url)

    def json_response(data: dict) -> Response:
        return Response(body=json.dumps(data), content_type="application/json")

    @routes.post(base_url + "/v3/conversations/{conversation_id}/activities")
    async def send_to_conversation(request: Request):
        result = await service_routes.send_to_conversation(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.post(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def reply_to_activity(request: Request):
        result = await service_routes.reply_to_activity(AiohttpRequestAdapter(request))
        return json_response(result)

    @routes.put(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def update_activity(request: Request):
        result = await service_routes.update_activity(AiohttpRequestAdapter(request))
        return json_response(result)

    @routes.delete(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def delete_activity(request: Request):
        await service_routes.delete_activity(AiohttpRequestAdapter(request))
        return Response()

    @routes.get(
        base_url
        + "/v3/conversations/{conversation_id}/activities/{activity_id}/members"
    )
    async def get_activity_members(request: Request):
        result = await service_routes.get_activity_members(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.post(base_url + "/")
    async def create_conversation(request: Request):
        result = await service_routes.create_conversation(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.get(base_url + "/")
    async def get_conversation(request: Request):
        result = await service_routes.get_conversations(AiohttpRequestAdapter(request))
        return json_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/members")
    async def get_conversation_members(request: Request):
        result = await service_routes.get_conversation_members(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def get_conversation_member(request: Request):
        result = await service_routes.get_conversation_member(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/pagedmembers")
    async def get_conversation_paged_members(request: Request):
        result = await service_routes.get_conversation_paged_members(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.delete(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def delete_conversation_member(request: Request):
        result = await service_routes.delete_conversation_member(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.post(base_url + "/v3/conversations/{conversation_id}/activities/history")
    async def send_conversation_history(request: Request):
        result = await service_routes.send_conversation_history(
            AiohttpRequestAdapter(request)
        )
        return json_response(result)

    @routes.post(base_url + "/v3/conversations/{conversation_id}/attachments")
    async def upload_attachment(request: Request):
        result = await service_routes.upload_attachment(AiohttpRequestAdapter(request))
        return json_response(result)

    return routes
