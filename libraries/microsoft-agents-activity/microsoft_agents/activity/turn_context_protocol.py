# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Protocol, Callable, Generic, TypeVar
from abc import abstractmethod

from microsoft_agents.activity import (
    Activity,
    ResourceResponse,
    ConversationReference,
)

# TODO: refactor circular dependency
# from .channel_adapter_protocol import ChannelAdapterProtocol

T = TypeVar("T", bound=Activity)


class TurnContextProtocol(Protocol, Generic[T]):
    adapter: "ChannelAdapterProtocol"
    activity: Activity | T
    responded: bool
    turn_state: dict

    @abstractmethod
    async def send_activity(
        self,
        activity_or_text: Activity | str,
        speak: str | None = None,
        input_hint: str | None = None,
    ) -> ResourceResponse | None:
        pass

    @abstractmethod
    async def send_activities(
        self, activities: list[Activity]
    ) -> list[ResourceResponse]:
        pass

    @abstractmethod
    async def update_activity(self, activity: Activity) -> ResourceResponse | None:
        pass

    @abstractmethod
    async def delete_activity(
        self, id_or_reference: str | ConversationReference
    ) -> None:
        pass

    @abstractmethod
    def on_send_activities(self, handler: Callable) -> "TurnContextProtocol":
        pass

    @abstractmethod
    def on_update_activity(self, handler: Callable) -> "TurnContextProtocol":
        pass

    @abstractmethod
    def on_delete_activity(self, handler: Callable) -> "TurnContextProtocol":
        pass

    @abstractmethod
    async def send_trace_activity(
        self,
        name: str,
        value: object | None = None,
        value_type: str | None = None,
        label: str | None = None,
    ) -> ResourceResponse:
        pass
