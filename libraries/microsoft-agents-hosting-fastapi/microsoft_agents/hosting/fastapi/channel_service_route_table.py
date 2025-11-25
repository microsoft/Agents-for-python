# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from microsoft_agents.hosting.core import ChannelApiHandlerProtocol
from microsoft_agents.hosting.core.http import ChannelServiceRoutes


class FastApiRequestAdapter:
    """Adapter for FastAPI requests to use with ChannelServiceRoutes."""

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


def channel_service_route_table(
    handler: ChannelApiHandlerProtocol, base_url: str = ""
) -> APIRouter:
    """Create FastAPI router for Channel Service API.

    Args:
        handler: The handler that implements the Channel API protocol.
        base_url: Optional base URL prefix for all routes.

    Returns:
        APIRouter with all channel service routes.
    """
    router = APIRouter()
    service_routes = ChannelServiceRoutes(handler, base_url)

    @router.post(base_url + "/v3/conversations/{conversation_id}/activities")
    async def send_to_conversation(conversation_id: str, request: Request):
        result = await service_routes.send_to_conversation(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.post(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def reply_to_activity(
        conversation_id: str, activity_id: str, request: Request
    ):
        result = await service_routes.reply_to_activity(FastApiRequestAdapter(request))
        return JSONResponse(content=result)

    @router.put(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def update_activity(conversation_id: str, activity_id: str, request: Request):
        result = await service_routes.update_activity(FastApiRequestAdapter(request))
        return JSONResponse(content=result)

    @router.delete(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def delete_activity(conversation_id: str, activity_id: str, request: Request):
        await service_routes.delete_activity(FastApiRequestAdapter(request))
        return Response(status_code=200)

    @router.get(
        base_url
        + "/v3/conversations/{conversation_id}/activities/{activity_id}/members"
    )
    async def get_activity_members(
        conversation_id: str, activity_id: str, request: Request
    ):
        result = await service_routes.get_activity_members(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.post(base_url + "/")
    async def create_conversation(request: Request):
        result = await service_routes.create_conversation(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.get(base_url + "/")
    async def get_conversation(request: Request):
        result = await service_routes.get_conversations(FastApiRequestAdapter(request))
        return JSONResponse(content=result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/members")
    async def get_conversation_members(conversation_id: str, request: Request):
        result = await service_routes.get_conversation_members(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def get_conversation_member(
        conversation_id: str, member_id: str, request: Request
    ):
        result = await service_routes.get_conversation_member(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/pagedmembers")
    async def get_conversation_paged_members(conversation_id: str, request: Request):
        result = await service_routes.get_conversation_paged_members(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.delete(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def delete_conversation_member(
        conversation_id: str, member_id: str, request: Request
    ):
        result = await service_routes.delete_conversation_member(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.post(base_url + "/v3/conversations/{conversation_id}/activities/history")
    async def send_conversation_history(conversation_id: str, request: Request):
        result = await service_routes.send_conversation_history(
            FastApiRequestAdapter(request)
        )
        return JSONResponse(content=result)

    @router.post(base_url + "/v3/conversations/{conversation_id}/attachments")
    async def upload_attachment(conversation_id: str, request: Request):
        result = await service_routes.upload_attachment(FastApiRequestAdapter(request))
        return JSONResponse(content=result)

    return router
