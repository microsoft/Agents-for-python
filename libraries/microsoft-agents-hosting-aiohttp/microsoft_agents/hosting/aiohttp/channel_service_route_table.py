import json
from typing import Any

from aiohttp.web import HTTPUnsupportedMediaType, Request, Response, RouteTableDef

from microsoft_agents.hosting.core import (
    ChannelApiHandlerProtocol,
    ChannelServiceOperations,
    serialize_agents_model,
)


async def _read_payload(request: Request) -> Any:
    if "application/json" not in request.headers.get("Content-Type", ""):
        raise HTTPUnsupportedMediaType()
    return await request.json()


def _json_response(result: Any) -> Response:
    if result is None:
        return Response()

    payload = serialize_agents_model(result)
    return Response(body=json.dumps(payload), content_type="application/json")


def channel_service_route_table(
    handler: ChannelApiHandlerProtocol, base_url: str = ""
) -> RouteTableDef:
    routes = RouteTableDef()
    operations = ChannelServiceOperations(handler)

    @routes.post(base_url + "/v3/conversations/{conversation_id}/activities")
    async def send_to_conversation(request: Request):
        payload = await _read_payload(request)
        result = await operations.send_to_conversation(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            payload,
        )
        return _json_response(result)

    @routes.post(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def reply_to_activity(request: Request):
        payload = await _read_payload(request)
        result = await operations.reply_to_activity(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["activity_id"],
            payload,
        )
        return _json_response(result)

    @routes.put(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def update_activity(request: Request):
        payload = await _read_payload(request)
        result = await operations.update_activity(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["activity_id"],
            payload,
        )
        return _json_response(result)

    @routes.delete(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def delete_activity(request: Request):
        await operations.delete_activity(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["activity_id"],
        )
        return Response()

    @routes.get(
        base_url
        + "/v3/conversations/{conversation_id}/activities/{activity_id}/members"
    )
    async def get_activity_members(request: Request):
        result = await operations.get_activity_members(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["activity_id"],
        )
        return _json_response(result)

    @routes.post(base_url + "/")
    async def create_conversation(request: Request):
        payload = await _read_payload(request)
        result = await operations.create_conversation(
            request.get("claims_identity"),
            payload,
        )
        return _json_response(result)

    @routes.get(base_url + "/")
    async def get_conversation(request: Request):
        result = await operations.get_conversations(
            request.get("claims_identity"),
            None,
        )
        return _json_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/members")
    async def get_conversation_members(request: Request):
        result = await operations.get_conversation_members(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
        )
        return _json_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def get_conversation_member(request: Request):
        result = await operations.get_conversation_member(
            request.get("claims_identity"),
            request.match_info["member_id"],
            request.match_info["conversation_id"],
        )
        return _json_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/pagedmembers")
    async def get_conversation_paged_members(request: Request):
        result = await operations.get_conversation_paged_members(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
        )
        return _json_response(result)

    @routes.delete(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def delete_conversation_member(request: Request):
        result = await operations.delete_conversation_member(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["member_id"],
        )
        return _json_response(result)

    @routes.post(base_url + "/v3/conversations/{conversation_id}/activities/history")
    async def send_conversation_history(request: Request):
        payload = await _read_payload(request)
        result = await operations.send_conversation_history(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            payload,
        )
        return _json_response(result)

    @routes.post(base_url + "/v3/conversations/{conversation_id}/attachments")
    async def upload_attachment(request: Request):
        payload = await _read_payload(request)
        result = await operations.upload_attachment(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            payload,
        )
        return _json_response(result)

    return routes
