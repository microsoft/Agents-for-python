# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import json
from typing import List, Union, Type

from aiohttp.web import RouteTableDef, Request, Response

from microsoft.agents.activity import (
    AgentsModel,
    Activity,
    AttachmentData,
    ConversationParameters,
    Transcript,
)
from microsoft.agents.hosting.core import ChannelApiHandlerProtocol


async def deserialize_from_body(
    request: Request, target_model: Type[AgentsModel]
) -> Activity:
    if "application/json" in request.headers["Content-Type"]:
        body = await request.json()
    else:
        return Response(status=415)

    return target_model.model_validate(body)


def get_serialized_response(
    model_or_list: Union[AgentsModel, List[AgentsModel]],
) -> Response:
    if isinstance(model_or_list, AgentsModel):
        json_obj = model_or_list.model_dump(
            mode="json", exclude_unset=True, by_alias=True
        )
    else:
        json_obj = [
            model.model_dump(mode="json", exclude_unset=True, by_alias=True)
            for model in model_or_list
        ]

    return Response(body=json.dumps(json_obj), content_type="application/json")


def channel_service_route_table(
    handler: ChannelApiHandlerProtocol, base_url: str = ""
) -> RouteTableDef:
    # pylint: disable=unused-variable
    routes = RouteTableDef()

    @routes.post(base_url + "/v3/conversations/{conversation_id}/activities")
    async def send_to_conversation(request: Request):
        activity = await deserialize_from_body(request, Activity)
        result = await handler.on_send_to_conversation(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            activity,
        )

        return get_serialized_response(result)

    @routes.post(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def reply_to_activity(request: Request):
        activity = await deserialize_from_body(request, Activity)
        result = await handler.on_reply_to_activity(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["activity_id"],
            activity,
        )

        return get_serialized_response(result)

    @routes.put(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def update_activity(request: Request):
        activity = await deserialize_from_body(request, Activity)
        result = await handler.on_update_activity(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["activity_id"],
            activity,
        )

        return get_serialized_response(result)

    @routes.delete(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def delete_activity(request: Request):
        await handler.on_delete_activity(
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
        result = await handler.on_get_activity_members(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["activity_id"],
        )

        return get_serialized_response(result)

    @routes.post(base_url + "/")
    async def create_conversation(request: Request):
        conversation_parameters = deserialize_from_body(request, ConversationParameters)
        result = await handler.on_create_conversation(
            request.get("claims_identity"), conversation_parameters
        )

        return get_serialized_response(result)

    @routes.get(base_url + "/")
    async def get_conversation(request: Request):
        # TODO: continuation token? conversation_id?
        result = await handler.on_get_conversations(
            request.get("claims_identity"), None
        )

        return get_serialized_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/members")
    async def get_conversation_members(request: Request):
        result = await handler.on_get_conversation_members(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
        )

        return get_serialized_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def get_conversation_member(request: Request):
        result = await handler.on_get_conversation_member(
            request.get("claims_identity"),
            request.match_info["member_id"],
            request.match_info["conversation_id"],
        )

        return get_serialized_response(result)

    @routes.get(base_url + "/v3/conversations/{conversation_id}/pagedmembers")
    async def get_conversation_paged_members(request: Request):
        # TODO: continuation token? page size?
        result = await handler.on_get_conversation_paged_members(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
        )

        return get_serialized_response(result)

    @routes.delete(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def delete_conversation_member(request: Request):
        result = await handler.on_delete_conversation_member(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            request.match_info["member_id"],
        )

        return get_serialized_response(result)

    @routes.post(base_url + "/v3/conversations/{conversation_id}/activities/history")
    async def send_conversation_history(request: Request):
        transcript = deserialize_from_body(request, Transcript)
        result = await handler.on_send_conversation_history(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            transcript,
        )

        return get_serialized_response(result)

    @routes.post(base_url + "/v3/conversations/{conversation_id}/attachments")
    async def upload_attachment(request: Request):
        attachment_data = deserialize_from_body(request, AttachmentData)
        result = await handler.on_upload_attachment(
            request.get("claims_identity"),
            request.match_info["conversation_id"],
            attachment_data,
        )

        return get_serialized_response(result)

    return routes
