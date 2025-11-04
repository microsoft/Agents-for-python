from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from microsoft_agents.hosting.core import (
    ChannelApiHandlerProtocol,
    ChannelServiceOperations,
    serialize_agents_model,
)


async def _read_payload(request: Request) -> Any:
    if "application/json" not in request.headers.get("Content-Type", ""):
        raise HTTPException(status_code=415, detail="Unsupported Media Type")
    return await request.json()


def _json_response(result: Any) -> Response:
    if result is None:
        return Response(status_code=200)

    payload = serialize_agents_model(result)
    return JSONResponse(content=payload)


def channel_service_route_table(
    handler: ChannelApiHandlerProtocol, base_url: str = ""
) -> APIRouter:
    router = APIRouter()
    operations = ChannelServiceOperations(handler)

    @router.post(base_url + "/v3/conversations/{conversation_id}/activities")
    async def send_to_conversation(conversation_id: str, request: Request):
        payload = await _read_payload(request)
        result = await operations.send_to_conversation(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            payload,
        )
        return _json_response(result)

    @router.post(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def reply_to_activity(
        conversation_id: str, activity_id: str, request: Request
    ):
        payload = await _read_payload(request)
        result = await operations.reply_to_activity(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity_id,
            payload,
        )
        return _json_response(result)

    @router.put(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def update_activity(conversation_id: str, activity_id: str, request: Request):
        payload = await _read_payload(request)
        result = await operations.update_activity(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity_id,
            payload,
        )
        return _json_response(result)

    @router.delete(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def delete_activity(conversation_id: str, activity_id: str, request: Request):
        await operations.delete_activity(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity_id,
        )
        return Response(status_code=200)

    @router.get(
        base_url
        + "/v3/conversations/{conversation_id}/activities/{activity_id}/members"
    )
    async def get_activity_members(
        conversation_id: str, activity_id: str, request: Request
    ):
        result = await operations.get_activity_members(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity_id,
        )
        return _json_response(result)

    @router.post(base_url + "/")
    async def create_conversation(request: Request):
        payload = await _read_payload(request)
        result = await operations.create_conversation(
            getattr(request.state, "claims_identity", None),
            payload,
        )
        return _json_response(result)

    @router.get(base_url + "/")
    async def get_conversation(request: Request):
        result = await operations.get_conversations(
            getattr(request.state, "claims_identity", None),
            None,
        )
        return _json_response(result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/members")
    async def get_conversation_members(conversation_id: str, request: Request):
        result = await operations.get_conversation_members(
            getattr(request.state, "claims_identity", None),
            conversation_id,
        )
        return _json_response(result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def get_conversation_member(
        conversation_id: str, member_id: str, request: Request
    ):
        result = await operations.get_conversation_member(
            getattr(request.state, "claims_identity", None),
            member_id,
            conversation_id,
        )
        return _json_response(result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/pagedmembers")
    async def get_conversation_paged_members(conversation_id: str, request: Request):
        result = await operations.get_conversation_paged_members(
            getattr(request.state, "claims_identity", None),
            conversation_id,
        )
        return _json_response(result)

    @router.delete(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def delete_conversation_member(
        conversation_id: str, member_id: str, request: Request
    ):
        result = await operations.delete_conversation_member(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            member_id,
        )
        return _json_response(result)

    @router.post(base_url + "/v3/conversations/{conversation_id}/activities/history")
    async def send_conversation_history(conversation_id: str, request: Request):
        payload = await _read_payload(request)
        result = await operations.send_conversation_history(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            payload,
        )
        return _json_response(result)

    @router.post(base_url + "/v3/conversations/{conversation_id}/attachments")
    async def upload_attachment(conversation_id: str, request: Request):
        payload = await _read_payload(request)
        result = await operations.upload_attachment(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            payload,
        )
        return _json_response(result)

    return router
