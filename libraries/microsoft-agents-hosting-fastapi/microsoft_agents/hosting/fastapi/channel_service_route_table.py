# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import json
from typing import List, Union, Type

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse

from microsoft_agents.activity import (
    AgentsModel,
    Activity,
    AttachmentData,
    ConversationParameters,
    Transcript,
)
from microsoft_agents.hosting.core import ChannelApiHandlerProtocol


async def deserialize_from_body(
    request: Request, target_model: Type[AgentsModel]
) -> AgentsModel:
    content_type = request.headers.get("Content-Type", "")
    if "application/json" in content_type:
        body = await request.json()
    else:
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    return target_model.model_validate(body)


def get_serialized_response(
    model_or_list: Union[AgentsModel, List[AgentsModel]],
) -> JSONResponse:
    if isinstance(model_or_list, AgentsModel):
        json_obj = model_or_list.model_dump(
            mode="json", exclude_unset=True, by_alias=True
        )
    else:
        json_obj = [
            model.model_dump(mode="json", exclude_unset=True, by_alias=True)
            for model in model_or_list
        ]

    return JSONResponse(content=json_obj)


def channel_service_route_table(
    handler: ChannelApiHandlerProtocol, base_url: str = ""
) -> APIRouter:
    router = APIRouter()

    @router.post(base_url + "/v3/conversations/{conversation_id}/activities")
    async def send_to_conversation(conversation_id: str, request: Request):
        activity = await deserialize_from_body(request, Activity)
        result = await handler.on_send_to_conversation(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity,
        )

        return get_serialized_response(result)

    @router.post(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def reply_to_activity(
        conversation_id: str, activity_id: str, request: Request
    ):
        activity = await deserialize_from_body(request, Activity)
        result = await handler.on_reply_to_activity(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity_id,
            activity,
        )

        return get_serialized_response(result)

    @router.put(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def update_activity(conversation_id: str, activity_id: str, request: Request):
        activity = await deserialize_from_body(request, Activity)
        result = await handler.on_update_activity(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity_id,
            activity,
        )

        return get_serialized_response(result)

    @router.delete(
        base_url + "/v3/conversations/{conversation_id}/activities/{activity_id}"
    )
    async def delete_activity(conversation_id: str, activity_id: str, request: Request):
        await handler.on_delete_activity(
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
        result = await handler.on_get_activity_members(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            activity_id,
        )

        return get_serialized_response(result)

    @router.post(base_url + "/")
    async def create_conversation(request: Request):
        conversation_parameters = await deserialize_from_body(
            request, ConversationParameters
        )
        result = await handler.on_create_conversation(
            getattr(request.state, "claims_identity", None), conversation_parameters
        )

        return get_serialized_response(result)

    @router.get(base_url + "/")
    async def get_conversation(request: Request):
        # TODO: continuation token? conversation_id?
        result = await handler.on_get_conversations(
            getattr(request.state, "claims_identity", None), None
        )

        return get_serialized_response(result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/members")
    async def get_conversation_members(conversation_id: str, request: Request):
        result = await handler.on_get_conversation_members(
            getattr(request.state, "claims_identity", None),
            conversation_id,
        )

        return get_serialized_response(result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def get_conversation_member(
        conversation_id: str, member_id: str, request: Request
    ):
        result = await handler.on_get_conversation_member(
            getattr(request.state, "claims_identity", None),
            member_id,
            conversation_id,
        )

        return get_serialized_response(result)

    @router.get(base_url + "/v3/conversations/{conversation_id}/pagedmembers")
    async def get_conversation_paged_members(conversation_id: str, request: Request):
        # TODO: continuation token? page size?
        result = await handler.on_get_conversation_paged_members(
            getattr(request.state, "claims_identity", None),
            conversation_id,
        )

        return get_serialized_response(result)

    @router.delete(base_url + "/v3/conversations/{conversation_id}/members/{member_id}")
    async def delete_conversation_member(
        conversation_id: str, member_id: str, request: Request
    ):
        result = await handler.on_delete_conversation_member(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            member_id,
        )

        return get_serialized_response(result)

    @router.post(base_url + "/v3/conversations/{conversation_id}/activities/history")
    async def send_conversation_history(conversation_id: str, request: Request):
        transcript = await deserialize_from_body(request, Transcript)
        result = await handler.on_send_conversation_history(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            transcript,
        )

        return get_serialized_response(result)

    @router.post(base_url + "/v3/conversations/{conversation_id}/attachments")
    async def upload_attachment(conversation_id: str, request: Request):
        attachment_data = await deserialize_from_body(request, AttachmentData)
        result = await handler.on_upload_attachment(
            getattr(request.state, "claims_identity", None),
            conversation_id,
            attachment_data,
        )

        return get_serialized_response(result)

    return router
