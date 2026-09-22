# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-aware :class:`Activity` subclass exposing Teams channel data helpers."""

from __future__ import annotations

import json

from typing import Iterable
from uuid import uuid4

from a2a.types import (
    Artifact,
    Message,
    Part,
    TaskState,
)

from pydantic import Field

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Attachment,
    Channels,
    ChannelId,
    ChannelAccount,
    ConversationAccount,
    DeliveryModes,
    RoleTypes,
)

from . import utils

_DEFAULT_USER_ID = "unknown"
# _ENTITY_TYPE_TEMPLATE = "application/vnd.microsoft.entity.{0}"

class A2AActivity(Activity):
    """A2A-aware :class:`Activity` subclass exposing A2A protocol data helpers."""

    channel_id: ChannelId = Field(default_factory=lambda: ChannelId(Channels.a2a), frozen=True)

    @staticmethod
    def from_message(request_id: str, task_id: str | None, message: Message) -> A2AActivity:
        """Create an A2AActivity from a Message object.

        :param request_id: The request ID for the activity.
        :param task_id: The task ID for the activity. If None, the task ID from the message will be used.
        :param message: The Message object to convert.
        :return: An A2AActivity object representing the message.
        """

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
        """Convert the activity to a Message object.
        
        :param context_id: The context ID for the message.
        :param task_id: The task ID for the message.
        :param include_entities: Whether to include entities in the message. Defaults to True.
        :return: A Message object representing the activity.
        """
        return utils.create_message(context_id, task_id, self, include_entities)

    def to_artifact(self, artifact_id: str | None = None, include_entities: bool = True) -> Artifact:
        """Convert the activity to an Artifact object.

        :param artifact_id: The ID of the artifact. If None, a new ID will be generated.
        :param include_entities: Whether to include entities in the artifact. Defaults to True.
        :return: An Artifact object representing the activity.
        """
        return utils.activity_to_artifact(self, artifact_id, include_entities)

    def get_task_state(self) -> TaskState:
        """Get the current task state of the activity.

        :return: The TaskState of the activity.
        """
        return utils.get_task_state(self)

    @staticmethod
    def _create_activity(
        conversation_id: str,
        parts: Iterable[Part],
        is_ingress: bool,
        is_streaming: bool
    ) -> A2AActivity:
        """Create an Activity representing an A2A concept.
        
        :param conversation_id: The ID of the conversation.
        :param parts: The parts to include in the activity.
        :param is_ingress: Whether the activity is incoming.
        :param is_streaming: Whether the activity is streaming.
        :return: An A2AActivity object representing the activity.
        """

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
            if part.text:
                if not activity.text:
                    activity.text = part.text
                else:
                    activity.text += part.text
            elif part.url:
                activity.attachments.append(Attachment(
                    content_type=part.media_type,
                    content_url=part.url,
                    name=part.filename,
                ))
            elif part.raw:
                activity.attachments.append(Attachment(
                    content_type=part.media_type,
                    content=part.raw,
                    name=part.filename,
                ))
            elif part.data:
                activity.attachments.append(Attachment(
                    content_type="application/json",
                    content=json.dumps(part.data),
                    name="A2A DataPart",
                ))

        return activity