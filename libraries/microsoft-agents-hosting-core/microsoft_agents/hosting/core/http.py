# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Shared HTTP hosting utilities used by framework-specific adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from traceback import format_exc
from typing import Any, Generic, Optional, Protocol, Type, TypeVar

from microsoft_agents.activity import (
    Activity,
    AgentsModel,
    AttachmentData,
    ConversationParameters,
    DeliveryModes,
    Transcript,
)

from .authorization.claims_identity import ClaimsIdentity
from .authorization.connections import Connections
from .channel_api_handler_protocol import ChannelApiHandlerProtocol
from .channel_service_adapter import ChannelServiceAdapter
from .channel_service_client_factory_base import ChannelServiceClientFactoryBase
from .message_factory import MessageFactory
from .rest_channel_service_client_factory import RestChannelServiceClientFactory
from .turn_context import TurnContext

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from microsoft_agents.hosting.core.agent import Agent
    from microsoft_agents.hosting.core.app.agent_application import AgentApplication


TModel = TypeVar("TModel", bound=AgentsModel)
RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class AgentHttpAdapterProtocol(Protocol, Generic[RequestT, ResponseT]):
    """Protocol describing the contract for framework specific HTTP adapters."""

    async def process(self, request: RequestT, agent: "Agent") -> Optional[ResponseT]:
        raise NotImplementedError


async def start_agent_process(
    request: RequestT,
    agent_application: "AgentApplication",
    adapter: AgentHttpAdapterProtocol[RequestT, ResponseT],
) -> Optional[ResponseT]:
    """Start the agent process using the provided adapter and application."""
    if adapter is None:
        raise TypeError("start_agent_process: adapter can't be None")
    if agent_application is None:
        raise TypeError("start_agent_process: agent_application can't be None")

    return await adapter.process(request, agent_application)


def parse_agents_model(payload: Any, model_type: Type[TModel]) -> TModel:
    """Parse a payload into the requested AgentsModel derived type."""
    return model_type.model_validate(payload)


def serialize_agents_model(model_or_list: AgentsModel | Iterable[AgentsModel]) -> Any:
    """Serialize AgentsModel instances into JSON serialisable structures."""
    if isinstance(model_or_list, AgentsModel):
        return model_or_list.model_dump(mode="json", exclude_unset=True, by_alias=True)

    return [
        model.model_dump(mode="json", exclude_unset=True, by_alias=True)
        for model in model_or_list
    ]


class ChannelServiceOperations:
    """Shared activity channel operations used by HTTP frameworks."""

    def __init__(self, handler: ChannelApiHandlerProtocol) -> None:
        self._handler = handler

    async def send_to_conversation(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_payload: Any,
    ):
        activity = parse_agents_model(activity_payload, Activity)
        return await self._handler.on_send_to_conversation(
            claims_identity,
            conversation_id,
            activity,
        )

    async def reply_to_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
        activity_payload: Any,
    ):
        activity = parse_agents_model(activity_payload, Activity)
        return await self._handler.on_reply_to_activity(
            claims_identity,
            conversation_id,
            activity_id,
            activity,
        )

    async def update_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
        activity_payload: Any,
    ):
        activity = parse_agents_model(activity_payload, Activity)
        return await self._handler.on_update_activity(
            claims_identity,
            conversation_id,
            activity_id,
            activity,
        )

    async def delete_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
    ) -> None:
        await self._handler.on_delete_activity(
            claims_identity,
            conversation_id,
            activity_id,
        )

    async def get_activity_members(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
    ):
        return await self._handler.on_get_activity_members(
            claims_identity,
            conversation_id,
            activity_id,
        )

    async def create_conversation(
        self,
        claims_identity: ClaimsIdentity,
        parameters_payload: Any,
    ):
        parameters = parse_agents_model(parameters_payload, ConversationParameters)
        return await self._handler.on_create_conversation(
            claims_identity,
            parameters,
        )

    async def get_conversations(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str | None = None,
    ):
        return await self._handler.on_get_conversations(
            claims_identity,
            conversation_id,
        )

    async def get_conversation_members(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
    ):
        return await self._handler.on_get_conversation_members(
            claims_identity,
            conversation_id,
        )

    async def get_conversation_member(
        self,
        claims_identity: ClaimsIdentity,
        user_id: str,
        conversation_id: str,
    ):
        return await self._handler.on_get_conversation_member(
            claims_identity,
            user_id,
            conversation_id,
        )

    async def get_conversation_paged_members(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        page_size: int | None = None,
        continuation_token: str | None = None,
    ):
        return await self._handler.on_get_conversation_paged_members(
            claims_identity,
            conversation_id,
            page_size,
            continuation_token,
        )

    async def delete_conversation_member(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        member_id: str,
    ):
        return await self._handler.on_delete_conversation_member(
            claims_identity,
            conversation_id,
            member_id,
        )

    async def send_conversation_history(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        transcript_payload: Any,
    ):
        transcript = parse_agents_model(transcript_payload, Transcript)
        return await self._handler.on_send_conversation_history(
            claims_identity,
            conversation_id,
            transcript,
        )

    async def upload_attachment(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        attachment_payload: Any,
    ):
        attachment = parse_agents_model(attachment_payload, AttachmentData)
        return await self._handler.on_upload_attachment(
            claims_identity,
            conversation_id,
            attachment,
        )


class CloudAdapterBase(ChannelServiceAdapter, Generic[RequestT, ResponseT], ABC):
    """Base implementation for framework specific CloudAdapter implementations."""

    def __init__(
        self,
        *,
        connection_manager: Connections | None = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase | None = None,
    ) -> None:
        async def on_turn_error(context: TurnContext, error: Exception) -> None:
            error_message = f"Exception caught : {error}"
            print(format_exc())

            await context.send_activity(MessageFactory.text(error_message))

            await context.send_trace_activity(
                "OnTurnError Trace",
                error_message,
                "https://www.botframework.com/schemas/error",
                "TurnError",
            )

        self.on_turn_error = on_turn_error

        factory = channel_service_client_factory or RestChannelServiceClientFactory(
            connection_manager
        )

        super().__init__(factory)

    async def process(
        self, request: RequestT, agent: "Agent"
    ) -> Optional[ResponseT]:  # pragma: no cover - exercised via subclasses
        if request is None:
            raise TypeError("CloudAdapter.process: request can't be None")
        if agent is None:
            raise TypeError("CloudAdapter.process: agent can't be None")

        if self._get_method(request) != "POST":
            raise self._method_not_allowed_error(request)

        body = await self._read_json_body(request)
        activity: Activity = Activity.model_validate(body)

        claims_identity = self._get_claims_identity(request)
        if not claims_identity:
            claims_identity = self._default_claims_identity()

        if (
            not activity.type
            or not activity.conversation
            or not activity.conversation.id
        ):
            raise self._bad_request_error(request)

        try:
            invoke_response = await self.process_activity(
                claims_identity,
                activity,
                agent.on_turn,
            )
        except PermissionError as error:
            raise self._unauthorized_error(request) from error

        if (
            activity.type == "invoke"
            or activity.delivery_mode == DeliveryModes.expect_replies
        ):
            return self._create_invoke_response(request, invoke_response)

        return self._create_accepted_response(request)

    def _default_claims_identity(self) -> ClaimsIdentity:
        return ClaimsIdentity({}, False)

    @abstractmethod
    def _get_method(self, request: RequestT) -> str:
        """Return the HTTP method for the incoming request."""

    @abstractmethod
    async def _read_json_body(self, request: RequestT) -> Any:
        """Read and return the JSON payload."""

    @abstractmethod
    def _get_claims_identity(self, request: RequestT) -> ClaimsIdentity | None:
        """Extract the claims identity from the request."""

    @abstractmethod
    def _method_not_allowed_error(self, request: RequestT) -> Exception:
        """Return the exception raised when the request method is unsupported."""

    @abstractmethod
    def _unsupported_media_type_error(self, request: RequestT) -> Exception:
        """Return the exception raised when the content type is unsupported."""

    @abstractmethod
    def _bad_request_error(self, request: RequestT) -> Exception:
        """Return the exception raised when the request payload is invalid."""

    @abstractmethod
    def _unauthorized_error(self, request: RequestT) -> Exception:
        """Return the exception raised when authorization fails."""

    @abstractmethod
    def _create_invoke_response(
        self, request: RequestT, invoke_response: Any
    ) -> ResponseT:
        """Create the framework specific response for invoke results."""

    @abstractmethod
    def _create_accepted_response(self, request: RequestT) -> ResponseT:
        """Create the framework specific HTTP 202 response."""
