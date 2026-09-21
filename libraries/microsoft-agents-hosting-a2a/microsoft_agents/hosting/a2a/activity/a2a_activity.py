# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-aware :class:`Activity` subclass exposing Teams channel data helpers."""

from __future__ import annotations

from typing import Literal, Mapping, Iterable
from uuid import uuid4

from a2a.types import (
    Artifact,
    Message,
    Part,
    Task,
    TaskState,
)

from pydantic import Field

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels,
    ChannelId,
    ChannelAccount,
    ConversationAccount,
    DeliveryModes,
    RoleTypes,
    InputHints,
    StreamInfo,
)

from . import utils

_DEFAULT_USER_ID = "unknown"
_ENTITY_TYPE_TEMPLATE = "application/vnd.microsoft.entity.{0}"

class A2AActivity(Activity):
    """A2A-aware :class:`Activity` subclass exposing A2A protocol data helpers."""

    channel_id: ChannelId = Field(default=ChannelId(Channels.a2a), frozen=True)

    @staticmethod
    def from_message(request_id: str, task_id: str | None, message: Message) -> A2AActivity:

        if not task_id and not message.task_id:
            raise ValueError("Task ID is required.")

        task_id = task_id or message.task_id
            
        activity = A2AActivity._create_activity(
            task_id,
            message.parts,
            True,
            True
        )

        activity.request_id = request_id or str(uuid4()) # formatting
        activity.channel_data = message
        message.context_id = message.context_id or str(uuid4()) # Formatting
        message.task_id = task_id

        return activity

    def to_message(self, context_id: str, task_id: str, include_entities: bool = True) -> Message:
        return utils.create_message(context_id, task_id, self, include_entities)

    def to_artifact(self, artifact_id: str | None = None, include_entities: bool = True) -> Artifact:
        return utils.activity_to_artifact(self, artifact_id, include_entities)

    def has_message_content(self) -> bool:
        return utils.has_message_content(self)

    def get_task_state(self) -> TaskState:
        return utils.get_task_state(self)

    @staticmethod
    def _create_activity(
        conversation_id: str,
        parts: Iterable[Part],
        is_ingress: bool,
        is_streaming: bool
    ) -> A2AActivity:
        """Create an Activity representing an A2A concept."""

        agent = ChannelAccount(id="assistant", role=RoleTypes.agent)
        user = ChannelAccount(id=_DEFAULT_USER_ID, role=RoleTypes.user)

        activity = A2AActivity(
            type=ActivityTypes.message,
            id=str(uuid4()),
            delivery_mode=DeliveryModes.stream if is_streaming else DeliveryModes.expect_replies,
            conversation=ConversationAccount(id=conversation_id),
            recipient=agent if is_ingress else user,
            from_property=user if is_ingress else agent,
        )

        for part in parts:
            if part.content_case

        return activity