# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Channel service route definitions (framework-agnostic logic)."""

from typing import Type, List, Union

from microsoft_agents.activity import (
    AgentsModel,
    Activity,
    AttachmentData,
    ConversationParameters,
    Transcript,
)
from microsoft_agents.hosting.core import ChannelApiHandlerProtocol

from ._http_request_protocol import HttpRequestProtocol


class ChannelServiceRoutes:
    """Defines the Channel Service API routes and their handlers.

    This class provides framework-agnostic route logic that can be
    adapted to different web frameworks (aiohttp, FastAPI, etc.).
    """

    def __init__(self, handler: ChannelApiHandlerProtocol, base_url: str = ""):
        """Initialize channel service routes.

        Args:
            handler: The handler that implements the Channel API protocol.
            base_url: Optional base URL prefix for all routes.
        """
        self.handler = handler
        self.base_url = base_url

    @staticmethod
    async def deserialize_from_body(
        request: HttpRequestProtocol, target_model: Type[AgentsModel]
    ) -> AgentsModel:
        """Deserialize request body to target model."""
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise ValueError("Content-Type must be application/json")

        body = await request.json()
        return target_model.model_validate(body)

    @staticmethod
    def serialize_model(model_or_list: Union[AgentsModel, List[AgentsModel]]) -> dict:
        """Serialize model or list of models to JSON-compatible dict."""
        if isinstance(model_or_list, AgentsModel):
            return model_or_list.model_dump(
                mode="json", exclude_unset=True, by_alias=True
            )
        else:
            return [
                model.model_dump(mode="json", exclude_unset=True, by_alias=True)
                for model in model_or_list
            ]

    # Route handler methods
    async def send_to_conversation(self, request: HttpRequestProtocol) -> dict:
        """Handle POST /v3/conversations/{conversation_id}/activities."""
        activity = await self.deserialize_from_body(request, Activity)
        conversation_id = request.get_path_param("conversation_id")
        result = await self.handler.on_send_to_conversation(
            request.get_claims_identity(),
            conversation_id,
            activity,
        )
        return self.serialize_model(result)

    async def reply_to_activity(self, request: HttpRequestProtocol) -> dict:
        """Handle POST /v3/conversations/{conversation_id}/activities/{activity_id}."""
        activity = await self.deserialize_from_body(request, Activity)
        conversation_id = request.get_path_param("conversation_id")
        activity_id = request.get_path_param("activity_id")
        result = await self.handler.on_reply_to_activity(
            request.get_claims_identity(),
            conversation_id,
            activity_id,
            activity,
        )
        return self.serialize_model(result)

    async def update_activity(self, request: HttpRequestProtocol) -> dict:
        """Handle PUT /v3/conversations/{conversation_id}/activities/{activity_id}."""
        activity = await self.deserialize_from_body(request, Activity)
        conversation_id = request.get_path_param("conversation_id")
        activity_id = request.get_path_param("activity_id")
        result = await self.handler.on_update_activity(
            request.get_claims_identity(),
            conversation_id,
            activity_id,
            activity,
        )
        return self.serialize_model(result)

    async def delete_activity(self, request: HttpRequestProtocol) -> None:
        """Handle DELETE /v3/conversations/{conversation_id}/activities/{activity_id}."""
        conversation_id = request.get_path_param("conversation_id")
        activity_id = request.get_path_param("activity_id")
        await self.handler.on_delete_activity(
            request.get_claims_identity(),
            conversation_id,
            activity_id,
        )

    async def get_activity_members(self, request: HttpRequestProtocol) -> dict:
        """Handle GET /v3/conversations/{conversation_id}/activities/{activity_id}/members."""
        conversation_id = request.get_path_param("conversation_id")
        activity_id = request.get_path_param("activity_id")
        result = await self.handler.on_get_activity_members(
            request.get_claims_identity(),
            conversation_id,
            activity_id,
        )
        return self.serialize_model(result)

    async def create_conversation(self, request: HttpRequestProtocol) -> dict:
        """Handle POST /."""
        conversation_parameters = await self.deserialize_from_body(
            request, ConversationParameters
        )
        result = await self.handler.on_create_conversation(
            request.get_claims_identity(), conversation_parameters
        )
        return self.serialize_model(result)

    async def get_conversations(self, request: HttpRequestProtocol) -> dict:
        """Handle GET /."""
        # TODO: continuation token? conversation_id?
        result = await self.handler.on_get_conversations(
            request.get_claims_identity(), None
        )
        return self.serialize_model(result)

    async def get_conversation_members(self, request: HttpRequestProtocol) -> dict:
        """Handle GET /v3/conversations/{conversation_id}/members."""
        conversation_id = request.get_path_param("conversation_id")
        result = await self.handler.on_get_conversation_members(
            request.get_claims_identity(),
            conversation_id,
        )
        return self.serialize_model(result)

    async def get_conversation_member(self, request: HttpRequestProtocol) -> dict:
        """Handle GET /v3/conversations/{conversation_id}/members/{member_id}."""
        conversation_id = request.get_path_param("conversation_id")
        member_id = request.get_path_param("member_id")
        result = await self.handler.on_get_conversation_member(
            request.get_claims_identity(),
            member_id,
            conversation_id,
        )
        return self.serialize_model(result)

    async def get_conversation_paged_members(
        self, request: HttpRequestProtocol
    ) -> dict:
        """Handle GET /v3/conversations/{conversation_id}/pagedmembers."""
        conversation_id = request.get_path_param("conversation_id")
        # TODO: continuation token? page size?
        result = await self.handler.on_get_conversation_paged_members(
            request.get_claims_identity(),
            conversation_id,
        )
        return self.serialize_model(result)

    async def delete_conversation_member(self, request: HttpRequestProtocol) -> dict:
        """Handle DELETE /v3/conversations/{conversation_id}/members/{member_id}."""
        conversation_id = request.get_path_param("conversation_id")
        member_id = request.get_path_param("member_id")
        result = await self.handler.on_delete_conversation_member(
            request.get_claims_identity(),
            conversation_id,
            member_id,
        )
        return self.serialize_model(result)

    async def send_conversation_history(self, request: HttpRequestProtocol) -> dict:
        """Handle POST /v3/conversations/{conversation_id}/activities/history."""
        conversation_id = request.get_path_param("conversation_id")
        transcript = await self.deserialize_from_body(request, Transcript)
        result = await self.handler.on_send_conversation_history(
            request.get_claims_identity(),
            conversation_id,
            transcript,
        )
        return self.serialize_model(result)

    async def upload_attachment(self, request: HttpRequestProtocol) -> dict:
        """Handle POST /v3/conversations/{conversation_id}/attachments."""
        conversation_id = request.get_path_param("conversation_id")
        attachment_data = await self.deserialize_from_body(request, AttachmentData)
        result = await self.handler.on_upload_attachment(
            request.get_claims_identity(),
            conversation_id,
            attachment_data,
        )
        return self.serialize_model(result)
