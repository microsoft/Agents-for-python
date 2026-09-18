# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol, Callable, Awaitable

from typing_extensions import Self

from .turn_context import TurnContext
from microsoft_agents.activity import (
    Activity,
    ResourceResponse,
    ConversationReference,
    ConversationParameters,
)


class ChannelAdapterProtocol(Protocol):
    on_turn_error: Callable[[TurnContext, Exception], Awaitable] | None

    @abstractmethod
    async def send_activities(
        self, context: TurnContext, activities: list[Activity]
    ) -> list[ResourceResponse]:
        pass

    @abstractmethod
    async def update_activity(self, context: TurnContext, activity: Activity) -> None:
        pass

    @abstractmethod
    async def delete_activity(
        self, context: TurnContext, reference: ConversationReference
    ) -> None:
        pass

    @abstractmethod
    def use(self, middleware: object) -> Self:
        pass

    @abstractmethod
    async def continue_conversation(
        self,
        agent_id: str,
        reference: ConversationReference,
        callback: Callable[[TurnContext], Awaitable],
    ) -> None:
        pass

    # TODO: potentially move ClaimsIdentity to activity
    @abstractmethod
    async def continue_conversation_with_claims(
        self,
        claims_identity: dict,
        continuation_activity: Activity,
        callback: Callable[[TurnContext], Awaitable],
        audience: str | None = None,
    ):
        pass

    @abstractmethod
    async def create_conversation(
        self,
        agent_app_id: str,
        channel_id: str,
        service_url: str,
        audience: str,
        conversation_parameters: ConversationParameters,
        callback: Callable[[TurnContext], Awaitable],
    ) -> None:
        pass

    @abstractmethod
    async def run_pipeline(
        self,
        context: TurnContext,
        callback: Callable[[TurnContext], Awaitable],
    ) -> None:
        pass
